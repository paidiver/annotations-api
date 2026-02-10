"""Common fields module for models."""

import random

import factory
import faker
from django.utils import timezone
from factory import Faker
from factory.django import DjangoModelFactory

from api.models.base import (
    AcquisitionEnum,
    CaptureModeEnum,
    DeploymentEnum,
    FaunaAttractionEnum,
    IlluminationEnum,
    MarineZoneEnum,
    NavigationEnum,
    PixelMagnitudeEnum,
    QualityEnum,
    ScaleReferenceEnum,
    SpectralResEnum,
)

from .fields import (
    ContextFactory,
    CreatorFactory,
    EventFactory,
    ImageCameraCalibrationModelFactory,
    ImageCameraHousingViewportFactory,
    ImageDomeportParameterFactory,
    ImageFlatportParameterFactory,
    ImagePhotometricCalibrationFactory,
    LicenseFactory,
    PIFactory,
    PlatformFactory,
    ProjectFactory,
    SensorFactory,
)
from .utils import enum_choice, rand_lat, rand_lon


class CommonFieldsAllFactory(DjangoModelFactory):
    """Common fields used across multiple tables."""

    handle = factory.LazyFunction(lambda: f"https://picsum.photos/800/600?random={random.randint(1, 10000)}")
    copyright = Faker("company")
    abstract = Faker("paragraph", nb_sentences=4)
    objective = Faker("paragraph", nb_sentences=2)
    target_environment = Faker("sentence")
    target_timescale = Faker("sentence")
    curation_protocol = Faker("paragraph", nb_sentences=3)

    class Meta:
        """Meta class for CommonFieldsAll."""

        abstract = True

    @factory.post_generation
    def creators(self, create: bool, extracted, **kwargs) -> None:
        """Populate creators M2M via the through model.

        Usage options:
            ImageSetFactory(creators=[creator1, creator2])
            ImageSetFactory(with_creators=3)

        Args:
            create: Whether the instance was actually created (vs just built).
            extracted: The value passed to creators when the factory is called.
            **kwargs: Additional keyword arguments (not used here).
        """
        if not create:
            return

        if not hasattr(self, "creators"):
            return

        through_model = self.creators.through

        fk_to_self_name = None
        for f in through_model._meta.fields:
            if getattr(f, "remote_field", None) and f.remote_field.model == self.__class__:
                fk_to_self_name = f.name
                break
        if fk_to_self_name is None:
            raise RuntimeError(f"Could not find FK from {through_model.__name__} to {self.__class__.__name__}")

        if extracted:
            creators_list = list(extracted)
        else:
            n = int(getattr(self, "with_creators", 0) or 0)
            if n <= 0:
                return
            creators_list = [CreatorFactory() for _ in range(n)]

        rows = [through_model(**{fk_to_self_name: self, "creator": c}) for c in creators_list]
        through_model.objects.bulk_create(rows, ignore_conflicts=True)


