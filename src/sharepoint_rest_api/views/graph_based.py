from django.http import HttpResponseBadRequest
from django.utils.functional import cached_property
from office365.runtime.client_request_exception import ClientRequestException
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from sharepoint_rest_api import config
from sharepoint_rest_api.graph_client import GraphClient, GraphClientError
from sharepoint_rest_api.models import SourceId
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

    def _apply_source_id_filters(self, qp):
        source_id = qp.get("source_id")
        if not source_id:
            return
        try:
            source_obj = SourceId.objects.get(source_id=source_id)
            default_filters = source_obj.default_filters or {}
        except SourceId.DoesNotExist:
            default_filters = {}
        for key, value in default_filters.get("filters", {}).items():
            if key not in qp:
                qp[key] = value
        search_kql = default_filters.get("search_kql", "")
        if search_kql:
            existing_search = qp.get("search", "")
            if existing_search:
                qp["search"] = f"({search_kql}) AND ({existing_search})"
            else:
                qp["search"] = search_kql
        exclude_paths = default_filters.get("exclude_paths", [])
        if exclude_paths:
            path_exclusions = " ".join(f'-Path:"{p}"' for p in exclude_paths)
            qp["search"] = f"{path_exclusions} {qp.get('search', '')}".strip()
        order_by = default_filters.get("order_by")
        if order_by and "order_by" not in qp:
            qp["order_by"] = order_by
        elif "order_by" not in qp:
            qp["order_by"] = "LastModifiedTime desc"

    def list(self, request, *args, **kwargs):
        try:
            queryset = self.filter_queryset(self.get_queryset())
            serializer = self.get_serializer(queryset, many=True)
            response = Response(serializer.data)
        except (ClientRequestException, GraphClientError) as e:
            return HttpResponseBadRequest(str(e))
        return self._build_paginated_response(request, response)
