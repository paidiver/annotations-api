"""Serializers for endpoints."""

from rest_framework import serializers

from ..models.annotation import Annotator
from ..models.fields import PI, Context, Creator, Event, License, Platform, Project, Sensor


class CreatorSerializer(serializers.ModelSerializer):
    """Serializer for Creator model."""
    class Meta:
        """Meta class for CreatorSerializer."""
        model = Creator
        fields = ["id", "name", "uri", "created_at", "updated_at"]


class ContextSerializer(serializers.ModelSerializer):
    """Serializer for Context model."""
    class Meta:
        """Meta class for ContextSerializer."""
        model = Context
        fields = "__all__"

class PISerializer(serializers.ModelSerializer):
    """Serializer for PI model."""
    class Meta:
        """Meta class for PISerializer."""
        model = PI
        fields = ["id", "name", "uri", "created_at", "updated_at"]


class EventSerializer(serializers.ModelSerializer):
    """Serializer for Event model."""
    class Meta:
        """Meta class for EventSerializer."""
        model = Event
        fields = ["id", "name", "uri", "created_at", "updated_at"]


class LicenseSerializer(serializers.ModelSerializer):
    """Serializer for License model."""
    class Meta:
        """Meta class for LicenseSerializer."""
        model = License
        fields = ["id", "name", "uri", "created_at", "updated_at"]


class PlatformSerializer(serializers.ModelSerializer):
    """Serializer for Platform model."""
    class Meta:
        """Meta class for PlatformSerializer."""
        model = Platform
        fields = ["id", "name", "uri", "created_at", "updated_at"]


class ProjectSerializer(serializers.ModelSerializer):
    """Serializer for Project model."""
    class Meta:
        """Meta class for ProjectSerializer."""
        model = Project
        fields = ["id", "name", "uri", "created_at", "updated_at"]


class SensorSerializer(serializers.ModelSerializer):
    """Serializer for Sensor model."""
    class Meta:
        """Meta class for SensorSerializer."""
        model = Sensor
        fields = ["id", "name", "uri", "created_at", "updated_at"]


class AnnotatorSerializer(serializers.ModelSerializer):
    """Serializer for Annotator model."""
    class Meta:
        """Meta class for AnnotatorSerializer."""
        model = Annotator
        fields = ["id", "name", "created_at", "updated_at"]
