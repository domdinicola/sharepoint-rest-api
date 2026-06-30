from unittest import mock

from django.conf import settings as django_settings

from sharepoint_rest_api.serializers.fields import SharePointPropertyManyField
from sharepoint_rest_api.serializers.sharepoint import (
    SharePointFileSerializer,
    SharePointSearchSerializer,
    SharePointSettingsSerializer,
    SharePointUrlSerializer,
)


# ---- fields.py: empty values in SharePointPropertyManyField ----


def test_property_many_field_empty_values():
    field = SharePointPropertyManyField(source="donors")
    result = field.get_attribute({"Donors": ""})
    assert result == ""


# ---- sharepoint.py: SharePointSettingsSerializer.get_download_url ----


@mock.patch("sharepoint_rest_api.serializers.sharepoint.reverse")
def test_settings_serializer_empty_filename(mock_reverse):
    mock_reverse.return_value = "/path"
    serializer = SharePointSettingsSerializer(context={"folder": "docs"})
    serializer.instance = {"FileLeafRef": "", "Title": ""}
    url = serializer.get_download_url(serializer.instance)
    assert f"{django_settings.HOST}/path" == url


@mock.patch("sharepoint_rest_api.serializers.sharepoint.reverse")
def test_settings_serializer_no_dot(mock_reverse):
    mock_reverse.return_value = "/path"
    serializer = SharePointSettingsSerializer(context={"folder": "docs"})
    serializer.instance = {"FileLeafRef": "report", "Title": "Report"}
    url = serializer.get_download_url(serializer.instance)
    assert f"{django_settings.HOST}/path" == url


# ---- sharepoint.py: SharePointUrlSerializer.get_download_url ----


@mock.patch("sharepoint_rest_api.serializers.sharepoint.reverse")
def test_url_serializer_empty_filename(mock_reverse):
    mock_reverse.return_value = "/path"
    serializer = SharePointUrlSerializer(context={"tenant": "t", "site": "s", "folder": "docs"})
    serializer.instance = {"FileLeafRef": "", "Title": ""}
    url = serializer.get_download_url(serializer.instance)
    assert f"{django_settings.HOST}/path" == url


@mock.patch("sharepoint_rest_api.serializers.sharepoint.reverse")
def test_url_serializer_no_dot(mock_reverse):
    mock_reverse.return_value = "/path"
    serializer = SharePointUrlSerializer(context={"tenant": "t", "site": "s", "folder": "docs"})
    serializer.instance = {"FileLeafRef": "report", "Title": "Report"}
    url = serializer.get_download_url(serializer.instance)
    assert f"{django_settings.HOST}/path" == url


# ---- sharepoint.py: SharePointFileSerializer.get_download_url ----


@mock.patch("sharepoint_rest_api.serializers.sharepoint.reverse")
def test_file_serializer_download_url(mock_reverse):
    mock_reverse.return_value = "/path"
    serializer = SharePointFileSerializer(context={"tenant": "t", "site": "s", "folder": "docs"})
    serializer.instance = {"Name": "report.pdf"}
    url = serializer.get_download_url(serializer.instance)
    assert f"{django_settings.HOST}/path" == url


# ---- sharepoint.py: SharePointSearchSerializer.get_download_url error path ----


def test_search_serializer_download_url_key_error():
    serializer = SharePointSearchSerializer()
    result = serializer.get_download_url([{"Key": "Path"}])
    assert isinstance(result, str)
    assert result


@mock.patch("sharepoint_rest_api.serializers.sharepoint.reverse")
def test_search_serializer_download_url_success(mock_reverse):
    mock_reverse.return_value = "/path"
    serializer = SharePointSearchSerializer()
    result = serializer.get_download_url([{"Key": "Path", "Value": "/sites/docs/report.pdf"}])
    assert isinstance(result, str)
    assert mock_reverse.called
