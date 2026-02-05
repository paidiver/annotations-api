"""Viewsets classes for the API."""

from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_204_NO_CONTENT, HTTP_400_BAD_REQUEST

from ..models.fields import Creator
from ..serializers.serializers import CreatorSerializer


class CreatorViewSet(viewsets.ViewSet):
    """ViewSet for the Creator model."""

    def get_queryset(self):
        """Get the queryset for the Creator model."""
        queryset = Creator.objects.all()
        return queryset

    def create(self, request) -> Response:
        """Create new creator object."""
        data = CreatorSerializer(data=request.data)
        if data.is_valid():
            creator = data.save()
            return Response(CreatorSerializer(creator).data, status=HTTP_201_CREATED)
        return Response(data.errors, status=HTTP_400_BAD_REQUEST)

    def list(self, request) -> Response:
        """List all creators."""
        serializer_class = CreatorSerializer(self.get_queryset(), many=True)
        return Response(serializer_class.data, status=HTTP_200_OK)

    def retrieve(self, request, pk: int=None) -> Response:
        """Get a specific creator by ID."""
        creator = get_object_or_404(self.get_queryset(), pk=pk)
        serializer = CreatorSerializer(creator)
        return Response(serializer.data, status=HTTP_200_OK)

    def update(self, request, pk: int=None) -> Response:
        """Update specific creator by id."""
        creator = get_object_or_404(self.get_queryset(), pk=pk)
        serializer = CreatorSerializer(creator, data=request.data)
        if serializer.is_valid():
            updated_creator = serializer.save()
            return Response(CreatorSerializer(updated_creator).data, status=HTTP_200_OK)
        return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk: int=None) -> Response:
        """Delete creator by id."""
        creator = get_object_or_404(self.get_queryset(), pk=pk)
        creator.delete()
        return Response(status=HTTP_204_NO_CONTENT)
