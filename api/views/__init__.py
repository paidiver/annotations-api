"""__init__.py for the api.views package."""

from .annotation import AnnotationViewSet, AnnotatorViewSet, UploadAnnotationsView
from .annotation_set import AnnotationSetModelViewSet, AnnotationSetViewSet
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
from .label_set import LabelSetViewSet

__all__ = [
    "HealthView",
    "ImageSetViewSet",
    "ImageViewSet",
    "AnnotationViewSet",
    "AnnotatorViewSet",
    "AnnotationSetViewSet",
    "AnnotationSetModelViewSet",
    "LabelViewSet",
    "LabelSetViewSet",
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