class CommonFieldsImagesImageSetsFactory(DjangoModelFactory):
    """Common fields for image_sets and images."""

    sha256_hash = factory.LazyFunction(lambda: faker.Faker().sha256())
    date_time = factory.LazyFunction(lambda: timezone.now() - timezone.timedelta(days=random.randint(0, 3650)))

    latitude = factory.LazyFunction(rand_lat)
    longitude = factory.LazyFunction(rand_lon)
    altitude_meters = factory.LazyFunction(lambda: random.uniform(-6000.0, 2000.0))
    coordinate_uncertainty_meters = factory.LazyFunction(lambda: random.uniform(0.0, 50.0))

    entropy = factory.LazyFunction(lambda: random.uniform(0.0, 8.0))
    particle_count = factory.LazyFunction(lambda: random.randint(0, 10000))

    average_color = factory.LazyFunction(lambda: [random.uniform(0, 255) for _ in range(3)])

    mpeg7_color_layout = None
    mpeg7_color_statistic = None
    mpeg7_color_structure = None
    mpeg7_dominant_color = None
    mpeg7_edge_histogram = None
    mpeg7_homogeneous_texture = None
    mpeg7_scalable_color = None

    acquisition = factory.LazyFunction(lambda: enum_choice(AcquisitionEnum))
    quality = factory.LazyFunction(lambda: enum_choice(QualityEnum))
    deployment = factory.LazyFunction(lambda: enum_choice(DeploymentEnum))
    navigation = factory.LazyFunction(lambda: enum_choice(NavigationEnum))
    scale_reference = factory.LazyFunction(lambda: enum_choice(ScaleReferenceEnum))
    illumination = factory.LazyFunction(lambda: enum_choice(IlluminationEnum))
    pixel_magnitude = factory.LazyFunction(lambda: enum_choice(PixelMagnitudeEnum))
    marine_zone = factory.LazyFunction(lambda: enum_choice(MarineZoneEnum))
    spectral_resolution = factory.LazyFunction(lambda: enum_choice(SpectralResEnum))
    capture_mode = factory.LazyFunction(lambda: enum_choice(CaptureModeEnum))
    fauna_attraction = factory.LazyFunction(lambda: enum_choice(FaunaAttractionEnum))
    area_square_meters = factory.LazyFunction(lambda: random.uniform(0.1, 1e6))
    meters_above_ground = factory.LazyFunction(lambda: random.uniform(0.0, 200.0))
    acquisition_settings = factory.LazyFunction(
        lambda: {"exposure": random.randint(1, 2000), "iso": random.choice([100, 200, 400, 800])}
    )

    camera_yaw_degrees = factory.LazyFunction(lambda: random.uniform(-180.0, 180.0))
    camera_pitch_degrees = factory.LazyFunction(lambda: random.uniform(-90.0, 90.0))
    camera_roll_degrees = factory.LazyFunction(lambda: random.uniform(-180.0, 180.0))
    overlap_fraction = factory.LazyFunction(lambda: random.uniform(0.0, 1.0))

    spatial_constraints = Faker("sentence")
    temporal_constraints = Faker("sentence")
    time_synchronisation = Faker("sentence")
    item_identification_scheme = Faker("sentence")
    visual_constraints = Faker("sentence")

    context = None
    project = None
    event = None
    platform = None
    sensor = None
    pi = None
    license = None
    creators = None

    camera_pose = None
    camera_housing_viewport = None
    flatport_parameter = None
    domeport_parameter = None
    photometric_calibration = None
    camera_calibration_model = None

    @factory.post_generation
    def with_relations(self, create: bool, extracted, **kwargs) -> None:
        """Populate all related fields if with_relations is True.

        Usage:
          ImageSetFactory(with_relations=True)  # creates and sets all related fields
          ImageSetFactory(with_relations=False) # leaves all related fields null

        Args:
            create: Whether the instance was actually created (vs just built).
            extracted: The value passed to with_relations when the factory is called.
            **kwargs: Additional keyword arguments (not used here).
        """
        if not create:
            return

        enabled = bool(extracted) if extracted is not None else False
        if not enabled:
            return

        self.context = ContextFactory()
        self.project = ProjectFactory()
        self.event = EventFactory()
        self.platform = PlatformFactory()
        self.sensor = SensorFactory()
        self.pi = PIFactory()
        self.license = LicenseFactory()
        self.save(update_fields=["context", "project", "event", "platform", "sensor", "pi", "license"])

    @factory.post_generation
    def with_camera_models(self, create: bool, extracted, **kwargs) -> None:
        """Populate camera models if with_camera_models is True.

        Usage:
          ImageSetFactory(with_camera_models=True)  # creates and sets camera models
          ImageSetFactory(with_camera_models=False) # leaves camera models null

        Args:
            create: Whether the instance was actually created (vs just built).
            extracted: The value passed to with_camera_models when the factory is called.
            **kwargs: Additional keyword arguments (not used here).
        """
        if not create:
            return

        enabled = bool(extracted) if extracted is not None else False
        if not enabled:
            return

        self.camera_housing_viewport = ImageCameraHousingViewportFactory()
        self.flatport_parameter = ImageFlatportParameterFactory()
        self.domeport_parameter = ImageDomeportParameterFactory()
        self.photometric_calibration = ImagePhotometricCalibrationFactory()
        self.camera_calibration_model = ImageCameraCalibrationModelFactory()
        self.save(
            update_fields=[
                "camera_housing_viewport",
                "flatport_parameter",
                "domeport_parameter",
                "photometric_calibration",
                "camera_calibration_model",
            ]
        )
