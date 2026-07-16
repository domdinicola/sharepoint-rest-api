from unittest import mock

from django.http import HttpResponse, HttpResponseBadRequest
from django.test import RequestFactory
import pytest
from rest_framework.response import Response

from sharepoint_rest_api.graph_client import GraphClientError
from sharepoint_rest_api.models import SourceId
from sharepoint_rest_api.views.graph_based import GraphBasedSearchViewSet, GraphFileDownloadViewSet
from rest_framework.exceptions import PermissionDenied


def _make_viewset():
    viewset = GraphBasedSearchViewSet()
    viewset.kwargs = {}
    viewset.folder = "docs"
    viewset.tenant = "t"
    viewset.site = "s"
    viewset.action = "list"
    viewset.format_kwarg = None
    viewset.serializer_class = mock.MagicMock()
    viewset.serializer_class._declared_fields = {"Title": mock.MagicMock()}
    request = RequestFactory().get("/graph/search", {"page": "1"})
    request.query_params = request.GET
    request.parser_context = {"kwargs": {}}
    viewset.request = request
    viewset.headers = request.headers
    return viewset, request


@mock.patch("sharepoint_rest_api.views.graph_based.GraphClient")
def test_client_success(mock_graph_client):
    viewset = GraphBasedSearchViewSet()
    viewset.folder = "Documents"
    result = viewset.client
    mock_graph_client.assert_called_once_with(
        url="https://unitst.sharepoint.com/sites/GLB-DRP",
        relative_url="sites/GLB-DRP",
        folder="Documents",
    )
    assert result == mock_graph_client.return_value


@mock.patch("sharepoint_rest_api.views.graph_based.GraphClient")
def test_client_raises_permission_denied(mock_graph_client):
    mock_graph_client.side_effect = GraphClientError("auth failed")
    viewset = GraphBasedSearchViewSet()
    viewset.folder = "Documents"
    with pytest.raises(PermissionDenied):
        viewset.client


@mock.patch("sharepoint_rest_api.views.graph_based.config")
@mock.patch("sharepoint_rest_api.views.graph_based.GraphClient")
def test_client_uses_config(mock_graph_client, mock_config):
    mock_config.SHAREPOINT_TENANT = "https://contoso.sharepoint.com"
    mock_config.SHAREPOINT_SITE_TYPE = "teams"
    mock_config.SHAREPOINT_SITE = "MyTeam"
    viewset = GraphBasedSearchViewSet()
    viewset.folder = "Shared Documents"
    viewset.client
    mock_graph_client.assert_called_once_with(
        url="https://contoso.sharepoint.com/teams/MyTeam",
        relative_url="teams/MyTeam",
        folder="Shared Documents",
    )


def test_list_happy_path():
    viewset, request = _make_viewset()
    viewset.get_queryset = mock.MagicMock(return_value=[{"Title": "doc1"}])

    viewset._build_paginated_response = mock.MagicMock(return_value=Response({"items": [{"Title": "doc1"}]}))

    response = viewset.list(request)
    assert response.status_code == 200
    viewset._build_paginated_response.assert_called_once()
    viewset.get_queryset.assert_called_once()


def test_list_catches_graph_client_exception():
    viewset, request = _make_viewset()
    viewset.get_queryset = mock.MagicMock()
    viewset.get_queryset.side_effect = GraphClientError("graph error")

    response = viewset.list(request)
    assert isinstance(response, HttpResponseBadRequest)
    assert b"graph error" in response.content


def test_get_page_size():
    viewset, _ = _make_viewset()
    result = viewset._get_page_size()
    assert result == 25


def test_apply_source_id_filters_no_source_id():
    viewset, _ = _make_viewset()
    qp = {"search": "test"}
    viewset._apply_source_id_filters(qp)
    assert qp == {"search": "test"}


@mock.patch("sharepoint_rest_api.views.graph_based.SourceId.objects")
def test_apply_source_id_filters_not_found(mock_objects):
    mock_objects.get.side_effect = SourceId.DoesNotExist
    viewset, _ = _make_viewset()
    qp = {"source_id": "nonexistent"}
    viewset._apply_source_id_filters(qp)
    assert qp == {"source_id": "nonexistent", "order_by": "-LastModifiedTime"}


