"""__init__.py for the api.views package."""

from .annotation import AnnotationLabelViewSet, AnnotationViewSet, AnnotatorViewSet, UploadAnnotationsView
from .annotation_set import AnnotationSetViewSet
from .base import HealthView
from .fields import (
    ContextViewSet,
    CreatorViewSet,
    EventViewSet,
    ImageCameraCalibrationModelViewSet,
    ImageCameraHousingViewportViewSet,
    ImageCameraPoseViewSet,
    ImageDomeportParameterViewSet,
    ImageFlatportParameterViewSet,
    ImagePhotometricCalibrationViewSet,
    LicenseViewSet,
    PIViewSet,
    PlatformViewSet,
    ProjectViewSet,
    RelatedMaterialViewSet,
    SensorViewSet,
)
from .image import ImageViewSet
from .image_set import ImageSetViewSet
from .label import LabelViewSet

__all__ = [
    "HealthView",
    "ImageSetViewSet",
    "ImageViewSet",
    "AnnotationViewSet",
    "AnnotatorViewSet",
    "AnnotationSetViewSet",
    "AnnotationLabelViewSet",
    "LabelViewSet",
    "ContextViewSet",
    "CreatorViewSet",
    "EventViewSet",
    "ImageCameraCalibrationModelViewSet",
    "ImageCameraHousingViewportViewSet",
    "ImageCameraPoseViewSet",
    "ImageDomeportParameterViewSet",
    "ImageFlatportParameterViewSet",
    "ImagePhotometricCalibrationViewSet",
    "LicenseViewSet",
    "PIViewSet",
    "PlatformViewSet",
    "ProjectViewSet",
    "RelatedMaterialViewSet",
    "SensorViewSet",
    "UploadAnnotationsView",
]
