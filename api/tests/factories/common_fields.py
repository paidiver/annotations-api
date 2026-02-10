"""Common fields module for models."""

import random

import factory
from django.utils import timezone
from factory import Faker
from factory.django import DjangoModelFactory

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
from .utils import rand_lat, rand_lon


class CommonFieldsAllFactory(DjangoModelFactory):
    """Common fields used across multiple tables."""

    name = factory.Sequence(lambda n: f"ImageSet {n:05d}")
    handle = Faker("url")
    copyright = Faker("company")
    abstract = Faker("paragraph", nb_sentences=4)
    objective = Faker("paragraph", nb_sentences=2)
    target_environment = Faker("sentence")
    target_timescale = Faker("sentence")
    curation_protocol = Faker("paragraph", nb_sentences=3)

    class Meta:
        """Meta class for CommonFieldsAll."""

        abstract = True


class CommonFieldsImagesImageSetsFactory(DjangoModelFactory):
    """Common fields for image_sets and images."""

    sha256_hash = factory.LazyFunction(lambda: Faker("sha256").generate({}))
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

    @factory.lazy_attribute
    def acquisition(self) -> str | None:
        """Returns a random acquisition choice or None if no choices defined."""
        choices = [c[0] for c in self._meta.model._meta.get_field("acquisition").choices]
        return random.choice(choices) if choices else None

    @factory.lazy_attribute
    def quality(self) -> str | None:
        """Returns a random quality choice or None if no choices defined."""
        choices = [c[0] for c in self._meta.model._meta.get_field("quality").choices]
        return random.choice(choices) if choices else None

    @factory.lazy_attribute
    def deployment(self) -> str | None:
        """Returns a random deployment choice or None if no choices defined."""
        choices = [c[0] for c in self._meta.model._meta.get_field("deployment").choices]
        return random.choice(choices) if choices else None

    @factory.lazy_attribute
    def navigation(self) -> str | None:
        """Returns a random navigation choice or None if no choices defined."""
        choices = [c[0] for c in self._meta.model._meta.get_field("navigation").choices]
        return random.choice(choices) if choices else None

    @factory.lazy_attribute
    def scale_reference(self) -> str | None:
        """Returns a random scale_reference choice or None if no choices defined."""
        choices = [c[0] for c in self._meta.model._meta.get_field("scale_reference").choices]
        return random.choice(choices) if choices else None

    @factory.lazy_attribute
    def illumination(self) -> str | None:
        """Returns a random illumination choice or None if no choices defined."""
        choices = [c[0] for c in self._meta.model._meta.get_field("illumination").choices]
        return random.choice(choices) if choices else None

    @factory.lazy_attribute
    def pixel_magnitude(self) -> str | None:
        """Returns a random pixel_magnitude choice or None if no choices defined."""
        choices = [c[0] for c in self._meta.model._meta.get_field("pixel_magnitude").choices]
        return random.choice(choices) if choices else None

    @factory.lazy_attribute
    def marine_zone(self) -> str | None:
        """Returns a random marine_zone choice or None if no choices defined."""
        choices = [c[0] for c in self._meta.model._meta.get_field("marine_zone").choices]
        return random.choice(choices) if choices else None

    @factory.lazy_attribute
    def spectral_resolution(self) -> str | None:
        """Returns a random spectral_resolution choice or None if no choices defined."""
        choices = [c[0] for c in self._meta.model._meta.get_field("spectral_resolution").choices]
        return random.choice(choices) if choices else None

    @factory.lazy_attribute
    def capture_mode(self) -> str | None:
        """Returns a random capture_mode choice or None if no choices defined."""
        choices = [c[0] for c in self._meta.model._meta.get_field("capture_mode").choices]
        return random.choice(choices) if choices else None

    @factory.lazy_attribute
    def fauna_attraction(self) -> str | None:
        """Returns a random fauna_attraction choice or None if no choices defined."""
        choices = [c[0] for c in self._meta.model._meta.get_field("fauna_attraction").choices]
        return random.choice(choices) if choices else None

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
    def with_relations(self, create: bool, extracted: any, **kwargs: any) -> None:
        """Generate context/etc related models and assign to FKs if extracted is True (or not provided).

        Usage:
          ImageSetFactory(with_relations=True)
          ImageSetFactory(with_relations=False)  # default behavior

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
        self.creators = [CreatorFactory() for _ in range(random.randint(1, 3))]
        self.save(update_fields=["context", "project", "event", "platform", "sensor", "pi", "license"])

    @factory.post_generation
    def with_camera_models(self, create: bool, extracted: any, **kwargs: any) -> None:
        """Generate camera/sensor related models and assign to FKs if extracted is True (or not provided).

        Usage:
          ImageSetFactory(with_camera_models=True)

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
