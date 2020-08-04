from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.filters import OrderingFilter, SearchFilter

from sharepoint_rest_api.filters import SharePointLibraryFilter
from sharepoint_rest_api.models import SharePointLibrary, SharePointSite, SharePointTenant
from sharepoint_rest_api.serializers.model_serializers import (
    SharePointLibrarySerializer,
    SharePointSiteSerializer,
    SharePointTenantSerializer,
)


class SharePointTenantViewSet(viewsets.ReadOnlyModelViewSet):
    filter_backends = (SearchFilter, DjangoFilterBackend, OrderingFilter)
    queryset = SharePointTenant.objects.all()
    serializer_class = SharePointTenantSerializer
    search_fields = ('url', )


class SharePointSiteViewSet(viewsets.ReadOnlyModelViewSet):
    filter_backends = (SearchFilter, DjangoFilterBackend, OrderingFilter)
    queryset = SharePointSite.objects.all()
    serializer_class = SharePointSiteSerializer
    search_fields = ('name', )


class SharePointLibraryViewSet(viewsets.ReadOnlyModelViewSet):
    filter_backends = (SearchFilter, DjangoFilterBackend, OrderingFilter)
    queryset = SharePointLibrary.objects.all()
    serializer_class = SharePointLibrarySerializer
    search_fields = ('name', )
    filterset_class = SharePointLibraryFilter
