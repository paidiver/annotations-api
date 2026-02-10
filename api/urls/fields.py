"""Routes for the API viewsets."""

from rest_framework.routers import DefaultRouter

from api.views.fields import (
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

router_fields = DefaultRouter()

# field related routes
router_fields.register("creator", CreatorViewSet, basename="creator")
router_fields.register("context", ContextViewSet, basename="context")
router_fields.register("pi", PIViewSet, basename="pi")
router_fields.register("event", EventViewSet, basename="event")
router_fields.register("license", LicenseViewSet, basename="license")
router_fields.register("platform", PlatformViewSet, basename="platform")
router_fields.register("project", ProjectViewSet, basename="project")
router_fields.register("relatedmaterial", RelatedMaterialViewSet, basename="relatedmaterial")
router_fields.register("sensor", SensorViewSet, basename="sensor")

# image related routes
router_fields.register("image_camera_pose", ImageCameraPoseViewSet, basename="image-camera-pose")
router_fields.register("image_domeport_parameter", ImageDomeportParameterViewSet, basename="image-domeport-parameter")
router_fields.register("image_flatport_parameter", ImageFlatportParameterViewSet, basename="image-flatport-parameter")
router_fields.register(
    "image_camera_calibration_model", ImageCameraCalibrationModelViewSet, basename="image-camera-calibration-model"
)
router_fields.register(
    "image_camera_housing_viewport", ImageCameraHousingViewportViewSet, basename="image-camera-housing-viewport"
)
router_fields.register(
    "image_photometric_calibration", ImagePhotometricCalibrationViewSet, basename="image-photometric-calibration"
)
