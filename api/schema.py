"""This module defines custom schema extensions for drf-spectacular to improve the API docs for serializer fields."""

from drf_spectacular.extensions import OpenApiSerializerFieldExtension
from drf_spectacular.plumbing import build_basic_type


class CreateOnlyRelatedFieldExtension(OpenApiSerializerFieldExtension):
    """Extension to map CreateOnlyRelatedField to the schema of the serializer used for creation."""

    target_class = "api.serializers.base.CreateOnlyRelatedField"

    def map_serializer_field(self, auto_schema, direction):
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

        return build_basic_type("object")
