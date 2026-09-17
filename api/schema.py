"""Custom schema extensions for drf-spectacular to document custom serializer fields."""

from typing import Any

from drf_spectacular.extensions import OpenApiSerializerFieldExtension
from drf_spectacular.openapi import AutoSchema

FALLBACK_OBJECT_SCHEMA = {"type": "object", "additionalProperties": True}


class CreateOnlyRelatedFieldExtension(OpenApiSerializerFieldExtension):
    """Map CreateOnlyRelatedField -> schema of the create serializer."""

    target_class = "api.serializers.base.CreateOnlyRelatedField"

    def map_serializer_field(self, auto_schema: AutoSchema, direction: str) -> dict[str, Any]:
        """This extension maps CreateOnlyRelatedField to the schema of the serializer used for creation.

        This allows the API documentation to show the expected fields for creating related objects, rather than just
        showing a reference to the related object's ID.

        Args:
            auto_schema: The AutoSchema instance that is generating the schema.
            direction: The direction of the schema generation (request or response).

        Returns:
            The OpenAPI schema for the related object's creation serializer, or a basic object schema if the serializer
        cannot be determined.
        """
        field = self.target
        ser_class = getattr(field, "create_serializer_class", None)

        if ser_class is not None:
            serializer = ser_class(context=getattr(field, "context", {}))
            return auto_schema.resolve_serializer(serializer, direction).ref

        return FALLBACK_OBJECT_SCHEMA


class CreateOnlyRelatedListFieldExtension(OpenApiSerializerFieldExtension):
    """Map CreateOnlyRelatedListField -> array of the create serializer schema."""

    target_class = "api.serializers.base.CreateOnlyRelatedListField"

    def map_serializer_field(self, auto_schema: AutoSchema, direction: str) -> dict[str, Any]:
        """This extension maps CreateOnlyRelatedListField to the schema of the serializer used for creation.

        This allows the API documentation to show the expected fields for creating related objects, rather than just
        showing a reference to the related object's ID.

        Args:
            auto_schema: The AutoSchema instance that is generating the schema.
            direction: The direction of the schema generation (request or response).

        Returns:
            The OpenAPI schema for the related object's creation serializer, or a basic object schema if the serializer
        cannot be determined.
        """
        field = self.target
        ser_class = getattr(field, "create_serializer_class", None)

        if ser_class is not None:
            serializer = ser_class(context=getattr(field, "context", {}))
            items_schema = auto_schema.resolve_serializer(serializer, direction).ref
        else:
            items_schema = FALLBACK_OBJECT_SCHEMA

        return {"type": "array", "items": items_schema}


class ResponseSchema(AutoSchema):
    """Document the error envelope used by the API middleware."""

    def _get_response_bodies(self, direction: str = "response") -> dict:
        responses = super()._get_response_bodies(direction)
        problem = {
            "type": "object",
            "required": ["type", "title", "status", "detail", "code"],
            "properties": {
                "type": {"type": "string"},
                "title": {"type": "string"},
                "status": {"type": "integer"},
                "detail": {"type": "string"},
                "code": {"type": "string"},
                "errors": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {"field": {"type": "string"}, "message": {"type": "string"}},
                    },
                },
            },
        }
        for code in (400, 401, 403, 404, 405, 415, 429, 500, 502, 504):
            responses[str(code)] = {
                "description": "Request failed. See code and optional field errors.",
                "content": {"application/problem+json": {"schema": problem}},
            }
        return responses
