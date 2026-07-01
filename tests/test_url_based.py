from unittest import mock

import pytest

from django.http import HttpResponse, HttpResponseBadRequest
from django.test import RequestFactory

from sharepoint_rest_api.client import SharePointClient, SharePointClientException
from sharepoint_rest_api.graph_client import GraphClientError
from sharepoint_rest_api.models import SharePointLibrary, SharePointSite, SharePointTenant
from sharepoint_rest_api.views.files import UploadViewSet
from sharepoint_rest_api.views.settings_based import SharePointSettingsRestViewSet
from sharepoint_rest_api.views.url_based import (
    SharePointUrlCamlViewSet,
    SharePointUrlFileViewSet,
    SharePointUrlRestViewSet,
    SharePointUrlSearchViewSet,
)
from rest_framework.exceptions import PermissionDenied


@pytest.mark.django_db
def test_is_public():
    tenant = SharePointTenant.objects.create(url="https://contoso.sharepoint.com/")
    site = SharePointSite.objects.create(tenant=tenant, name="MySite")
    SharePointLibrary.objects.create(site=site, name="Documents", public=True)
    view = SharePointUrlRestViewSet()
    view.kwargs = {"tenant": "contoso", "site": "MySite", "folder": "Documents"}
    assert view.is_public() is True


@pytest.mark.django_db
@mock.patch.object(SharePointClient, "__init__", return_value=None)
def test_client_with_username(mock_init):
    tenant = SharePointTenant.objects.create(
        url="https://contoso.sharepoint.com/",
        username="testuser",
        password="testpass",
    )
    site = SharePointSite.objects.create(tenant=tenant, name="MySite")
    SharePointLibrary.objects.create(site=site, name="Documents", public=True)
    view = SharePointUrlRestViewSet()
    view.kwargs = {"tenant": "contoso", "site": "MySite", "folder": "Documents"}
    view.client
    _, kwargs = mock_init.call_args
    assert kwargs["username"] == "testuser"
    assert kwargs["password"] == "testpass"


@pytest.mark.django_db
@mock.patch.object(SharePointClient, "__init__", return_value=None)
def test_client_with_client_id(mock_init):
    tenant = SharePointTenant.objects.create(
        url="https://contoso.sharepoint.com/",
        client_id="test-client-id",
        client_cert_tenant="test-tenant.onmicrosoft.com",
        client_cert_thumbprint="abc123",
        client_cert_path="/path/to/cert.pem",
        client_cert_passphrase="testphrase",
    )
    site = SharePointSite.objects.create(tenant=tenant, name="MySite")
    SharePointLibrary.objects.create(site=site, name="Documents", public=False)
    view = SharePointUrlRestViewSet()
    view.kwargs = {"tenant": "contoso", "site": "MySite", "folder": "Documents"}
    view.client
    _, kwargs = mock_init.call_args
    assert kwargs["client_id"] == "test-client-id"
    assert kwargs["cert_tenant"] == "test-tenant.onmicrosoft.com"
    assert kwargs["cert_thumbprint"] == "abc123"
    assert kwargs["cert_path"] == "/path/to/cert.pem"
    assert kwargs["cert_passphrase"] == "testphrase"


@pytest.mark.django_db
@mock.patch.object(SharePointClient, "__init__", side_effect=SharePointClientException("fail"))
def test_client_raises_permission_denied(mock_init):
    tenant = SharePointTenant.objects.create(url="https://contoso.sharepoint.com/")
    site = SharePointSite.objects.create(tenant=tenant, name="MySite")
    SharePointLibrary.objects.create(site=site, name="Documents")
    view = SharePointUrlRestViewSet()
    view.kwargs = {"tenant": "contoso", "site": "MySite", "folder": "Documents"}
    with pytest.raises(PermissionDenied):
        view.client


# ---- SettingsBasedSharePointViewSet coverage ----


@pytest.mark.django_db
def test_settings_is_public():
    tenant = SharePointTenant.objects.create(url="https://contoso.sharepoint.com/")
    site = SharePointSite.objects.create(tenant=tenant, name="MySite")
    SharePointLibrary.objects.create(site=site, name="Documents", public=True)
    view = SharePointSettingsRestViewSet()
    view.kwargs = {"folder": "Documents"}
    assert view.is_public().exists()


