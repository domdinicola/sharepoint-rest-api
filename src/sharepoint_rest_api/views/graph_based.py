from django.http import HttpResponse, HttpResponseBadRequest
from django.utils.functional import cached_property
from office365.runtime.client_request_exception import ClientRequestException
from rest_framework import viewsets
from rest_framework.decorators import action
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
            qp["order_by"] = "-LastModifiedTime"

    def list(self, request, *args, **kwargs):
        try:
            queryset = self.filter_queryset(self.get_queryset())
            serializer = self.get_serializer(queryset, many=True)
            response = Response(serializer.data)
        except (ClientRequestException, GraphClientError) as e:
            return HttpResponseBadRequest(str(e))
        return self._build_paginated_response(request, response)


class GraphFileDownloadViewSet(viewsets.ViewSet):
    """ViewSet that downloads files via the Microsoft Graph API.

    Accepts ``site_id`` or ``drive_id`` + ``item_id`` as query parameters
    to locate the file in the target SharePoint site.
    """

    lookup_field = "filename"
    lookup_value_regex = "[^/]+"

    @cached_property
    def client(self):
        try:
            return GraphClient(
                url=f"{config.SHAREPOINT_TENANT}/{config.SHAREPOINT_SITE_TYPE}/{config.SHAREPOINT_SITE}",
                relative_url=f"{config.SHAREPOINT_SITE_TYPE}/{config.SHAREPOINT_SITE}",
                folder="Documents",
            )
        except GraphClientError:
            raise PermissionDenied

    @action(detail=True, methods=["get"])
    def download(self, request, *args, **kwargs):
        filename = kwargs.get("filename")
        folder = kwargs.get("folder", "")
        site_id = request.query_params.get("site_id")
        drive_id = request.query_params.get("drive_id")
        item_id = request.query_params.get("item_id")
        try:
            if drive_id and item_id:
                graph_response = self.client.download_item(drive_id, item_id)
            else:
                if not site_id:
                    return HttpResponseBadRequest("site_id or drive_id+item_id query parameter is required")
                drive_id = self.client.get_drive_id_by_name(folder, site_id=site_id)
                if drive_id:
                    file_path = filename
                else:
                    file_path = f"{folder}/{filename}" if folder else filename
                graph_response = self.client.download_file(file_path, drive_id=drive_id, site_id=site_id)
            django_response = HttpResponse(
                content=graph_response.content,
                status=graph_response.status_code,
                content_type=graph_response.headers.get("Content-Type", "application/octet-stream"),
            )
            django_response["Content-Disposition"] = "attachment; filename=%s" % filename
            return django_response
        except GraphClientError as e:
            return HttpResponseBadRequest(str(e))
