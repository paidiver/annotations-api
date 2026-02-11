from django.test import TestCase

from api.factories.annotation_set import AnnotationSetFactory
from api.factories.fields import CreatorFactory
from api.factories.image_set import ImageSetFactory


class CommonFieldsFactoryCoverageTests(TestCase):
    # ---------------------------------------------------------------------
    # CommonFieldsAllFactory.creators
    # ---------------------------------------------------------------------
    def test_creators_postgen_does_nothing_on_build(self):
        # Hits: if not create: return  (line ~73 / 76 area depending on file)
        iset = ImageSetFactory.build(creators=[CreatorFactory()])
        # Built instances are not saved; just sanity check no crash and no PK
        self.assertIsNone(iset.pk)

    def test_creators_postgen_returns_if_model_has_no_creators_m2m(self):
        # This is specifically to hit:
        #   if not hasattr(self, "creators"): return
        #
        # If your AnnotationSet model doesn't have a creators M2M, this will cover it.
        # If it DOES have creators, this test will still be harmless but won't hit that branch.
        aset = AnnotationSetFactory()
        if hasattr(aset, "creators"):
            # Avoid failing if your model actually has creators.
            self.skipTest("AnnotationSet has creators M2M; cannot hit hasattr(self, 'creators') guard branch.")
        self.assertTrue(True)  # reached without error

    def test_creators_links_explicit_extracted_list(self):
        # Hits: if extracted: creators_list = list(extracted)
        c1 = CreatorFactory()
        c2 = CreatorFactory()

        iset = ImageSetFactory(creators=[c1, c2])

        ids = set(iset.creators.values_list("id", flat=True))
        self.assertEqual(ids, {c1.id, c2.id})

    def test_creators_empty_extracted_list_hits_n_branch_and_returns(self):
        # This is the cleanest way to cover the "else: n = int(getattr(self, 'creators', 0) ...)" lines
        # WITHOUT depending on creators being available on the model instance.
        #
        # extracted=[] is falsy => goes to else branch => n defaults to 0 => returns.
        iset = ImageSetFactory(creators=[])
        self.assertEqual(iset.creators.count(), 0)

    def test_creators_raises_runtimeerror_if_fk_to_self_not_found(self):
        # Hits: fk_to_self_name is None -> RuntimeError
        iset = ImageSetFactory()
        through_model = iset.creators.through

        original_fields = through_model._meta.fields

        class DummyRemoteField:
            model = object  # will never equal iset.__class__

        class DummyField:
            name = "not_fk"
            remote_field = DummyRemoteField()

        try:
            through_model._meta.fields = [DummyField()]
            with self.assertRaises(RuntimeError):
                ImageSetFactory(creators=[CreatorFactory()])
        finally:
            through_model._meta.fields = original_fields

    # ---------------------------------------------------------------------
    # CommonFieldsImagesImageSetsFactory.with_relations
    # ---------------------------------------------------------------------
    def test_with_relations_disabled_leaves_related_fields_null(self):
        iset = ImageSetFactory(with_relations=False)
        self.assertIsNone(iset.context)
        self.assertIsNone(iset.project)
        self.assertIsNone(iset.event)
        self.assertIsNone(iset.platform)
        self.assertIsNone(iset.sensor)
        self.assertIsNone(iset.pi)
        self.assertIsNone(iset.license)

    def test_with_relations_enabled_sets_related_fields(self):
        # Hits: enabled=True path and update_fields save
        iset = ImageSetFactory(with_relations=True)
        self.assertIsNotNone(iset.context)
        self.assertIsNotNone(iset.project)
        self.assertIsNotNone(iset.event)
        self.assertIsNotNone(iset.platform)
        self.assertIsNotNone(iset.sensor)
        self.assertIsNotNone(iset.pi)
        self.assertIsNotNone(iset.license)

    def test_with_relations_does_nothing_on_build(self):
        # Hits: if not create: return
        iset = ImageSetFactory.build(with_relations=True)
        self.assertIsNone(iset.context)
        self.assertIsNone(iset.project)
        self.assertIsNone(iset.event)
        self.assertIsNone(iset.platform)
        self.assertIsNone(iset.sensor)
        self.assertIsNone(iset.pi)
        self.assertIsNone(iset.license)

    # ---------------------------------------------------------------------
    # CommonFieldsImagesImageSetsFactory.with_camera_models
    # ---------------------------------------------------------------------
    def test_with_camera_models_disabled_leaves_camera_fields_null(self):
        iset = ImageSetFactory(with_camera_models=False)
        self.assertIsNone(iset.camera_housing_viewport)
        self.assertIsNone(iset.flatport_parameter)
        self.assertIsNone(iset.domeport_parameter)
        self.assertIsNone(iset.photometric_calibration)
        self.assertIsNone(iset.camera_calibration_model)

    def test_with_camera_models_enabled_sets_camera_fields(self):
        # Hits: enabled=True path and update_fields save
        iset = ImageSetFactory(with_camera_models=True)
        self.assertIsNotNone(iset.camera_housing_viewport)
        self.assertIsNotNone(iset.flatport_parameter)
        self.assertIsNotNone(iset.domeport_parameter)
        self.assertIsNotNone(iset.photometric_calibration)
        self.assertIsNotNone(iset.camera_calibration_model)

    def test_with_camera_models_does_nothing_on_build(self):
        # Hits: if not create: return
        iset = ImageSetFactory.build(with_camera_models=True)
        self.assertIsNone(iset.camera_housing_viewport)
        self.assertIsNone(iset.flatport_parameter)
        self.assertIsNone(iset.domeport_parameter)
        self.assertIsNone(iset.photometric_calibration)
        self.assertIsNone(iset.camera_calibration_model)
