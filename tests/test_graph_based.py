from unittest import mock

from django.http import HttpResponseBadRequest
from django.test import RequestFactory
import pytest
from rest_framework.response import Response

from sharepoint_rest_api.graph_client import GraphClientError
from sharepoint_rest_api.views.graph_based import GraphBasedSearchViewSet
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