@pytest.mark.django_db
@mock.patch.object(SharePointClient, "__init__", side_effect=SharePointClientException("fail"))
def test_settings_client_raises_permission_denied(mock_init):
    view = SharePointSettingsRestViewSet()
    view.kwargs = {"folder": "Documents"}
    with pytest.raises(PermissionDenied):
        view.client


# ---- FileSharePointViewSet coverage (views/base.py) ----


@pytest.mark.django_db
def test_file_get_object():
    tenant = SharePointTenant.objects.create(url="https://contoso.sharepoint.com/")
    site = SharePointSite.objects.create(tenant=tenant, name="MySite")
    SharePointLibrary.objects.create(site=site, name="Documents")

    view = SharePointUrlFileViewSet()
    view.kwargs = {"tenant": "contoso", "site": "MySite", "folder": "Documents", "filename": "report.pdf"}
    mock_client = mock.MagicMock()
    mock_file = mock.MagicMock()
    mock_file.properties = {"Name": "report.pdf"}
    mock_client.read_file.return_value = mock_file
    view.client = mock_client

    result = view.get_object()
    mock_client.read_file.assert_called_once_with("report.pdf")
    assert result == mock_file


@pytest.mark.django_db
def test_file_get_queryset():
    tenant = SharePointTenant.objects.create(url="https://contoso.sharepoint.com/")
    site = SharePointSite.objects.create(tenant=tenant, name="MySite")
    SharePointLibrary.objects.create(site=site, name="Documents")

    view = SharePointUrlFileViewSet()
    view.kwargs = {"tenant": "contoso", "site": "MySite", "folder": "Documents"}
    mock_client = mock.MagicMock()
    mock_files = [mock.MagicMock()]
    mock_client.read_files.return_value = mock_files
    view.client = mock_client

    request_mock = mock.MagicMock()
    request_mock.query_params.dict.return_value = {}
    view.request = request_mock

    result = view.get_queryset()
    mock_client.read_files.assert_called_once_with(filters={})
    assert result == mock_files


@pytest.mark.django_db
@mock.patch("sharepoint_rest_api.views.base.File")
def test_file_download(mock_file):
    tenant = SharePointTenant.objects.create(url="https://contoso.sharepoint.com/")
    site = SharePointSite.objects.create(tenant=tenant, name="MySite")
    SharePointLibrary.objects.create(site=site, name="Documents")

    view = SharePointUrlFileViewSet()
    view.kwargs = {"tenant": "contoso", "site": "MySite", "folder": "Documents", "filename": "report.pdf"}
    mock_client = mock.MagicMock()
    mock_sh_file = mock.MagicMock()
    mock_sh_file.properties = {"ServerRelativeUrl": "/sites/MySite/Documents/report.pdf", "Name": "report.pdf"}
    mock_client.read_file.return_value = mock_sh_file
    view.client = mock_client

    mock_response = mock.MagicMock()
    mock_response.content = b"pdf content"
    mock_response.status_code = 200
    mock_response.headers = {"Content-Type": "application/pdf"}
    mock_file.open_binary.return_value = mock_response

    request_mock = mock.MagicMock()
    view.request = request_mock

    result = view.download(request_mock)
    assert isinstance(result, HttpResponse)
    assert result.status_code == 200
    assert result["Content-Disposition"] == "attachment; filename=report.pdf"


@pytest.mark.django_db
def test_caml_get_queryset_cache_hit():
    tenant = SharePointTenant.objects.create(url="https://contoso.sharepoint.com/")
    site = SharePointSite.objects.create(tenant=tenant, name="CacheTestSite")
    SharePointLibrary.objects.create(site=site, name="CacheTestLib")

    view = SharePointUrlCamlViewSet()
    view.kwargs = {"tenant": "contoso", "site": "CacheTestSite", "folder": "CacheTestLib"}

    mock_client = mock.MagicMock()
    mock_raw = mock.MagicMock()
    mock_raw.to_json.return_value = {"data": "result"}
    mock_client.read_caml_items.return_value = mock_raw
    view.client = mock_client

    request_mock = mock.MagicMock()
    request_mock.query_params.dict.return_value = {}
    view.request = request_mock

    view.get_queryset()
    mock_client.read_caml_items.assert_called_once()
    view.get_queryset()
    mock_client.read_caml_items.assert_called_once()


