from unittest import mock

from django.http import HttpResponseBadRequest
from django.test import RequestFactory
import pytest

from sharepoint_rest_api.graph_client import GraphClientError
from sharepoint_rest_api.views.graph_based import GraphBasedSearchViewSet
from rest_framework.exceptions import PermissionDenied


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


def test_list_catches_graph_client_exception():
    viewset = GraphBasedSearchViewSet()
    viewset.kwargs = {}
    viewset.folder = "docs"
    viewset.tenant = "t"
    viewset.site = "s"
    viewset.action = "list"
    viewset.format_kwarg = None
    viewset.serializer_class = mock.MagicMock()
    viewset.serializer_class._declared_fields = {"Title": mock.MagicMock()}
    viewset.get_queryset = mock.MagicMock()
    viewset.get_queryset.side_effect = GraphClientError("graph error")

    request = RequestFactory().get("/graph/search")
    request.query_params = request.GET
    request.parser_context = {"kwargs": {}}
    viewset.request = request

    response = viewset.list(request)
    assert isinstance(response, HttpResponseBadRequest)
    assert b"graph error" in response.content
