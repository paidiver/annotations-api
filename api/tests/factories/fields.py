"""Factories for models in api.models.fields."""

import random
import uuid

import factory
from factory.django import DjangoModelFactory

from api.models import (
    PI,
    Context,
    Creator,
    Event,
    ImageCameraCalibrationModel,
    ImageCameraHousingViewport,
    ImageDomeportParameter,
    ImageFlatportParameter,
    ImagePhotometricCalibration,
    License,
    Platform,
    Project,
    Sensor,
)
from api.models.fields import RelatedMaterial

from .utils import vec3


class NamedURIFactory(DjangoModelFactory):
    """General factory for models with common fields."""

    name = factory.LazyFunction(lambda: f"Name {uuid.uuid4().hex[:12]}")
    uri = factory.Faker("url")


class CreatorFactory(NamedURIFactory):
    """Factory for Creator model."""

    class Meta:
        """Factory meta class."""

        model = Creator


class ContextFactory(NamedURIFactory):
    """Factory for Context model."""

    class Meta:
        """Factory meta class."""

        model = Context


class ProjectFactory(NamedURIFactory):
    """Factory for Project model."""

    class Meta:
        """Meta class for Project."""

        model = Project


class PIFactory(NamedURIFactory):
    """Factory for PI model."""

    class Meta:
        """Meta class for PI."""

        model = PI


class LicenseFactory(NamedURIFactory):
    """Factory for License model."""

    class Meta:
        """Meta class for License."""

        model = License


class EventFactory(NamedURIFactory):
    """Factory for Event model."""

    class Meta:
        """Meta class for Event."""

        model = Event


class PlatformFactory(NamedURIFactory):
    """Factory for Platform model."""

    class Meta:
        """Meta class for Platform."""

        model = Platform


class SensorFactory(NamedURIFactory):
    """Factory for Sensor model."""

    class Meta:
        """Meta class for Sensor."""

        model = Sensor


class RelatedMaterialFactory(DjangoModelFactory):
    """Factory for RelatedMaterial model."""

    uri = factory.Faker("url")
    title = factory.Faker("sentence")
    relation = factory.Faker("sentence")

    class Meta:
        """Meta class for RelatedMaterial."""

        model = RelatedMaterial


class ImageCameraHousingViewportFactory(DjangoModelFactory):
    """Factory for ImageCameraHousingViewport model."""

    class Meta:
        """Meta class for ImageCameraHousingViewport."""

        model = ImageCameraHousingViewport

    viewport_type = factory.LazyFunction(lambda: random.choice(["flat port", "dome port", "other", None]))
    optical_density = factory.LazyFunction(lambda: random.choice([None, random.uniform(0.8, 1.2)]))
    thickness_millimeters = factory.LazyFunction(lambda: random.choice([None, random.uniform(2.0, 30.0)]))
    extra_description = factory.Faker("sentence")


class ImageFlatportParameterFactory(DjangoModelFactory):
    """Factory for ImageFlatportParameter model."""

    class Meta:
        """Meta class for ImageFlatportParameter."""

        model = ImageFlatportParameter

    lens_port_distance_millimeters = factory.LazyFunction(lambda: random.choice([None, random.uniform(0.0, 80.0)]))

    interface_normal_direction = factory.LazyFunction(
        lambda: random.choice(
            [
                None,
                [
                    random.uniform(-0.1, 0.1),
                    random.uniform(-0.1, 0.1),
                    random.uniform(0.8, 1.0),
                ],
            ]
        )
    )

    extra_description = factory.Faker("sentence")


class ImageDomeportParameterFactory(DjangoModelFactory):
    """Factory for ImageDomeportParameter model."""

    class Meta:
        """Meta class for ImageDomeportParameter."""

        model = ImageDomeportParameter

    outer_radius_millimeters = factory.LazyFunction(lambda: random.choice([None, random.uniform(10.0, 250.0)]))

    decentering_offset_xyz_millimeters = factory.LazyFunction(
        lambda: random.choice([None, vec3(min_v=-10.0, max_v=10.0)])
    )

    extra_description = factory.Faker("sentence")


class ImageCameraCalibrationModelFactory(DjangoModelFactory):
    """Factory for ImageCameraCalibrationModel model."""

    class Meta:
        """Meta class for ImageCameraCalibrationModel."""

        model = ImageCameraCalibrationModel

    calibration_model_type = factory.LazyFunction(
        lambda: random.choice(
            [
                "rectilinear air",
                "rectilinear water",
                "fisheye air",
                "fisheye water",
                "other",
                None,
            ]
        )
    )

    focal_length_xy_pixel = factory.LazyFunction(
        lambda: random.choice([None, [random.uniform(300.0, 4000.0), random.uniform(300.0, 4000.0)]])
    )

    principal_point_xy_pixel = factory.LazyFunction(
        lambda: random.choice([None, [random.uniform(0.0, 4000.0), random.uniform(0.0, 3000.0)]])
    )

    distortion_coefficients = factory.LazyFunction(
        lambda: random.choice(
            [
                None,
                [random.uniform(-0.5, 0.5) for _ in range(4)],
                [random.uniform(-0.5, 0.5) for _ in range(8)],
            ]
        )
    )

    approximate_field_of_view_water_xy_degree = factory.LazyFunction(
        lambda: random.choice([None, [random.uniform(10.0, 180.0), random.uniform(10.0, 180.0)]])
    )

    extra_description = factory.Faker("sentence")


class ImagePhotometricCalibrationFactory(DjangoModelFactory):
    """Factory for ImagePhotometricCalibration model."""

    class Meta:
        """Meta class for ImagePhotometricCalibration."""

        model = ImagePhotometricCalibration

    sequence_white_balancing = factory.Faker("sentence")

    exposure_factor_rgb = factory.LazyFunction(
        lambda: random.choice([None, [random.uniform(0.1, 10.0), random.uniform(0.1, 10.0), random.uniform(0.1, 10.0)]])
    )

    sequence_illumination_type = factory.LazyFunction(
        lambda: random.choice(
            [
                "constant artificial",
                "globally adapted artificial",
                "individually varying light sources",
                "sunlight",
                "mixed",
                None,
            ]
        )
    )

    sequence_illumination_description = factory.Faker("sentence")

    illumination_factor_rgb = factory.LazyFunction(
        lambda: random.choice([None, [random.uniform(0.1, 10.0), random.uniform(0.1, 10.0), random.uniform(0.1, 10.0)]])
    )

    water_properties_description = factory.Faker("sentence")