@pytest.mark.django_db
def test_rest_get_queryset_cache_hit():
    tenant = SharePointTenant.objects.create(url="https://contoso.sharepoint.com/")
    site = SharePointSite.objects.create(tenant=tenant, name="CacheTestSite2")
    SharePointLibrary.objects.create(site=site, name="CacheTestLib2")

    view = SharePointUrlRestViewSet()
    view.kwargs = {"tenant": "contoso", "site": "CacheTestSite2", "folder": "CacheTestLib2"}

    mock_client = mock.MagicMock()
    mock_raw = mock.MagicMock()
    mock_raw.to_json.return_value = {"data": "result"}
    mock_client.read_items.return_value = mock_raw
    view.client = mock_client

    request_mock = mock.MagicMock()
    request_mock.query_params.dict.return_value = {}
    view.request = request_mock

    view.get_queryset()
    mock_client.read_items.assert_called_once()
    view.get_queryset()
    mock_client.read_items.assert_called_once()


# ---- UploadViewSet coverage (views/files.py) ----


@mock.patch("sharepoint_rest_api.views.files.SharePointClient")
def test_upload_list(mock_client_cls):
    view = UploadViewSet()
    request_mock = mock.MagicMock()
    result = view.list(request_mock)
    assert result.status_code == 200
    assert result.data == "Use the form to upload files"


@mock.patch("sharepoint_rest_api.views.files.SharePointClient")
def test_upload_create(mock_client_cls):
    view = UploadViewSet()
    mock_file = mock.MagicMock()
    mock_file.name = "test.pdf"
    mock_file.read.return_value = b"content"
    request_mock = mock.MagicMock()
    request_mock.FILES = {"file_uploaded": mock_file}
    request_mock.POST = {"folder": "Documents", "metadata": '{"Title": "Test"}'}
    result = view.create(request_mock)
    mock_client_cls.assert_called_once()
    mock_client_cls.return_value.upload_file.assert_called_once_with(
        mock_file, folder_name="Documents", metadata={"Title": "Test"}
    )
    assert result.status_code == 200


@mock.patch("sharepoint_rest_api.views.files.SharePointClient")
def test_upload_create_no_metadata(mock_client_cls):
    view = UploadViewSet()
    mock_file = mock.MagicMock()
    mock_file.name = "test.pdf"
    request_mock = mock.MagicMock()
    request_mock.FILES = {"file_uploaded": mock_file}
    request_mock.POST = {"folder": "Documents"}
    result = view.create(request_mock)
    mock_client_cls.return_value.upload_file.assert_called_once_with(mock_file, folder_name="Documents", metadata=None)
    assert result.status_code == 200


# ---- CamlQuery/RestQuery cache hit coverage (views/base.py) ----


# ---- SharePointSearchViewSet coverage (views/base.py) ----


@pytest.mark.django_db
def test_search_get_queryset():
    tenant = SharePointTenant.objects.create(url="https://contoso.sharepoint.com/")
    site = SharePointSite.objects.create(tenant=tenant, name="MySite")
    SharePointLibrary.objects.create(site=site, name="Documents")

    view = SharePointUrlSearchViewSet()
    view.kwargs = {"tenant": "contoso", "site": "MySite", "folder": "Documents"}
    view.serializer_class = mock.MagicMock()
    view.serializer_class._declared_fields = {"Title": mock.MagicMock(), "Path": mock.MagicMock()}

    mock_client = mock.MagicMock()
    mock_client.search.return_value = (["item1", "item2"], 10)
    view.client = mock_client

    request_mock = mock.MagicMock()
    request_mock.query_params.dict.return_value = {"search": "test", "selected": "Title", "page": "2"}
    view.request = request_mock
    view.action = "list"
    view.format_kwarg = None
    request_mock.parser_context = {"kwargs": {}}

    result = view.get_queryset()
    mock_client.search.assert_called_once()
    assert result == ["item1", "item2"]