@mock.patch("sharepoint_rest_api.views.graph_based.SourceId")
def test_apply_source_id_filters_with_default_filters(mock_source_id):
    mock_source_id.objects.get.return_value.default_filters = {
        "filters": {"Donor": "Red Cross"},
    }
    mock_source_id.objects.get.return_value.search_kql = ""
    mock_source_id.objects.get.return_value.exclude_paths = []
    mock_source_id.objects.get.return_value.order_by = None
    viewset, _ = _make_viewset()
    qp = {"source_id": "src1"}
    viewset._apply_source_id_filters(qp)
    assert qp.get("Donor") == "Red Cross"


@mock.patch("sharepoint_rest_api.views.graph_based.SourceId")
def test_apply_source_id_filters_does_not_overwrite(mock_source_id):
    mock_source_id.objects.get.return_value.default_filters = {
        "filters": {"Donor": "Red Cross"},
    }
    mock_source_id.objects.get.return_value.search_kql = ""
    mock_source_id.objects.get.return_value.exclude_paths = []
    mock_source_id.objects.get.return_value.order_by = None
    viewset, _ = _make_viewset()
    qp = {"source_id": "src1", "Donor": "Existing"}
    viewset._apply_source_id_filters(qp)
    assert qp.get("Donor") == "Existing"


@mock.patch("sharepoint_rest_api.views.graph_based.SourceId")
def test_apply_source_id_filters_search_kql_without_existing(mock_source_id):
    mock_source_id.objects.get.return_value.default_filters = {
        "search_kql": "Donor:Red Cross",
    }
    mock_source_id.objects.get.return_value.filters = {}
    mock_source_id.objects.get.return_value.exclude_paths = []
    mock_source_id.objects.get.return_value.order_by = None
    viewset, _ = _make_viewset()
    qp = {"source_id": "src1"}
    viewset._apply_source_id_filters(qp)
    assert qp.get("search") == "Donor:Red Cross"


@mock.patch("sharepoint_rest_api.views.graph_based.SourceId")
def test_apply_source_id_filters_search_kql_with_existing(mock_source_id):
    mock_source_id.objects.get.return_value.default_filters = {
        "search_kql": "Donor:Red Cross",
    }
    mock_source_id.objects.get.return_value.filters = {}
    mock_source_id.objects.get.return_value.exclude_paths = []
    mock_source_id.objects.get.return_value.order_by = None
    viewset, _ = _make_viewset()
    qp = {"source_id": "src1", "search": "ReportStatus:Final"}
    viewset._apply_source_id_filters(qp)
    assert qp.get("search") == "(Donor:Red Cross) AND (ReportStatus:Final)"


@mock.patch("sharepoint_rest_api.views.graph_based.SourceId")
def test_apply_source_id_filters_exclude_paths(mock_source_id):
    mock_source_id.objects.get.return_value.default_filters = {
        "exclude_paths": ["/archive", "/old"],
    }
    mock_source_id.objects.get.return_value.filters = {}
    mock_source_id.objects.get.return_value.search_kql = ""
    mock_source_id.objects.get.return_value.order_by = None
    viewset, _ = _make_viewset()
    qp = {"source_id": "src1"}
    viewset._apply_source_id_filters(qp)
    assert '-Path:"/archive"' in qp["search"]
    assert '-Path:"/old"' in qp["search"]


@mock.patch("sharepoint_rest_api.views.graph_based.SourceId")
def test_apply_source_id_filters_order_by(mock_source_id):
    mock_source_id.objects.get.return_value.default_filters = {
        "order_by": "Size desc",
    }
    mock_source_id.objects.get.return_value.filters = {}
    mock_source_id.objects.get.return_value.search_kql = ""
    mock_source_id.objects.get.return_value.exclude_paths = []
    viewset, _ = _make_viewset()
    qp = {"source_id": "src1"}
    viewset._apply_source_id_filters(qp)
    assert qp.get("order_by") == "Size desc"


