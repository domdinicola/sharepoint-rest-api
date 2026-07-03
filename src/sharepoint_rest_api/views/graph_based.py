from django.http import HttpResponseBadRequest
from django.utils.functional import cached_property
from office365.runtime.client_request_exception import ClientRequestException
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from sharepoint_rest_api import config
from sharepoint_rest_api.graph_client import GraphClient, GraphClientError
from sharepoint_rest_api.views.base import AbstractSharePointViewSet, SearchResponseMixin


class GraphBasedSearchViewSet(SearchResponseMixin, AbstractSharePointViewSet):
    """ViewSet that uses Microsoft Graph Search API instead of SharePoint Search API."""

    folder = None
    filter_backends = []

    @cached_property
    def client(self):
        try:
            return GraphClient(
                url=f"{config.SHAREPOINT_TENANT}/{config.SHAREPOINT_SITE_TYPE}/{config.SHAREPOINT_SITE}",
                relative_url=f"{config.SHAREPOINT_SITE_TYPE}/{config.SHAREPOINT_SITE}",
                folder=self.folder,
            )
        except GraphClientError:
            raise PermissionDenied

    def _get_page_size(self):
        return config.GRAPH_PAGE_SIZE

    def list(self, request, *args, **kwargs):
        try:
            queryset = self.filter_queryset(self.get_queryset())
            serializer = self.get_serializer(queryset, many=True)
            response = Response(serializer.data)
        except (ClientRequestException, GraphClientError) as e:
            return HttpResponseBadRequest(str(e))
        return self._build_paginated_response(request, response)