@pytest.mark.django_db
def test_search_list_pagination():
    tenant = SharePointTenant.objects.create(url="https://contoso.sharepoint.com/")
    site = SharePointSite.objects.create(tenant=tenant, name="MySite")
    SharePointLibrary.objects.create(site=site, name="Documents")

    view = SharePointUrlSearchViewSet()
    view.kwargs = {"tenant": "contoso", "site": "MySite", "folder": "Documents"}
    view.serializer_class = mock.MagicMock()
    view.serializer_class._declared_fields = {"Title": mock.MagicMock(), "Path": mock.MagicMock()}

    mock_client = mock.MagicMock()
    mock_client.search.return_value = ([{"Title": "doc1", "Path": "/a"}], 50)
    view.client = mock_client
    view.action = "list"
    view.format_kwarg = None

    request = RequestFactory().get("/search", {"search": "test", "page": "1"})
    request.query_params = request.GET
    request.parser_context = {"kwargs": {}}
    view.request = request

    response = view.list(request)
    assert response.data["total_rows"] == 50
    assert response.data["first"] is not None


@pytest.mark.django_db
def test_search_list_non_first_page():
    tenant = SharePointTenant.objects.create(url="https://contoso.sharepoint.com/")
    site = SharePointSite.objects.create(tenant=tenant, name="MySite")
    SharePointLibrary.objects.create(site=site, name="Documents")

    view = SharePointUrlSearchViewSet()
    view.kwargs = {"tenant": "contoso", "site": "MySite", "folder": "Documents"}
    view.serializer_class = mock.MagicMock()
    view.serializer_class._declared_fields = {"Title": mock.MagicMock(), "Path": mock.MagicMock()}

    mock_client = mock.MagicMock()
    mock_client.search.return_value = ([{"Title": "doc1", "Path": "/a"}], 5)
    view.client = mock_client
    view.action = "list"
    view.format_kwarg = None

    request = RequestFactory().get("/search", {"search": "test", "page": "2"})
    request.query_params = request.GET
    request.parser_context = {"kwargs": {}}
    view.request = request

    response = view.list(request)
    assert response.data["total_rows"] == 5
    assert response.data["previous"] is not None
    assert response.data["next"] is None


@pytest.mark.django_db
def test_search_get_queryset_cache_hit():
    tenant = SharePointTenant.objects.create(url="https://contoso.sharepoint.com/")
    site = SharePointSite.objects.create(tenant=tenant, name="MySite")
    SharePointLibrary.objects.create(site=site, name="Documents")

    view = SharePointUrlSearchViewSet()
    view.kwargs = {"tenant": "contoso", "site": "MySite", "folder": "Documents"}
    view.serializer_class = mock.MagicMock()
    view.serializer_class._declared_fields = {"Title": mock.MagicMock(), "Path": mock.MagicMock()}

    mock_client = mock.MagicMock()
    mock_client.search.return_value = (["item1"], 10)
    view.client = mock_client
    view.action = "list"
    view.format_kwarg = None

    request = RequestFactory().get("/search", {"search": "test"})
    request.query_params = request.GET
    request.parser_context = {"kwargs": {}}
    view.request = request

    view.get_queryset()
    mock_client.search.assert_called_once()
    result2 = view.get_queryset()
    mock_client.search.assert_called_once()
    assert result2 == ["item1"]


@pytest.mark.django_db
def test_search_list_catches_exception():
    tenant = SharePointTenant.objects.create(url="https://contoso.sharepoint.com/")
    site = SharePointSite.objects.create(tenant=tenant, name="MySite")
    SharePointLibrary.objects.create(site=site, name="Documents")

    view = SharePointUrlSearchViewSet()
    view.kwargs = {"tenant": "contoso", "site": "MySite", "folder": "Documents"}
    view.serializer_class = mock.MagicMock()
    view.serializer_class._declared_fields = {"Title": mock.MagicMock(), "Path": mock.MagicMock()}
    view.client = mock.MagicMock()
    view.client.search.side_effect = GraphClientError("graph error")
    view.action = "list"
    view.format_kwarg = None

    request = RequestFactory().get("/search", {"search": "exception_test_unique"})
    request.query_params = request.GET
    request.parser_context = {"kwargs": {}}
    view.request = request

    response = view.list(request)
    assert isinstance(response, HttpResponseBadRequest)
    assert b"graph error" in response.content