@mock.patch("sharepoint_rest_api.views.graph_based.SourceId")
def test_apply_source_id_filters_default_order_by(mock_source_id):
    mock_source_id.objects.get.return_value.default_filters = {}
    viewset, _ = _make_viewset()
    qp = {"source_id": "src1"}
    viewset._apply_source_id_filters(qp)
    assert qp.get("order_by") == "-LastModifiedTime"


@mock.patch("sharepoint_rest_api.views.graph_based.SourceId")
def test_apply_source_id_filters_existing_order_by_not_overridden(mock_source_id):
    mock_source_id.objects.get.return_value.default_filters = {}
    viewset, _ = _make_viewset()
    qp = {"source_id": "src1", "order_by": "Size"}
    viewset._apply_source_id_filters(qp)
    assert qp.get("order_by") == "Size"


# ---- GraphFileDownloadViewSet -------------------------------------------------


def _make_download_viewset():
    viewset = GraphFileDownloadViewSet()
    viewset.kwargs = {}
    viewset.action = "download"
    viewset.format_kwarg = None
    request = RequestFactory().get("/graph/download")
    request.query_params = request.GET
    request.parser_context = {"kwargs": {}}
    viewset.request = request
    viewset.headers = request.headers
    return viewset, request


@mock.patch("sharepoint_rest_api.views.graph_based.GraphClient")
def test_download_viewset_client_success(mock_graph_client):
    viewset = GraphFileDownloadViewSet()
    result = viewset.client
    mock_graph_client.assert_called_once_with(
        url="https://unitst.sharepoint.com/sites/GLB-DRP",
        relative_url="sites/GLB-DRP",
        folder="Documents",
    )
    assert result == mock_graph_client.return_value


@mock.patch("sharepoint_rest_api.views.graph_based.GraphClient")
def test_download_viewset_client_raises_permission_denied(mock_graph_client):
    mock_graph_client.side_effect = GraphClientError("auth failed")
    viewset = GraphFileDownloadViewSet()
    with pytest.raises(PermissionDenied):
        viewset.client


@mock.patch("sharepoint_rest_api.views.graph_based.GraphClient")
def test_download_with_drive_id_and_item_id(mock_graph_client):
    viewset, _ = _make_download_viewset()
    mock_client = mock_graph_client.return_value
    mock_resp = mock.MagicMock()
    mock_resp.content = b"file-bytes"
    mock_resp.status_code = 200
    mock_resp.headers = {"Content-Type": "application/pdf"}
    mock_client.download_item.return_value = mock_resp

    request = RequestFactory().get("/graph/download/test.pdf", {"drive_id": "d1", "item_id": "i1"})
    request.query_params = request.GET
    response = viewset.download(request, filename="test.pdf")

    assert isinstance(response, HttpResponse)
    assert response.status_code == 200
    assert response.content == b"file-bytes"
    mock_client.download_item.assert_called_once_with("d1", "i1")


@mock.patch("sharepoint_rest_api.views.graph_based.GraphClient")
def test_download_with_site_id_drive_not_found(mock_graph_client):
    viewset, _ = _make_download_viewset()
    mock_client = mock_graph_client.return_value
    mock_client.get_drive_id_by_name.return_value = None
    mock_resp = mock.MagicMock()
    mock_resp.content = b"file-bytes"
    mock_resp.status_code = 200
    mock_resp.headers = {"Content-Type": "application/octet-stream"}
    mock_client.download_file.return_value = mock_resp

    request = RequestFactory().get("/graph/download/test.pdf", {"site_id": "s1"})
    request.query_params = request.GET
    response = viewset.download(request, filename="test.pdf", folder="SharedDocs")

    assert isinstance(response, HttpResponse)
    assert response.status_code == 200
    mock_client.download_file.assert_called_once_with("SharedDocs/test.pdf", drive_id=None, site_id="s1")


