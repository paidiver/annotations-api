"""Debug view to dump database contents as JSON."""

from urllib.request import Request

from django.conf import settings
from rest_framework.response import Response
from rest_framework.views import APIView

from api.models import (
    PI,
    Annotation,
    AnnotationLabel,
    AnnotationSet,
    Annotator,
    Context,
    Creator,
    Event,
    Image,
    ImageCameraCalibrationModel,
    ImageCameraHousingViewport,
    ImageCameraPose,
    ImageDomeportParameter,
    ImageFlatportParameter,
    ImagePhotometricCalibration,
    ImageSet,
    Label,
    License,
    Platform,
    Project,
    RelatedMaterial,
    Sensor,
)
from api.serializers import (
    AnnotationLabelSerializer,
    AnnotationSerializer,
    AnnotationSetSerializer,
    AnnotatorSerializer,
    ImageCameraCalibrationModelSerializer,
    ImageCameraHousingViewportSerializer,
    ImageCameraPoseSerializer,
    ImageDomeportParameterSerializer,
    ImageFlatportParameterSerializer,
    ImagePhotometricCalibrationSerializer,
    ImageSerializer,
    ImageSetSerializer,
    LabelSerializer,
)
from api.serializers.fields import (
    ContextSerializer,
    CreatorSerializer,
    EventSerializer,
    LicenseSerializer,
    PISerializer,
    PlatformSerializer,
    ProjectSerializer,
    RelatedMaterialSerializer,
    SensorSerializer,
)

tables_to_models_and_serializers = {
    "image_sets": (ImageSet, ImageSetSerializer),
    "images": (Image, ImageSerializer),
    "pi": (PI, PISerializer),
    "context": (Context, ContextSerializer),
    "creator": (Creator, CreatorSerializer),
    "event": (Event, EventSerializer),
    "license": (License, LicenseSerializer),
    "platform": (Platform, PlatformSerializer),
    "project": (Project, ProjectSerializer),
    "related_material": (RelatedMaterial, RelatedMaterialSerializer),
    "sensor": (Sensor, SensorSerializer),
    "image_camera_calibration_model": (ImageCameraCalibrationModel, ImageCameraCalibrationModelSerializer),
    "image_camera_housing_viewport": (ImageCameraHousingViewport, ImageCameraHousingViewportSerializer),
    "image_camera_pose": (ImageCameraPose, ImageCameraPoseSerializer),
    "image_domeport_parameter": (ImageDomeportParameter, ImageDomeportParameterSerializer),
    "image_flatport_parameter": (ImageFlatportParameter, ImageFlatportParameterSerializer),
    "image_photometric_calibration": (ImagePhotometricCalibration, ImagePhotometricCalibrationSerializer),
    "annotation_sets": (AnnotationSet, AnnotationSetSerializer),
    "labels": (Label, LabelSerializer),
    "annotators": (Annotator, AnnotatorSerializer),
    "annotations": (Annotation, AnnotationSerializer),
    "annotation_labels": (AnnotationLabel, AnnotationLabelSerializer),
}


class DebugDatabaseDumpView(APIView):
    """Debug endpoint to dump DB contents as JSON.

    Only enabled when DEBUG=True
    """

    def get(self, request: Request, *args, **kwargs):
        """Handle GET request to dump database contents.

        Args:
            request: The HTTP request object.
            *args: Additional positional arguments (not used here).
            **kwargs: Additional keyword arguments (not used here).

        Returns:
            Response: A DRF Response containing the serialized database contents, or a 404 if not in DEBUG mode.
        """
        if not settings.DEBUG:
            return Response({"detail": "Not found."}, status=404)

        payload = {}

        for table_name, (model, serializer) in tables_to_models_and_serializers.items():
            queryset = model.objects.all()
            serialized_data = serializer(queryset, many=True).data
            payload[table_name] = serialized_data

        return Response(payload)
