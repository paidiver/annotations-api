"""Routes for the API viewsets."""

from rest_framework.routers import DefaultRouter

from api.views.image_views import (
    ImageCameraCalibrationModelViewSet,
    ImageCameraHousingViewportViewSet,
    ImageCameraPoseViewSet,
    ImageDomeportParameterViewSet,
    ImageFlatportParameterViewSet,
    ImagePhotometricCalibrationViewSet,
)

from .annotation_views import AnnotatorViewSet
from .views import (
    ContextViewSet,
    CreatorViewSet,
    EventViewSet,
    LicenseViewSet,
    PIViewSet,
    PlatformViewSet,
    ProjectViewSet,
    RelatedMaterialViewSet,
    SensorViewSet,
)

router = DefaultRouter()
#annotation related routes
router.register("annotators", AnnotatorViewSet, basename="annotator")

#field related routes
router.register("creators", CreatorViewSet, basename="creator")
router.register("contexts", ContextViewSet, basename="context")
router.register("pis", PIViewSet, basename="pi")
router.register("events", EventViewSet, basename="event")
router.register("licenses", LicenseViewSet, basename="license")
router.register("platforms", PlatformViewSet, basename="platform")
router.register("projects", ProjectViewSet, basename="project")
router.register("related-materials", RelatedMaterialViewSet, basename="relatedmaterial")
router.register("sensors", SensorViewSet, basename="sensor")

#image related routes
router.register("image-camera-calibration-models", ImageCameraCalibrationModelViewSet, basename="imagecameracalibrationmodel")  # noqa: E501
router.register("image-camera-housing-viewports", ImageCameraHousingViewportViewSet, basename="imagecamerahousingviewport")  # noqa: E501
router.register("image-camera-poses", ImageCameraPoseViewSet, basename="imagecamerapose")
router.register("image-domeport-parameters", ImageDomeportParameterViewSet, basename="imagedomeportparameter")
router.register("image-flatport-parameters", ImageFlatportParameterViewSet, basename="imageflatportparameter")
router.register("image-photometric-calibrations", ImagePhotometricCalibrationViewSet, basename="imagephotometriccalibration")  # noqa: E501