@mock.patch("sharepoint_rest_api.views.graph_based.GraphClient")
def test_download_with_site_id_drive_found(mock_graph_client):
    viewset, _ = _make_download_viewset()
    mock_client = mock_graph_client.return_value
    mock_client.get_drive_id_by_name.return_value = "drive-abc"
    mock_resp = mock.MagicMock()
    mock_resp.content = b"file-bytes"
    mock_resp.status_code = 200
    mock_resp.headers = {"Content-Type": "application/pdf"}
    mock_client.download_file.return_value = mock_resp

    request = RequestFactory().get("/graph/download/test.pdf", {"site_id": "s1"})
    request.query_params = request.GET
    response = viewset.download(request, filename="test.pdf", folder="SharedDocs")

    assert isinstance(response, HttpResponse)
    assert response.status_code == 200
    mock_client.download_file.assert_called_once_with("test.pdf", drive_id="drive-abc", site_id="s1")


@mock.patch("sharepoint_rest_api.views.graph_based.GraphClient")
def test_download_without_site_id_or_drive_item(mock_graph_client):
    viewset, _ = _make_download_viewset()
    request = RequestFactory().get("/graph/download/test.pdf")
    request.query_params = request.GET
    response = viewset.download(request, filename="test.pdf")

    assert isinstance(response, HttpResponseBadRequest)
    assert b"site_id or drive_id+item_id" in response.content


@mock.patch("sharepoint_rest_api.views.graph_based.GraphClient")
def test_download_graph_client_error(mock_graph_client):
    viewset, _ = _make_download_viewset()
    mock_client = mock_graph_client.return_value
    mock_client.download_item.side_effect = GraphClientError("download failed")

    request = RequestFactory().get("/graph/download/test.pdf", {"drive_id": "d1", "item_id": "i1"})
    request.query_params = request.GET
    response = viewset.download(request, filename="test.pdf")

    assert isinstance(response, HttpResponseBadRequest)
    assert b"download failed" in response.content


@mock.patch("sharepoint_rest_api.views.graph_based.GraphClient")
def test_download_with_empty_folder(mock_graph_client):
    viewset, _ = _make_download_viewset()
    mock_client = mock_graph_client.return_value
    mock_client.get_drive_id_by_name.return_value = None
    mock_resp = mock.MagicMock()
    mock_resp.content = b"data"
    mock_resp.status_code = 200
    mock_resp.headers = {}
    mock_client.download_file.return_value = mock_resp

    request = RequestFactory().get("/graph/download/test.pdf", {"site_id": "s1"})
    request.query_params = request.GET
    response = viewset.download(request, filename="test.pdf", folder="")

    assert isinstance(response, HttpResponse)
    mock_client.download_file.assert_called_once_with("test.pdf", drive_id=None, site_id="s1")


@mock.patch("sharepoint_rest_api.views.graph_based.GraphClient")
def test_download_sets_content_disposition(mock_graph_client):
    viewset, _ = _make_download_viewset()
    mock_client = mock_graph_client.return_value
    mock_resp = mock.MagicMock()
    mock_resp.content = b"data"
    mock_resp.status_code = 200
    mock_resp.headers = {"Content-Type": "text/plain"}
    mock_client.download_item.return_value = mock_resp

    request = RequestFactory().get("/graph/download/report.csv", {"drive_id": "d1", "item_id": "i1"})
    request.query_params = request.GET
    response = viewset.download(request, filename="report.csv")

    assert response["Content-Disposition"] == "attachment; filename=report.csv"


@mock.patch("sharepoint_rest_api.views.graph_based.GraphClient")
def test_download_default_content_type(mock_graph_client):
    viewset, _ = _make_download_viewset()
    mock_client = mock_graph_client.return_value
    mock_resp = mock.MagicMock()
    mock_resp.content = b"data"
    mock_resp.status_code = 200
    mock_resp.headers = {}
    mock_client.download_item.return_value = mock_resp

    request = RequestFactory().get("/graph/download/file", {"drive_id": "d1", "item_id": "i1"})
    request.query_params = request.GET
    response = viewset.download(request, filename="file")

    assert response["Content-Type"] == "application/octet-stream"
