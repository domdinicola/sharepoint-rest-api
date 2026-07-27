from datetime import datetime, timezone
from unittest import mock

import pytest
import requests

from sharepoint_rest_api.builders.rest_builder import RestBuilder
from sharepoint_rest_api.graph_client import (
    GraphClient,
    GraphClientError,
    GRAPH_URL,
    _parse_last_modified,
)


# ---- __init__ ----------------------------------------------------------------


def test_defaults():
    client = GraphClient()
    assert client._client_id == "invalid_graph_client_id"
    assert client._client_secret == "invalid_graph_client_secret"
    assert client._tenant == ""
    assert client._app is None
    assert client._token is None
    assert client._site_id is None
    assert client.folder == "Documents"


def test_custom_values():
    client = GraphClient(
        client_id="my-id",
        client_secret="my-secret",
        tenant="my-tenant.onmicrosoft.com",
        folder="MyFolder",
    )
    assert client._client_id == "my-id"
    assert client._client_secret == "my-secret"
    assert client._tenant == "my-tenant.onmicrosoft.com"
    assert client.folder == "MyFolder"


# ---- _msal_app ---------------------------------------------------------------


@mock.patch("sharepoint_rest_api.graph_client.ConfidentialClientApplication")
def test_msal_app_lazy_creation(mock_cca):
    client = GraphClient()
    assert client._app is None
    app = client._msal_app
    mock_cca.assert_called_once_with(
        client_id="invalid_graph_client_id",
        client_credential="invalid_graph_client_secret",
        authority="https://login.microsoftonline.com/",
    )
    assert app == mock_cca.return_value


@mock.patch("sharepoint_rest_api.graph_client.ConfidentialClientApplication")
def test_msal_app_caches(mock_cca):
    client = GraphClient()
    app1 = client._msal_app
    app2 = client._msal_app
    assert app1 is app2
    mock_cca.assert_called_once()


# ---- token -------------------------------------------------------------------


@mock.patch("sharepoint_rest_api.graph_client.ConfidentialClientApplication")
def test_token_acquires(mock_cca):
    mock_app = mock_cca.return_value
    mock_app.acquire_token_for_client.return_value = {"access_token": "test-token"}
    client = GraphClient()
    token = client.token
    assert token == "test-token"
    mock_app.acquire_token_for_client.assert_called_once_with(scopes=["https://graph.microsoft.com/.default"])


@mock.patch("sharepoint_rest_api.graph_client.ConfidentialClientApplication")
def test_token_caches(mock_cca):
    mock_app = mock_cca.return_value
    mock_app.acquire_token_for_client.return_value = {"access_token": "test-token"}
    client = GraphClient()
    token1 = client.token
    token2 = client.token
    assert token1 is token2
    mock_app.acquire_token_for_client.assert_called_once()


@mock.patch("sharepoint_rest_api.graph_client.ConfidentialClientApplication")
def test_token_raises_on_failure(mock_cca):
    mock_app = mock_cca.return_value
    mock_app.acquire_token_for_client.return_value = {
        "error": "invalid_client",
        "error_description": "Invalid client credentials",
    }
    client = GraphClient()
    with pytest.raises(GraphClientError, match="Could not acquire token: Invalid client credentials"):
        client.token


# ---- headers -----------------------------------------------------------------


@mock.patch("sharepoint_rest_api.graph_client.ConfidentialClientApplication")
def test_headers(mock_cca):
    mock_app = mock_cca.return_value
    mock_app.acquire_token_for_client.return_value = {"access_token": "test-token"}
    client = GraphClient()
    headers = client.headers
    assert headers["Authorization"] == "Bearer test-token"
    assert headers["Content-Type"] == "application/json"


# ---- get ---------------------------------------------------------------------


@mock.patch("sharepoint_rest_api.graph_client.requests.get")
@mock.patch("sharepoint_rest_api.graph_client.ConfidentialClientApplication")
def test_get_success(mock_cca, mock_get):
    mock_app = mock_cca.return_value
    mock_app.acquire_token_for_client.return_value = {"access_token": "t"}
    mock_response = mock.MagicMock()
    mock_get.return_value = mock_response

    client = GraphClient()
    response = client.get("https://graph.microsoft.com/v1.0/sites/root", timeout=30)

    assert response == mock_response
    mock_get.assert_called_once_with(
        "https://graph.microsoft.com/v1.0/sites/root",
        headers={"Authorization": "Bearer t", "Content-Type": "application/json"},
        timeout=30,
    )


@mock.patch("sharepoint_rest_api.graph_client.requests.get")
@mock.patch("sharepoint_rest_api.graph_client.ConfidentialClientApplication")
def test_get_http_error(mock_cca, mock_get):
    mock_app = mock_cca.return_value
    mock_app.acquire_token_for_client.return_value = {"access_token": "t"}
    mock_get.return_value = mock.MagicMock()
    mock_get.return_value.raise_for_status.side_effect = requests.exceptions.HTTPError("403")

    client = GraphClient()
    with pytest.raises(GraphClientError, match="Graph GET request failed"):
        client.get("https://graph.microsoft.com/v1.0/sites/root")


# ---- post --------------------------------------------------------------------


@mock.patch("sharepoint_rest_api.graph_client.requests.post")
@mock.patch("sharepoint_rest_api.graph_client.ConfidentialClientApplication")
def test_post_success(mock_cca, mock_post):
    mock_app = mock_cca.return_value
    mock_app.acquire_token_for_client.return_value = {"access_token": "t"}
    mock_response = mock.MagicMock()
    mock_post.return_value = mock_response

    client = GraphClient()
    response = client.post("https://graph.microsoft.com/v1.0/search/query", json={"query": "test"}, timeout=60)

    assert response == mock_response
    mock_post.assert_called_once_with(
        "https://graph.microsoft.com/v1.0/search/query",
        headers={"Authorization": "Bearer t", "Content-Type": "application/json"},
        json={"query": "test"},
        timeout=60,
    )


@mock.patch("sharepoint_rest_api.graph_client.requests.post")
@mock.patch("sharepoint_rest_api.graph_client.ConfidentialClientApplication")
def test_post_http_error(mock_cca, mock_post):
    mock_app = mock_cca.return_value
    mock_app.acquire_token_for_client.return_value = {"access_token": "t"}
    mock_post.side_effect = requests.exceptions.RequestException("API down")

    client = GraphClient()
    with pytest.raises(GraphClientError, match="Graph POST request failed"):
        client.post("https://graph.microsoft.com/v1.0/search/query", json={"query": "test"})


# ---- get / post retries on 504 ----------------------------------------------------------------


@mock.patch("sharepoint_rest_api.graph_client.requests.get")
@mock.patch("sharepoint_rest_api.graph_client.ConfidentialClientApplication")
def test_get_retries_on_504_then_succeeds(mock_cca, mock_get):
    mock_app = mock_cca.return_value
    mock_app.acquire_token_for_client.return_value = {"access_token": "t"}
    mock_response_504 = mock.MagicMock()
    mock_response_504.status_code = 504
    mock_response_200 = mock.MagicMock()
    mock_response_200.status_code = 200
    mock_get.side_effect = [mock_response_504, mock_response_200]

    client = GraphClient()
    response = client.get("https://graph.microsoft.com/v1.0/sites/root")

    assert response == mock_response_200
    assert mock_get.call_count == 2


@mock.patch("sharepoint_rest_api.graph_client.requests.get")
@mock.patch("sharepoint_rest_api.graph_client.ConfidentialClientApplication")
def test_get_retries_on_504_then_fails(mock_cca, mock_get):
    mock_app = mock_cca.return_value
    mock_app.acquire_token_for_client.return_value = {"access_token": "t"}
    mock_response_504 = mock.MagicMock()
    mock_response_504.status_code = 504
    mock_response_504.raise_for_status.side_effect = requests.exceptions.HTTPError("504")
    mock_get.return_value = mock_response_504

    client = GraphClient()
    with pytest.raises(GraphClientError, match="Graph GET request failed"):
        client.get("https://graph.microsoft.com/v1.0/sites/root")

    assert mock_get.call_count == 2  # default retries = 1


@mock.patch("sharepoint_rest_api.graph_client.requests.get")
@mock.patch("sharepoint_rest_api.graph_client.ConfidentialClientApplication")
def test_get_does_not_retry_on_non_504(mock_cca, mock_get):
    mock_app = mock_cca.return_value
    mock_app.acquire_token_for_client.return_value = {"access_token": "t"}
    mock_response_500 = mock.MagicMock()
    mock_response_500.status_code = 500
    mock_response_500.raise_for_status.side_effect = requests.exceptions.HTTPError("500")
    mock_get.return_value = mock_response_500

    client = GraphClient()
    with pytest.raises(GraphClientError, match="Graph GET request failed"):
        client.get("https://graph.microsoft.com/v1.0/sites/root")

    assert mock_get.call_count == 1


@mock.patch("sharepoint_rest_api.graph_client.requests.get")
@mock.patch("sharepoint_rest_api.graph_client.ConfidentialClientApplication")
def test_get_uses_configurable_retry_count(mock_cca, mock_get):
    mock_app = mock_cca.return_value
    mock_app.acquire_token_for_client.return_value = {"access_token": "t"}
    mock_response_504 = mock.MagicMock()
    mock_response_504.status_code = 504
    mock_response_504.raise_for_status.side_effect = requests.exceptions.HTTPError("504")
    mock_get.return_value = mock_response_504

    client = GraphClient()
    with mock.patch("sharepoint_rest_api.graph_client.config.GRAPH_API_RETRY_COUNT", 3):
        with pytest.raises(GraphClientError, match="Graph GET request failed"):
            client.get("https://graph.microsoft.com/v1.0/sites/root")

    assert mock_get.call_count == 4  # initial + 3 retries


@mock.patch("sharepoint_rest_api.graph_client.requests.post")
@mock.patch("sharepoint_rest_api.graph_client.ConfidentialClientApplication")
def test_post_retries_on_504_then_succeeds(mock_cca, mock_post):
    mock_app = mock_cca.return_value
    mock_app.acquire_token_for_client.return_value = {"access_token": "t"}
    mock_response_504 = mock.MagicMock()
    mock_response_504.status_code = 504
    mock_response_200 = mock.MagicMock()
    mock_response_200.status_code = 200
    mock_post.side_effect = [mock_response_504, mock_response_200]

    client = GraphClient()
    response = client.post("https://graph.microsoft.com/v1.0/search/query", json={"query": "test"})

    assert response == mock_response_200
    assert mock_post.call_count == 2


@mock.patch("sharepoint_rest_api.graph_client.requests.post")
@mock.patch("sharepoint_rest_api.graph_client.ConfidentialClientApplication")
def test_post_retries_on_504_then_fails(mock_cca, mock_post):
    mock_app = mock_cca.return_value
    mock_app.acquire_token_for_client.return_value = {"access_token": "t"}
    mock_response_504 = mock.MagicMock()
    mock_response_504.status_code = 504
    mock_response_504.raise_for_status.side_effect = requests.exceptions.HTTPError("504")
    mock_post.return_value = mock_response_504

    client = GraphClient()
    with pytest.raises(GraphClientError, match="Graph POST request failed"):
        client.post("https://graph.microsoft.com/v1.0/search/query", json={"query": "test"})

    assert mock_post.call_count == 2


@mock.patch("sharepoint_rest_api.graph_client.requests.post")
@mock.patch("sharepoint_rest_api.graph_client.ConfidentialClientApplication")
def test_post_does_not_retry_on_non_504(mock_cca, mock_post):
    mock_app = mock_cca.return_value
    mock_app.acquire_token_for_client.return_value = {"access_token": "t"}
    mock_response_400 = mock.MagicMock()
    mock_response_400.status_code = 400
    mock_response_400.raise_for_status.side_effect = requests.exceptions.HTTPError("400")
    mock_post.return_value = mock_response_400

    client = GraphClient()
    with pytest.raises(GraphClientError, match="Graph POST request failed"):
        client.post("https://graph.microsoft.com/v1.0/search/query", json={"query": "test"})

    assert mock_post.call_count == 1


# ---- _get_site_id / site_id ---------------------------------------------------


@mock.patch("sharepoint_rest_api.graph_client.requests.get")
@mock.patch("sharepoint_rest_api.graph_client.ConfidentialClientApplication")
def test_get_site_id_success(mock_cca, mock_get):
    mock_app = mock_cca.return_value
    mock_app.acquire_token_for_client.return_value = {"access_token": "t"}
    mock_response = mock.MagicMock()
    mock_response.json.return_value = {"id": "site123"}
    mock_get.return_value = mock_response

    client = GraphClient()
    site_id = client._get_site_id()

    assert site_id == "site123"
    mock_get.assert_called_once()
    args, kwargs = mock_get.call_args
    assert args[0] == "https://graph.microsoft.com/v1.0/sites/unitst.sharepoint.com:/sites/GLB-DRP"
    assert kwargs["timeout"] == 120
    assert "Authorization" in kwargs.get("headers", {})


@mock.patch("sharepoint_rest_api.graph_client.requests.get")
@mock.patch("sharepoint_rest_api.graph_client.ConfidentialClientApplication")
def test_get_site_id_http_error(mock_cca, mock_get):
    mock_app = mock_cca.return_value
    mock_app.acquire_token_for_client.return_value = {"access_token": "t"}
    mock_get.return_value = mock.MagicMock()
    mock_get.return_value.raise_for_status.side_effect = requests.exceptions.HTTPError("403")

    client = GraphClient()
    with pytest.raises(GraphClientError):
        client._get_site_id()


@mock.patch("sharepoint_rest_api.graph_client.ConfidentialClientApplication")
def test_site_id_property_caches(mock_cca):
    mock_app = mock_cca.return_value
    mock_app.acquire_token_for_client.return_value = {"access_token": "t"}
    client = GraphClient()
    with mock.patch.object(GraphClient, "_get_site_id", return_value="site123") as mock_get:
        sid1 = client.site_id
        sid2 = client.site_id
        assert sid1 == sid2 == "site123"
        mock_get.assert_called_once()


@mock.patch("sharepoint_rest_api.graph_client.requests.get")
@mock.patch("sharepoint_rest_api.graph_client.ConfidentialClientApplication")
def test_get_site_id_cache_hit(mock_cca, mock_get):
    mock_app = mock_cca.return_value
    mock_app.acquire_token_for_client.return_value = {"access_token": "t"}
    mock_resp = mock.MagicMock()
    mock_resp.json.return_value = {"id": "cached-site-id"}
    mock_get.return_value = mock_resp

    client = GraphClient()
    result1 = client._get_site_id()
    assert result1 == "cached-site-id"
    assert mock_get.call_count == 1

    result2 = client._get_site_id()
    assert result2 == "cached-site-id"
    assert mock_get.call_count == 1


# ---- build_kql (delegates to RestBuilder) ------------------------------------


def test_kql_no_filters_no_search():
    assert RestBuilder.build_kql() == "*"


def test_kql_no_filters_with_search():
    assert RestBuilder.build_kql(search="path:/documents") == "path:/documents"


def test_kql_eq_filter_single():
    result = RestBuilder.build_kql(filters={"Donor": "Red Cross"})
    assert result == 'Donor:"Red Cross"'


def test_kql_eq_filter_multi_value():
    result = RestBuilder.build_kql(filters={"Donor": "Red Cross,UNICEF"})
    assert result == 'Donor:("Red Cross" OR "UNICEF")'


def test_kql_not_filter():
    result = RestBuilder.build_kql(filters={"Donor__not": "Red Cross"})
    assert result == '-Donor:"Red Cross"'


def test_kql_contains_filter():
    result = RestBuilder.build_kql(filters={"Donor__contains": "Cross"})
    assert result == 'Donor:"Cross*"'


def test_kql_not_in_filter():
    result = RestBuilder.build_kql(filters={"Donor__not_in": "Red Cross,UNICEF"})
    assert result == '-"Red Cross" -"UNICEF"'


def test_kql_unknown_operator():
    result = RestBuilder.build_kql(filters={"Donor__unknown": "val"})
    assert result == 'Donor:"val"'


def test_kql_exclusion_filter():
    result = RestBuilder.build_kql(filters={"-Donor": "Red Cross"})
    assert result == '-Donor:"Red Cross"'


def test_kql_search_with_filters():
    result = RestBuilder.build_kql(search="path:/docs", filters={"Donor": "Red Cross"})
    assert result == 'path:/docs Donor:"Red Cross"'


def test_kql_multiple_filters():
    result = RestBuilder.build_kql(filters={"Donor": "Red Cross", "ReportStatus": "Final"})
    assert 'Donor:"Red Cross"' in result
    assert 'ReportStatus:"Final"' in result
    assert " AND " not in result


def test_kql_gte():
    result = RestBuilder.build_kql(filters={"Size__gte": "1000"})
    assert result == "Size>=1000"


# ---- _matches_post_filters ---------------------------------------------------


def test_post_filter_eq_match():
    assert GraphClient._matches_post_filters({"Donor": "Red Cross"}, {"Donor": "Red Cross"})


def test_post_filter_eq_no_match():
    assert not GraphClient._matches_post_filters({"Donor": "UNICEF"}, {"Donor": "Red Cross"})


def test_post_filter_eq_multi_value_or():
    assert GraphClient._matches_post_filters({"Donor": "UNICEF"}, {"Donor": "Red Cross,UNICEF"})


def test_post_filter_not_match():
    assert GraphClient._matches_post_filters({"Donor": "UNICEF"}, {"Donor__not": "Red Cross"})


def test_post_filter_not_no_match():
    assert not GraphClient._matches_post_filters({"Donor": "Red Cross"}, {"Donor__not": "Red Cross"})


def test_post_filter_not_multi_value():
    assert not GraphClient._matches_post_filters({"Donor": "Red Cross"}, {"Donor__not": "Red Cross,UNICEF"})


def test_post_filter_contains_match():
    assert GraphClient._matches_post_filters({"Donor": "Red Cross"}, {"Donor__contains": "Cross"})


def test_post_filter_contains_no_match():
    assert not GraphClient._matches_post_filters({"Donor": "Red Cross"}, {"Donor__contains": "Blue"})


def test_post_filter_contains_multi_value():
    assert GraphClient._matches_post_filters({"Donor": "Red Cross Org"}, {"Donor__contains": "Blue,Cross"})


def test_post_filter_not_in_match():
    assert GraphClient._matches_post_filters({"Donor": "UNICEF"}, {"Donor__not_in": "Red Cross,WHO"})


def test_post_filter_not_in_no_match():
    assert not GraphClient._matches_post_filters({"Donor": "Red Cross"}, {"Donor__not_in": "Red Cross,UNICEF"})


def test_post_filter_not_in_no_match_multi():
    assert not GraphClient._matches_post_filters({"Donor": "UNICEF"}, {"Donor__not_in": "Red Cross,UNICEF"})


def test_post_filter_exclusion_match():
    assert GraphClient._matches_post_filters({"Donor": "UNICEF"}, {"-Donor": "Red Cross"})


def test_post_filter_exclusion_no_match():
    assert not GraphClient._matches_post_filters({"Donor": "Red Cross"}, {"-Donor": "Red Cross"})


def test_post_filter_exclusion_multi_value():
    assert not GraphClient._matches_post_filters({"Donor": "Red Cross"}, {"-Donor": "UNICEF,Red Cross"})


def test_post_filter_absent_field_not():
    assert GraphClient._matches_post_filters({}, {"Donor__not": "Red Cross"})


def test_post_filter_absent_field_eq():
    assert not GraphClient._matches_post_filters({}, {"Donor": "Red Cross"})


def test_post_filter_absent_field_exclusion():
    assert GraphClient._matches_post_filters({}, {"-Donor": "Red Cross"})


def test_post_filter_semicolons_in_item():
    assert GraphClient._matches_post_filters({"Donor": "Red Cross;UNICEF"}, {"Donor": "UNICEF"})
    assert GraphClient._matches_post_filters({"Donor": "Red Cross;UNICEF"}, {"Donor": "Red Cross"})
    assert not GraphClient._matches_post_filters({"Donor": "Red Cross;UNICEF"}, {"Donor": "WHO"})


def test_post_filter_reverse_map():
    reverse_map = {"DonorCode": "DRPDonorCode"}
    assert GraphClient._matches_post_filters({"DRPDonorCode": "123"}, {"DonorCode": "123"}, reverse_map=reverse_map)
    assert not GraphClient._matches_post_filters({"DRPDonorCode": "456"}, {"DonorCode": "123"}, reverse_map=reverse_map)


def test_post_filter_reverse_map_prefers_original():
    reverse_map = {"DonorCode": "DRPDonorCode"}
    assert GraphClient._matches_post_filters(
        {"DonorCode": "123", "DRPDonorCode": "456"},
        {"DonorCode": "123"},
        reverse_map=reverse_map,
    )


def test_post_filter_unknown_operator_falls_through():
    assert GraphClient._matches_post_filters({"Donor": "Red Cross"}, {"Donor__unknown_op": "Red Cross"})


def test_post_filter_no_matching_elif_returns_true():
    assert GraphClient._matches_post_filters({"Donor": "Red Cross"}, {"Donor__weird": "Red Cross"})


# ---- _fetch_item_fields -------------------------------------------------------


@mock.patch("sharepoint_rest_api.graph_client.requests.post")
@mock.patch("sharepoint_rest_api.graph_client.ConfidentialClientApplication")
def test_fetch_item_fields_empty(mock_cca, mock_post):
    mock_app = mock_cca.return_value
    mock_app.acquire_token_for_client.return_value = {"access_token": "t"}
    client = GraphClient()
    client._fetch_item_fields([])
    mock_post.assert_not_called()


@mock.patch("sharepoint_rest_api.graph_client.requests.post")
@mock.patch("sharepoint_rest_api.graph_client.ConfidentialClientApplication")
def test_fetch_item_fields_quote_failure_skips(mock_cca, mock_post):
    mock_app = mock_cca.return_value
    mock_app.acquire_token_for_client.return_value = {"access_token": "t"}
    client = GraphClient()
    with mock.patch("sharepoint_rest_api.graph_client.quote", side_effect=TypeError("encoding error")):
        items_with_refs = [
            ({"Title": "doc1"}, "bad|site", "list1", "item1"),
            ({"Title": "doc2"}, "site2", "list2", "item2"),
        ]
        client._fetch_item_fields(items_with_refs)
    mock_post.assert_not_called()


@mock.patch("sharepoint_rest_api.graph_client.requests.post")
@mock.patch("sharepoint_rest_api.graph_client.ConfidentialClientApplication")
def test_fetch_item_fields_skips_incomplete(mock_cca, mock_post):
    mock_app = mock_cca.return_value
    mock_app.acquire_token_for_client.return_value = {"access_token": "t"}
    client = GraphClient()
    items_with_refs = [
        ({"Title": "doc1"}, None, "list1", "item1"),
        ({"Title": "doc2"}, "site2", None, "item2"),
        ({"Title": "doc3"}, "site3", "list3", None),
    ]
    client._fetch_item_fields(items_with_refs)
    mock_post.assert_not_called()


@mock.patch("sharepoint_rest_api.graph_client.requests.post")
@mock.patch("sharepoint_rest_api.graph_client.ConfidentialClientApplication")
def test_fetch_item_fields_success(mock_cca, mock_post):
    mock_app = mock_cca.return_value
    mock_app.acquire_token_for_client.return_value = {"access_token": "t"}
    mock_resp = mock.MagicMock()
    mock_resp.json.return_value = {
        "responses": [
            {
                "id": "0",
                "status": 200,
                "body": {"fields": {"ReportStatus": "Final", "ExtraField": "val"}},
            }
        ]
    }
    mock_post.return_value = mock_resp

    client = GraphClient()
    item = {"Title": "doc1"}
    items_with_refs = [(item, "site1", "list1", "item1")]
    client._fetch_item_fields(items_with_refs)

    assert item["ReportStatus"] == "Final"
    assert item["ExtraField"] == "val"
    mock_post.assert_called_once()
    url = mock_post.call_args[0][0]
    assert url == f"{GRAPH_URL}/$batch"


@mock.patch("sharepoint_rest_api.graph_client.requests.post")
@mock.patch("sharepoint_rest_api.graph_client.ConfidentialClientApplication")
def test_fetch_item_fields_http_error(mock_cca, mock_post):
    mock_app = mock_cca.return_value
    mock_app.acquire_token_for_client.return_value = {"access_token": "t"}
    mock_post.side_effect = requests.exceptions.RequestException("timeout")

    client = GraphClient()
    item = {"Title": "doc1"}
    items_with_refs = [(item, "site1", "list1", "item1")]
    client._fetch_item_fields(items_with_refs)
    assert "ReportStatus" not in item


@mock.patch("sharepoint_rest_api.graph_client.requests.post")
@mock.patch("sharepoint_rest_api.graph_client.ConfidentialClientApplication")
def test_fetch_item_fields_respects_limit(mock_cca, mock_post):
    mock_app = mock_cca.return_value
    mock_app.acquire_token_for_client.return_value = {"access_token": "t"}
    mock_resp = mock.MagicMock()
    mock_resp.json.return_value = {"responses": []}
    mock_post.return_value = mock_resp

    client = GraphClient()
    items_with_refs = [({"Title": f"doc{i}"}, "site1", "list1", f"item{i}") for i in range(30)]
    client._fetch_item_fields(items_with_refs)

    assert mock_post.call_count == 2
    first_body = mock_post.call_args_list[0][1]["json"]
    assert len(first_body["requests"]) == 20
    second_body = mock_post.call_args_list[1][1]["json"]
    assert len(second_body["requests"]) == 10


@mock.patch("sharepoint_rest_api.graph_client.requests.post")
@mock.patch("sharepoint_rest_api.graph_client.ConfidentialClientApplication")
def test_fetch_item_fields_non_200(mock_cca, mock_post):
    mock_app = mock_cca.return_value
    mock_app.acquire_token_for_client.return_value = {"access_token": "t"}
    mock_resp = mock.MagicMock()
    mock_resp.json.return_value = {"responses": [{"id": "0", "status": 404, "body": {}}]}
    mock_post.return_value = mock_resp

    client = GraphClient()
    item = {"Title": "doc1"}
    items_with_refs = [(item, "site1", "list1", "item1")]
    client._fetch_item_fields(items_with_refs)
    assert "ReportStatus" not in item


@mock.patch("sharepoint_rest_api.graph_client.requests.post")
@mock.patch("sharepoint_rest_api.graph_client.ConfidentialClientApplication")
def test_fetch_item_fields_invalid_body(mock_cca, mock_post):
    mock_app = mock_cca.return_value
    mock_app.acquire_token_for_client.return_value = {"access_token": "t"}
    mock_resp = mock.MagicMock()
    mock_resp.json.return_value = {
        "responses": [
            {"id": "0", "status": 200, "body": None},
            {"id": "1", "status": 200, "body": {"fields": None}},
            {"id": "2", "status": 200, "body": {"fields": {"Key": "val"}}},
        ]
    }
    mock_post.return_value = mock_resp

    client = GraphClient()
    items_with_refs = [
        ({"Title": "doc1"}, "site1", "list1", "item1"),
        ({"Title": "doc2"}, "site1", "list1", "item2"),
        ({"Title": "doc3"}, "site1", "list1", "item3"),
    ]
    client._fetch_item_fields(items_with_refs)
    assert items_with_refs[2][0].get("Key") == "val"


@mock.patch("sharepoint_rest_api.graph_client.requests.post")
@mock.patch("sharepoint_rest_api.graph_client.ConfidentialClientApplication")
def test_fetch_item_fields_invalid_index(mock_cca, mock_post):
    mock_app = mock_cca.return_value
    mock_app.acquire_token_for_client.return_value = {"access_token": "t"}
    mock_resp = mock.MagicMock()
    mock_resp.json.return_value = {
        "responses": [
            {"id": "invalid", "status": 200, "body": {"fields": {"X": "y"}}},
            {"id": "99", "status": 200, "body": {"fields": {"X": "y"}}},
        ]
    }
    mock_post.return_value = mock_resp

    client = GraphClient()
    items_with_refs = [({"Title": "doc1"}, "site1", "list1", "item1")]
    client._fetch_item_fields(items_with_refs)
    assert "X" not in items_with_refs[0][0]


@mock.patch("sharepoint_rest_api.graph_client.requests.post")
@mock.patch("sharepoint_rest_api.graph_client.ConfidentialClientApplication")
def test_fetch_item_fields_existing_key_not_overwritten(mock_cca, mock_post):
    mock_app = mock_cca.return_value
    mock_app.acquire_token_for_client.return_value = {"access_token": "t"}
    mock_resp = mock.MagicMock()
    mock_resp.json.return_value = {
        "responses": [
            {"id": "0", "status": 200, "body": {"fields": {"Title": "new_title", "Extra": "val"}}},
        ]
    }
    mock_post.return_value = mock_resp

    client = GraphClient()
    item = {"Title": "original_title"}
    items_with_refs = [(item, "site1", "list1", "item1")]
    client._fetch_item_fields(items_with_refs)
    assert item["Title"] == "original_title"
    assert item["Extra"] == "val"


# ---- _execute_search_page -----------------------------------------------------


@mock.patch("sharepoint_rest_api.graph_client.requests.post")
@mock.patch("sharepoint_rest_api.graph_client.ConfidentialClientApplication")
def test_execute_search_page_no_results(mock_cca, mock_post):
    mock_app = mock_cca.return_value
    mock_app.acquire_token_for_client.return_value = {"access_token": "t"}
    mock_resp = mock.MagicMock()
    mock_resp.json.return_value = {"value": [{"hitsContainers": [{"total": 0, "hits": []}]}]}
    mock_post.return_value = mock_resp

    client = GraphClient()
    items, total = client._execute_search_page("*", 0, 25)
    assert items == []
    assert total == 0


@mock.patch("sharepoint_rest_api.graph_client.requests.post")
@mock.patch("sharepoint_rest_api.graph_client.ConfidentialClientApplication")
def test_execute_search_page_with_hits(mock_cca, mock_post):
    mock_app = mock_cca.return_value
    mock_app.acquire_token_for_client.return_value = {"access_token": "t"}
    mock_resp = mock.MagicMock()
    mock_resp.json.return_value = {
        "value": [
            {
                "hitsContainers": [
                    {
                        "total": 2,
                        "hits": [
                            {
                                "hitId": "hit1",
                                "rank": 1,
                                "resource": {
                                    "id": "doc1",
                                    "name": "Report1.pdf",
                                    "webUrl": "https://sharepoint.com/site/doc1",
                                    "size": 1024,
                                    "lastModifiedDateTime": "2024-01-01T00:00:00Z",
                                    "file": {"mimeType": "application/pdf"},
                                    "createdBy": {"user": {"displayName": "John Doe"}},
                                    "parentReference": {
                                        "siteId": "site1",
                                        "sharepointIds": {"listId": "list1", "listItemId": "item1"},
                                    },
                                },
                            },
                            {
                                "hitId": "hit2",
                                "rank": 2,
                                "resource": {
                                    "id": "doc2",
                                    "webUrl": "https://sharepoint.com/site/doc2",
                                    "size": 2048,
                                    "lastModifiedDateTime": "2024-02-01T00:00:00Z",
                                    "parentReference": {},
                                },
                            },
                        ],
                    }
                ]
            }
        ]
    }
    mock_post.return_value = mock_resp

    client = GraphClient()
    items, total = client._execute_search_page("*", 0, 25)

    assert total == 2
    assert len(items) == 2

    assert items[0]["Title"] == "Report1.pdf"
    assert items[0]["Path"] == "https://sharepoint.com/site/doc1"
    assert items[0]["DocId"] == "doc1"
    assert items[0]["WorkId"] == "hit1"
    assert items[0]["Rank"] == 1
    assert items[0]["Size"] == 1024
    assert items[0]["FileType"] == "pdf"
    assert items[0]["Author"] == "John Doe"
    assert items[0]["SiteId"] == "site1"
    assert items[0]["DriveId"] == ""

    assert items[1]["Title"] == "doc2"
    assert items[1]["Path"] == "https://sharepoint.com/site/doc2"
    assert "FileType" not in items[1]
    assert "Author" not in items[1]
    assert items[1]["SiteId"] == ""
    assert items[1]["DriveId"] == ""


@mock.patch("sharepoint_rest_api.graph_client.requests.post")
@mock.patch("sharepoint_rest_api.graph_client.ConfidentialClientApplication")
def test_execute_search_page_created_by_user_not_dict(mock_cca, mock_post):
    mock_app = mock_cca.return_value
    mock_app.acquire_token_for_client.return_value = {"access_token": "t"}
    mock_resp = mock.MagicMock()
    mock_resp.json.return_value = {
        "value": [
            {
                "hitsContainers": [
                    {
                        "total": 1,
                        "hits": [
                            {
                                "hitId": "hit1",
                                "rank": 1,
                                "resource": {
                                    "id": "doc1",
                                    "name": "doc.pdf",
                                    "webUrl": "https://sharepoint.com/site/doc1",
                                    "size": 512,
                                    "lastModifiedDateTime": "2024-01-01T00:00:00Z",
                                    "createdBy": {"user": "not_a_dict"},
                                },
                            }
                        ],
                    }
                ]
            }
        ]
    }
    mock_post.return_value = mock_resp

    client = GraphClient()
    items, total = client._execute_search_page("*", 0, 25)
    assert "Author" not in items[0]


@mock.patch("sharepoint_rest_api.graph_client.requests.post")
@mock.patch("sharepoint_rest_api.graph_client.ConfidentialClientApplication")
def test_execute_search_page_created_by_user_no_display_name(mock_cca, mock_post):
    mock_app = mock_cca.return_value
    mock_app.acquire_token_for_client.return_value = {"access_token": "t"}
    mock_resp = mock.MagicMock()
    mock_resp.json.return_value = {
        "value": [
            {
                "hitsContainers": [
                    {
                        "total": 1,
                        "hits": [
                            {
                                "hitId": "hit1",
                                "rank": 1,
                                "resource": {
                                    "id": "doc1",
                                    "name": "doc.pdf",
                                    "webUrl": "https://sharepoint.com/site/doc1",
                                    "size": 512,
                                    "lastModifiedDateTime": "2024-01-01T00:00:00Z",
                                    "createdBy": {"user": {"displayName": ""}},
                                },
                            }
                        ],
                    }
                ]
            }
        ]
    }
    mock_post.return_value = mock_resp

    client = GraphClient()
    items, total = client._execute_search_page("*", 0, 25)
    assert "Author" not in items[0]


@mock.patch("sharepoint_rest_api.graph_client.requests.post")
@mock.patch("sharepoint_rest_api.graph_client.ConfidentialClientApplication")
def test_execute_search_page_created_by_not_dict(mock_cca, mock_post):
    mock_app = mock_cca.return_value
    mock_app.acquire_token_for_client.return_value = {"access_token": "t"}
    mock_resp = mock.MagicMock()
    mock_resp.json.return_value = {
        "value": [
            {
                "hitsContainers": [
                    {
                        "total": 1,
                        "hits": [
                            {
                                "hitId": "hit1",
                                "rank": 1,
                                "resource": {
                                    "id": "doc1",
                                    "name": "doc.pdf",
                                    "webUrl": "https://sharepoint.com/site/doc1",
                                    "size": 512,
                                    "lastModifiedDateTime": "2024-01-01T00:00:00Z",
                                    "createdBy": "not_a_dict",
                                },
                            }
                        ],
                    }
                ]
            }
        ]
    }
    mock_post.return_value = mock_resp

    client = GraphClient()
    items, total = client._execute_search_page("*", 0, 25)
    assert "Author" not in items[0]


@mock.patch("sharepoint_rest_api.graph_client.requests.post")
@mock.patch("sharepoint_rest_api.graph_client.ConfidentialClientApplication")
def test_execute_search_page_list_item_not_dict(mock_cca, mock_post):
    mock_app = mock_cca.return_value
    mock_app.acquire_token_for_client.return_value = {"access_token": "t"}
    mock_resp = mock.MagicMock()
    mock_resp.json.return_value = {
        "value": [
            {
                "hitsContainers": [
                    {
                        "total": 1,
                        "hits": [
                            {
                                "hitId": "hit1",
                                "rank": 1,
                                "resource": {
                                    "id": "doc1",
                                    "name": "doc.pdf",
                                    "webUrl": "https://sharepoint.com/site/doc1",
                                    "size": 512,
                                    "lastModifiedDateTime": "2024-01-01T00:00:00Z",
                                    "listItem": "not_a_dict",
                                },
                            }
                        ],
                    }
                ]
            }
        ]
    }
    mock_post.return_value = mock_resp

    client = GraphClient()
    items, total = client._execute_search_page("*", 0, 25)
    assert "OriginalPath" not in items[0]


@mock.patch("sharepoint_rest_api.graph_client.requests.post")
@mock.patch("sharepoint_rest_api.graph_client.ConfidentialClientApplication")
def test_execute_search_page_list_item_fields_not_dict(mock_cca, mock_post):
    mock_app = mock_cca.return_value
    mock_app.acquire_token_for_client.return_value = {"access_token": "t"}
    mock_resp = mock.MagicMock()
    mock_resp.json.return_value = {
        "value": [
            {
                "hitsContainers": [
                    {
                        "total": 1,
                        "hits": [
                            {
                                "hitId": "hit1",
                                "rank": 1,
                                "resource": {
                                    "id": "doc1",
                                    "name": "doc.pdf",
                                    "webUrl": "https://sharepoint.com/site/doc1",
                                    "size": 512,
                                    "lastModifiedDateTime": "2024-01-01T00:00:00Z",
                                    "listItem": {"fields": "not_a_dict"},
                                },
                            }
                        ],
                    }
                ]
            }
        ]
    }
    mock_post.return_value = mock_resp

    client = GraphClient()
    items, total = client._execute_search_page("*", 0, 25)
    assert "OriginalPath" not in items[0]


@mock.patch("sharepoint_rest_api.graph_client.requests.post")
@mock.patch("sharepoint_rest_api.graph_client.ConfidentialClientApplication")
def test_execute_search_page_list_item_fields_overlap(mock_cca, mock_post):
    mock_app = mock_cca.return_value
    mock_app.acquire_token_for_client.return_value = {"access_token": "t"}
    mock_resp = mock.MagicMock()
    mock_resp.json.return_value = {
        "value": [
            {
                "hitsContainers": [
                    {
                        "total": 1,
                        "hits": [
                            {
                                "hitId": "hit1",
                                "rank": 1,
                                "resource": {
                                    "id": "doc1",
                                    "name": "Report.docx",
                                    "webUrl": "https://sharepoint.com/site/doc1",
                                    "size": 512,
                                    "lastModifiedDateTime": "2024-01-01T00:00:00Z",
                                    "listItem": {
                                        "fields": {
                                            "path": "/sites/site/doc1",
                                            "title": "Title from fields",
                                            "DocId": "overridden_doc_id",
                                            "Size": 9999,
                                        },
                                    },
                                    "parentReference": {
                                        "siteId": "site1",
                                        "sharepointIds": {"listId": "list1", "listItemId": "item1"},
                                    },
                                },
                            }
                        ],
                    }
                ]
            }
        ]
    }
    mock_post.return_value = mock_resp

    client = GraphClient()
    items, total = client._execute_search_page("*", 0, 25)

    assert items[0]["DocId"] == "doc1"
    assert items[0]["Size"] == 512


@mock.patch("sharepoint_rest_api.graph_client.requests.post")
@mock.patch("sharepoint_rest_api.graph_client.ConfidentialClientApplication")
def test_execute_search_page_name_from_web_url(mock_cca, mock_post):
    mock_app = mock_cca.return_value
    mock_app.acquire_token_for_client.return_value = {"access_token": "t"}
    mock_resp = mock.MagicMock()
    mock_resp.json.return_value = {
        "value": [
            {
                "hitsContainers": [
                    {
                        "total": 1,
                        "hits": [
                            {
                                "hitId": "hit1",
                                "rank": 1,
                                "resource": {
                                    "id": "doc1",
                                    "webUrl": "https://sharepoint.com/site/MyDoc.xlsx",
                                    "size": 512,
                                    "lastModifiedDateTime": "2024-01-01T00:00:00Z",
                                },
                            }
                        ],
                    }
                ]
            }
        ]
    }
    mock_post.return_value = mock_resp

    client = GraphClient()
    items, total = client._execute_search_page("*", 0, 25)
    assert items[0]["Title"] == "MyDoc.xlsx"


@mock.patch("sharepoint_rest_api.graph_client.requests.post")
@mock.patch("sharepoint_rest_api.graph_client.ConfidentialClientApplication")
def test_execute_search_page_list_item_fields(mock_cca, mock_post):
    mock_app = mock_cca.return_value
    mock_app.acquire_token_for_client.return_value = {"access_token": "t"}
    mock_resp = mock.MagicMock()
    mock_resp.json.return_value = {
        "value": [
            {
                "hitsContainers": [
                    {
                        "total": 1,
                        "hits": [
                            {
                                "hitId": "hit1",
                                "rank": 1,
                                "resource": {
                                    "id": "doc1",
                                    "name": "Report.docx",
                                    "webUrl": "https://sharepoint.com/site/doc1",
                                    "size": 512,
                                    "lastModifiedDateTime": "2024-01-01T00:00:00Z",
                                    "listItem": {
                                        "fields": {
                                            "path": "/sites/site/doc1",
                                            "title": "Custom Title",
                                            "Donor": "Red Cross",
                                        },
                                    },
                                    "parentReference": {
                                        "siteId": "site1",
                                        "sharepointIds": {"listId": "list1", "listItemId": "item1"},
                                    },
                                },
                            }
                        ],
                    }
                ]
            }
        ]
    }
    mock_post.return_value = mock_resp

    client = GraphClient()
    items, total = client._execute_search_page("*", 0, 25)

    assert items[0]["Title"] == "Custom Title"
    assert items[0]["OriginalPath"] == "/sites/site/doc1"
    assert items[0]["Donor"] == "Red Cross"


@mock.patch("sharepoint_rest_api.graph_client.requests.post")
@mock.patch("sharepoint_rest_api.graph_client.ConfidentialClientApplication")
def test_execute_search_page_summary(mock_cca, mock_post):
    mock_app = mock_cca.return_value
    mock_app.acquire_token_for_client.return_value = {"access_token": "t"}
    mock_resp = mock.MagicMock()
    mock_resp.json.return_value = {
        "value": [
            {
                "hitsContainers": [
                    {
                        "total": 1,
                        "hits": [
                            {
                                "hitId": "hit1",
                                "rank": 1,
                                "summary": "This is a <b>highlighted</b> summary",
                                "resource": {
                                    "id": "doc1",
                                    "name": "doc.pdf",
                                    "webUrl": "https://sharepoint.com/site/doc1",
                                    "size": 512,
                                    "lastModifiedDateTime": "2024-01-01T00:00:00Z",
                                },
                            }
                        ],
                    }
                ]
            }
        ]
    }
    mock_post.return_value = mock_resp

    client = GraphClient()
    items, total = client._execute_search_page("*", 0, 25)
    assert items[0]["HitHighlightedSummary"] == "This is a <b>highlighted</b> summary"


@mock.patch("sharepoint_rest_api.graph_client.requests.post")
@mock.patch("sharepoint_rest_api.graph_client.ConfidentialClientApplication")
def test_execute_search_page_http_error(mock_cca, mock_post):
    mock_app = mock_cca.return_value
    mock_app.acquire_token_for_client.return_value = {"access_token": "t"}
    mock_post.side_effect = requests.exceptions.RequestException("API down")

    client = GraphClient()
    with pytest.raises(GraphClientError, match="Graph Search API request failed"):
        client._execute_search_page("*", 0, 25)


@mock.patch("sharepoint_rest_api.graph_client.requests.post")
@mock.patch("sharepoint_rest_api.graph_client.ConfidentialClientApplication")
def test_execute_search_page_reverse_map(mock_cca, mock_post):
    mock_app = mock_cca.return_value
    mock_app.acquire_token_for_client.return_value = {"access_token": "t"}
    mock_resp = mock.MagicMock()
    mock_resp.json.return_value = {
        "value": [
            {
                "hitsContainers": [
                    {
                        "total": 1,
                        "hits": [
                            {
                                "hitId": "hit1",
                                "rank": 1,
                                "resource": {
                                    "id": "doc1",
                                    "name": "doc.docx",
                                    "webUrl": "https://sharepoint.com/site/doc1",
                                    "size": 512,
                                    "lastModifiedDateTime": "2024-01-01T00:00:00Z",
                                    "listItem": {
                                        "fields": {"DonorCode": "DC123"},
                                    },
                                },
                            }
                        ],
                    }
                ]
            }
        ]
    }
    mock_post.return_value = mock_resp

    client = GraphClient()
    items, total = client._execute_search_page("*", 0, 25, reverse_map={"DonorCode": "DRPDonorCode"})
    assert items[0]["DonorCode"] == "DC123"
    assert items[0]["DRPDonorCode"] == "DC123"


@mock.patch("sharepoint_rest_api.graph_client.requests.post")
@mock.patch("sharepoint_rest_api.graph_client.ConfidentialClientApplication")
def test_execute_search_page_reverse_map_no_overwrite(mock_cca, mock_post):
    mock_app = mock_cca.return_value
    mock_app.acquire_token_for_client.return_value = {"access_token": "t"}
    mock_resp = mock.MagicMock()
    mock_resp.json.return_value = {
        "value": [
            {
                "hitsContainers": [
                    {
                        "total": 1,
                        "hits": [
                            {
                                "hitId": "hit1",
                                "rank": 1,
                                "resource": {
                                    "id": "doc1",
                                    "name": "doc.docx",
                                    "webUrl": "https://sharepoint.com/site/doc1",
                                    "size": 512,
                                    "lastModifiedDateTime": "2024-01-01T00:00:00Z",
                                    "listItem": {
                                        "fields": {"DonorCode": "DC123", "DRPDonorCode": "existing"},
                                    },
                                },
                            }
                        ],
                    }
                ]
            }
        ]
    }
    mock_post.return_value = mock_resp

    client = GraphClient()
    items, total = client._execute_search_page("*", 0, 25, reverse_map={"DonorCode": "DRPDonorCode"})
    assert items[0]["DRPDonorCode"] == "existing"


@mock.patch("sharepoint_rest_api.graph_client.requests.post")
@mock.patch("sharepoint_rest_api.graph_client.ConfidentialClientApplication")
def test_execute_search_page_reverse_map_case_insensitive_fallback(mock_cca, mock_post):
    mock_app = mock_cca.return_value
    mock_app.acquire_token_for_client.return_value = {"access_token": "t"}
    mock_resp = mock.MagicMock()
    mock_resp.json.return_value = {
        "value": [
            {
                "hitsContainers": [
                    {
                        "total": 1,
                        "hits": [
                            {
                                "hitId": "hit1",
                                "rank": 1,
                                "resource": {
                                    "id": "doc1",
                                    "name": "doc.docx",
                                    "webUrl": "https://sharepoint.com/site/doc1",
                                    "size": 512,
                                    "lastModifiedDateTime": "2024-01-01T00:00:00Z",
                                    "Title": "already in item",
                                    "listItem": {
                                        "fields": {"donorcode": "DC123"},
                                    },
                                },
                            }
                        ],
                    }
                ]
            }
        ]
    }
    mock_post.return_value = mock_resp

    client = GraphClient()
    items, total = client._execute_search_page(
        "*",
        0,
        25,
        reverse_map={
            "DonorCode": "DRPDonorCode",
            "NonExistent": "DRPNonExistent",
        },
    )
    assert items[0]["DRPDonorCode"] == "DC123"
    assert "DRPNonExistent" not in items[0]


# ---- search -------------------------------------------------------------------


@mock.patch("sharepoint_rest_api.graph_client.requests.post")
@mock.patch("sharepoint_rest_api.graph_client.ConfidentialClientApplication")
def test_search_basic(mock_cca, mock_post):
    mock_app = mock_cca.return_value
    mock_app.acquire_token_for_client.return_value = {"access_token": "t"}
    mock_resp = mock.MagicMock()
    mock_resp.json.return_value = {
        "value": [
            {
                "hitsContainers": [
                    {
                        "total": 1,
                        "hits": [
                            {
                                "hitId": "hit1",
                                "rank": 1,
                                "resource": {
                                    "id": "doc1",
                                    "name": "doc.pdf",
                                    "webUrl": "https://sharepoint.com/site/doc1",
                                    "size": 512,
                                    "lastModifiedDateTime": "2024-01-01T00:00:00Z",
                                },
                            }
                        ],
                    }
                ]
            }
        ]
    }
    mock_post.return_value = mock_resp

    client = GraphClient()
    items, total = client.search()
    assert total == 1
    assert len(items) == 1
    assert items[0]["Title"] == "doc.pdf"


@mock.patch("sharepoint_rest_api.graph_client.requests.post")
@mock.patch("sharepoint_rest_api.graph_client.ConfidentialClientApplication")
def test_search_with_search_param(mock_cca, mock_post):
    mock_app = mock_cca.return_value
    mock_app.acquire_token_for_client.return_value = {"access_token": "t"}
    mock_resp = mock.MagicMock()
    mock_resp.json.return_value = {"value": [{"hitsContainers": [{"total": 0, "hits": []}]}]}
    mock_post.return_value = mock_resp

    client = GraphClient()
    items, total = client.search(search="path:/documents")
    assert total == 0
    assert items == []


@mock.patch("sharepoint_rest_api.graph_client.requests.post")
@mock.patch("sharepoint_rest_api.graph_client.ConfidentialClientApplication")
def test_search_with_searchable_properties(mock_cca, mock_post):
    mock_app = mock_cca.return_value
    mock_app.acquire_token_for_client.return_value = {"access_token": "t"}
    mock_resp = mock.MagicMock()
    mock_resp.json.return_value = {
        "value": [
            {
                "hitsContainers": [
                    {
                        "total": 1,
                        "hits": [
                            {
                                "hitId": "hit1",
                                "rank": 1,
                                "resource": {
                                    "id": "doc1",
                                    "name": "doc.pdf",
                                    "webUrl": "https://sharepoint.com/site/doc1",
                                    "size": 512,
                                    "lastModifiedDateTime": "2024-01-01T00:00:00Z",
                                },
                            }
                        ],
                    }
                ]
            }
        ]
    }
    mock_post.return_value = mock_resp

    client = GraphClient()
    items, total = client.search(
        filters={"Donor": "Red Cross"},
        searchable_properties={"Donor"},
    )
    assert total == 1
    body = mock_post.call_args[1]["json"]
    kql = body["requests"][0]["query"]["queryString"]
    assert "Donor" in kql


@mock.patch("sharepoint_rest_api.graph_client.requests.post")
@mock.patch("sharepoint_rest_api.graph_client.ConfidentialClientApplication")
def test_search_with_post_filters(mock_cca, mock_post):
    mock_app = mock_cca.return_value
    mock_app.acquire_token_for_client.return_value = {"access_token": "t"}
    mock_resp = mock.MagicMock()
    mock_resp.json.return_value = {
        "value": [
            {
                "hitsContainers": [
                    {
                        "total": 3,
                        "hits": [
                            {
                                "hitId": "hit1",
                                "rank": 1,
                                "resource": {
                                    "id": "doc1",
                                    "name": "doc1.pdf",
                                    "webUrl": "https://sharepoint.com/site/doc1",
                                    "size": 512,
                                    "lastModifiedDateTime": "2024-01-01T00:00:00Z",
                                    "listItem": {"fields": {"ReportStatus": "Final"}},
                                    "parentReference": {
                                        "siteId": "s1",
                                        "sharepointIds": {"listId": "l1", "listItemId": "i1"},
                                    },
                                },
                            },
                            {
                                "hitId": "hit2",
                                "rank": 2,
                                "resource": {
                                    "id": "doc2",
                                    "name": "doc2.pdf",
                                    "webUrl": "https://sharepoint.com/site/doc2",
                                    "size": 512,
                                    "lastModifiedDateTime": "2024-01-01T00:00:00Z",
                                    "listItem": {"fields": {"ReportStatus": "Draft"}},
                                    "parentReference": {
                                        "siteId": "s1",
                                        "sharepointIds": {"listId": "l1", "listItemId": "i2"},
                                    },
                                },
                            },
                            {
                                "hitId": "hit3",
                                "rank": 3,
                                "resource": {
                                    "id": "doc3",
                                    "name": "doc3.pdf",
                                    "webUrl": "https://sharepoint.com/site/doc3",
                                    "size": 512,
                                    "lastModifiedDateTime": "2024-01-01T00:00:00Z",
                                    "listItem": {"fields": {"ReportStatus": "Final"}},
                                    "parentReference": {
                                        "siteId": "s1",
                                        "sharepointIds": {"listId": "l1", "listItemId": "i3"},
                                    },
                                },
                            },
                        ],
                    }
                ]
            }
        ]
    }
    mock_post.return_value = mock_resp

    client = GraphClient()
    items, total = client.search(
        filters={"ReportStatus": "Final"},
        searchable_properties=set(),
    )
    assert total == 2
    assert len(items) == 2


@mock.patch("sharepoint_rest_api.graph_client.requests.post")
@mock.patch("sharepoint_rest_api.graph_client.ConfidentialClientApplication")
def test_search_with_post_filters_single_page(mock_cca, mock_post):
    mock_app = mock_cca.return_value
    mock_app.acquire_token_for_client.return_value = {"access_token": "t"}

    mock_resp = mock.MagicMock()
    mock_resp.json.return_value = {
        "value": [
            {
                "hitsContainers": [
                    {
                        "total": 3,
                        "hits": [
                            {
                                "hitId": "hit1",
                                "rank": 1,
                                "resource": {
                                    "id": "doc1",
                                    "name": "doc1.pdf",
                                    "webUrl": "https://sharepoint.com/site/doc1",
                                    "size": 512,
                                    "lastModifiedDateTime": "2024-01-01T00:00:00Z",
                                    "listItem": {"fields": {"ReportStatus": "Final"}},
                                    "parentReference": {
                                        "siteId": "s1",
                                        "sharepointIds": {"listId": "l1", "listItemId": "i1"},
                                    },
                                },
                            },
                            {
                                "hitId": "hit2",
                                "rank": 2,
                                "resource": {
                                    "id": "doc2",
                                    "name": "doc2.pdf",
                                    "webUrl": "https://sharepoint.com/site/doc2",
                                    "size": 512,
                                    "lastModifiedDateTime": "2024-01-01T00:00:00Z",
                                    "listItem": {"fields": {"ReportStatus": "Draft"}},
                                    "parentReference": {
                                        "siteId": "s1",
                                        "sharepointIds": {"listId": "l1", "listItemId": "i2"},
                                    },
                                },
                            },
                        ],
                    }
                ]
            }
        ]
    }
    mock_post.return_value = mock_resp

    client = GraphClient()
    with mock.patch.object(GraphClient, "_fetch_item_fields"):
        items, total = client.search(
            filters={"ReportStatus": "Final"},
            searchable_properties=set(),
        )
    assert total == 1
    assert len(items) == 1
    assert items[0]["DocId"] == "doc1"


@mock.patch("sharepoint_rest_api.graph_client.requests.post")
@mock.patch("sharepoint_rest_api.graph_client.ConfidentialClientApplication")
def test_search_with_pagination(mock_cca, mock_post):
    mock_app = mock_cca.return_value
    mock_app.acquire_token_for_client.return_value = {"access_token": "t"}
    mock_resp = mock.MagicMock()
    mock_resp.json.return_value = {
        "value": [
            {
                "hitsContainers": [
                    {
                        "total": 10,
                        "hits": [
                            {
                                "hitId": f"hit{i}",
                                "rank": i,
                                "resource": {
                                    "id": f"doc{i}",
                                    "name": f"doc{i}.pdf",
                                    "webUrl": f"https://sharepoint.com/site/doc{i}",
                                    "size": 512,
                                    "lastModifiedDateTime": "2024-01-01T00:00:00Z",
                                },
                            }
                            for i in range(5)
                        ],
                    }
                ]
            }
        ]
    }
    mock_post.return_value = mock_resp

    client = GraphClient()
    items, total = client.search(page=2)
    assert total == 10


@mock.patch("sharepoint_rest_api.graph_client.requests.post")
@mock.patch("sharepoint_rest_api.graph_client.ConfidentialClientApplication")
def test_search_post_filters_no_match(mock_cca, mock_post):
    mock_app = mock_cca.return_value
    mock_app.acquire_token_for_client.return_value = {"access_token": "t"}

    mock_resp = mock.MagicMock()
    mock_resp.json.return_value = {
        "value": [
            {
                "hitsContainers": [
                    {
                        "total": 2,
                        "hits": [
                            {
                                "hitId": "hit1",
                                "rank": 1,
                                "resource": {
                                    "id": "doc1",
                                    "name": "doc1.pdf",
                                    "webUrl": "https://sharepoint.com/site/doc1",
                                    "size": 512,
                                    "lastModifiedDateTime": "2024-01-01T00:00:00Z",
                                    "listItem": {"fields": {"ReportStatus": "Draft"}},
                                },
                            },
                        ],
                    }
                ]
            }
        ]
    }
    mock_post.return_value = mock_resp

    client = GraphClient()
    with mock.patch.object(GraphClient, "_fetch_item_fields"):
        items, total = client.search(
            filters={"ReportStatus": "Final"},
            searchable_properties=set(),
        )
    assert total == 0
    assert len(items) == 0


@mock.patch("sharepoint_rest_api.graph_client.requests.post")
@mock.patch("sharepoint_rest_api.graph_client.ConfidentialClientApplication")
def test_search_with_custom_page_size(mock_cca, mock_post):
    mock_app = mock_cca.return_value
    mock_app.acquire_token_for_client.return_value = {"access_token": "t"}

    mock_resp = mock.MagicMock()
    mock_resp.json.return_value = {
        "value": [
            {
                "hitsContainers": [
                    {
                        "total": 2,
                        "hits": [
                            {
                                "hitId": f"hit{i}",
                                "rank": i,
                                "resource": {
                                    "id": f"doc{i}",
                                    "name": f"doc{i}.pdf",
                                    "webUrl": f"https://sharepoint.com/site/doc{i}",
                                    "size": 512,
                                    "lastModifiedDateTime": "2024-01-01T00:00:00Z",
                                },
                            }
                            for i in range(2)
                        ],
                    }
                ]
            }
        ]
    }
    mock_post.return_value = mock_resp

    client = GraphClient()
    items, total = client.search(page_size=10)
    assert total == 2
    assert len(items) == 2
    body = mock_post.call_args[1]["json"]
    assert body["requests"][0]["size"] == 10


@mock.patch("sharepoint_rest_api.graph_client.requests.post")
@mock.patch("sharepoint_rest_api.graph_client.ConfidentialClientApplication")
def test_search_default_page_size(mock_cca, mock_post):
    mock_app = mock_cca.return_value
    mock_app.acquire_token_for_client.return_value = {"access_token": "t"}

    mock_resp = mock.MagicMock()
    mock_resp.json.return_value = {
        "value": [
            {
                "hitsContainers": [
                    {
                        "total": 0,
                        "hits": [],
                    }
                ]
            }
        ]
    }
    mock_post.return_value = mock_resp

    client = GraphClient()
    with mock.patch("sharepoint_rest_api.graph_client.config.GRAPH_PAGE_SIZE", 20):
        client.search()
    body = mock_post.call_args[1]["json"]
    assert body["requests"][0]["size"] == 20


@mock.patch("sharepoint_rest_api.graph_client.requests.post")
@mock.patch("sharepoint_rest_api.graph_client.ConfidentialClientApplication")
def test_search_with_all_params(mock_cca, mock_post):
    mock_app = mock_cca.return_value
    mock_app.acquire_token_for_client.return_value = {"access_token": "t"}
    mock_resp = mock.MagicMock()
    mock_resp.json.return_value = {"value": [{"hitsContainers": [{"total": 0, "hits": []}]}]}
    mock_post.return_value = mock_resp

    client = GraphClient()
    items, total = client.search(
        search="path:/docs",
        filters={"Donor__eq": "Red Cross"},
        page=1,
        searchable_properties={"Donor"},
        reverse_map={"DonorCode": "DRPDonorCode"},
    )
    assert total == 0
    assert items == []


@mock.patch("sharepoint_rest_api.graph_client.requests.get")
@mock.patch("sharepoint_rest_api.graph_client.requests.post")
@mock.patch("sharepoint_rest_api.graph_client.ConfidentialClientApplication")
def test_read_list_items(mock_cca, mock_post, mock_get):
    mock_app = mock_cca.return_value
    mock_app.acquire_token_for_client.return_value = {"access_token": "t"}

    page1_resp = mock.MagicMock()
    page1_resp.json.return_value = {
        "value": [{"id": "1", "fields": {"Title": "Doc1"}}, {"id": "2", "fields": {"Title": "Doc2"}}],
        "@odata.nextLink": "https://graph.microsoft.com/v1.0/sites/site123/lists/MyList/items?$skiptoken=abc",
    }
    page2_resp = mock.MagicMock()
    page2_resp.json.return_value = {
        "value": [{"id": "3", "fields": {"Title": "Doc3"}}],
    }
    mock_get.side_effect = [page1_resp, page2_resp]

    client = GraphClient()
    with mock.patch.object(GraphClient, "_get_site_id", return_value="site123"):
        items = client.read_list_items("MyList")

    assert len(items) == 3
    assert items[0]["fields"]["Title"] == "Doc1"
    assert items[2]["fields"]["Title"] == "Doc3"
    assert mock_get.call_count == 2


@mock.patch("sharepoint_rest_api.graph_client.requests.post")
@mock.patch("sharepoint_rest_api.graph_client.ConfidentialClientApplication")
def test_search_post_filter_cache_hit(mock_cca, mock_post):
    mock_app = mock_cca.return_value
    mock_app.acquire_token_for_client.return_value = {"access_token": "t"}
    mock_resp = mock.MagicMock()
    mock_resp.json.return_value = {
        "value": [
            {
                "hitsContainers": [
                    {
                        "total": 1,
                        "hits": [
                            {
                                "hitId": "hit1",
                                "rank": 1,
                                "resource": {
                                    "id": "doc1",
                                    "name": "doc1.pdf",
                                    "webUrl": "https://sharepoint.com/site/doc1",
                                    "size": 512,
                                    "lastModifiedDateTime": "2024-01-01T00:00:00Z",
                                    "listItem": {"fields": {"ReportStatus": "Final"}},
                                    "parentReference": {
                                        "siteId": "s1",
                                        "sharepointIds": {"listId": "l1", "listItemId": "i1"},
                                    },
                                },
                            }
                        ],
                    }
                ]
            }
        ]
    }
    mock_post.return_value = mock_resp

    client = GraphClient()
    with mock.patch.object(GraphClient, "_fetch_item_fields"):
        items1, total1 = client.search(filters={"ReportStatus": "Final"}, searchable_properties=set())
        items2, total2 = client.search(filters={"ReportStatus": "Final"}, searchable_properties=set())

    assert total1 == total2 == 1
    assert len(items1) == len(items2) == 1
    assert mock_post.call_count == 1


@mock.patch("sharepoint_rest_api.graph_client.requests.post")
@mock.patch("sharepoint_rest_api.graph_client.ConfidentialClientApplication")
def test_scan_all_post_filtered_multi_page(mock_cca, mock_post):
    mock_app = mock_cca.return_value
    mock_app.acquire_token_for_client.return_value = {"access_token": "t"}

    page1_resp = mock.MagicMock()
    page1_resp.json.return_value = {
        "value": [
            {
                "hitsContainers": [
                    {
                        "total": 10,
                        "hits": [
                            {
                                "hitId": f"hit{i}",
                                "rank": i,
                                "resource": {
                                    "id": f"doc{i}",
                                    "name": f"doc{i}.pdf",
                                    "webUrl": f"https://sharepoint.com/site/doc{i}",
                                    "size": 512,
                                    "lastModifiedDateTime": "2024-01-01T00:00:00Z",
                                    "listItem": {"fields": {"ReportStatus": "Final"}},
                                    "parentReference": {
                                        "siteId": "s1",
                                        "sharepointIds": {"listId": "l1", "listItemId": f"i{i}"},
                                    },
                                },
                            }
                            for i in range(2)
                        ],
                    }
                ]
            }
        ]
    }
    page2_resp = mock.MagicMock()
    page2_resp.json.return_value = {
        "value": [
            {
                "hitsContainers": [
                    {
                        "total": 10,
                        "hits": [
                            {
                                "hitId": "hit_extra",
                                "rank": 1,
                                "resource": {
                                    "id": "doc_extra",
                                    "name": "doc_extra.pdf",
                                    "webUrl": "https://sharepoint.com/site/doc_extra",
                                    "size": 512,
                                    "lastModifiedDateTime": "2024-01-01T00:00:00Z",
                                    "listItem": {"fields": {"ReportStatus": "Final"}},
                                    "parentReference": {
                                        "siteId": "s1",
                                        "sharepointIds": {"listId": "l1", "listItemId": "i_extra"},
                                    },
                                },
                            }
                        ],
                    }
                ]
            }
        ]
    }
    mock_post.side_effect = [page1_resp, page2_resp]

    client = GraphClient()
    with mock.patch.object(GraphClient, "_fetch_item_fields"):
        with mock.patch("sharepoint_rest_api.graph_client.config.GRAPH_PAGE_SIZE", 5):
            items, total = client.search(filters={"ReportStatus": "Final"}, searchable_properties=set())

    assert total == 3
    assert len(items) == 3
    assert mock_post.call_count == 2


@mock.patch("sharepoint_rest_api.graph_client.requests.post")
@mock.patch("sharepoint_rest_api.graph_client.ConfidentialClientApplication")
def test_scan_all_post_filtered_empty_total(mock_cca, mock_post):
    mock_app = mock_cca.return_value
    mock_app.acquire_token_for_client.return_value = {"access_token": "t"}
    mock_resp = mock.MagicMock()
    mock_resp.json.return_value = {"value": [{"hitsContainers": [{"total": 0, "hits": []}]}]}
    mock_post.return_value = mock_resp

    client = GraphClient()
    items, total = client.search(filters={"ReportStatus": "Final"}, searchable_properties=set())

    assert total == 0
    assert items == []


@mock.patch("sharepoint_rest_api.graph_client.requests.post")
@mock.patch("sharepoint_rest_api.graph_client.ConfidentialClientApplication")
def test_scan_all_post_filtered_exhaust_all_pages(mock_cca, mock_post):
    mock_app = mock_cca.return_value
    mock_app.acquire_token_for_client.return_value = {"access_token": "t"}

    def side_effect(*args, **kwargs):
        mock_resp = mock.MagicMock()
        mock_resp.json.return_value = {
            "value": [
                {
                    "hitsContainers": [
                        {
                            "total": 50,
                            "hits": [
                                {
                                    "hitId": "hit",
                                    "rank": 1,
                                    "resource": {
                                        "id": "doc",
                                        "name": "doc.pdf",
                                        "webUrl": "https://sharepoint.com/site/doc",
                                        "size": 512,
                                        "lastModifiedDateTime": "2024-01-01T00:00:00Z",
                                        "listItem": {"fields": {"ReportStatus": "Final"}},
                                        "parentReference": {
                                            "siteId": "s1",
                                            "sharepointIds": {"listId": "l1", "listItemId": "i1"},
                                        },
                                    },
                                }
                                for _ in range(2)
                            ],
                        }
                    ]
                }
            ]
        }
        return mock_resp

    mock_post.side_effect = side_effect

    client = GraphClient()
    with mock.patch.object(GraphClient, "_fetch_item_fields"):
        with mock.patch("sharepoint_rest_api.graph_client.config.GRAPH_PAGE_SIZE", 3):
            items, total = client.search(filters={"ReportStatus": "Final"}, searchable_properties=set())

    assert total == 10
    assert len(items) == 3
    assert mock_post.call_count == 5


# ---- _parse_last_modified -----------------------------------------------------


def test_parse_last_modified_valid():
    result = _parse_last_modified({"LastModifiedTime": "2024-06-15T10:30:00Z"})
    assert result == datetime(2024, 6, 15, 10, 30, tzinfo=timezone.utc)


def test_parse_last_modified_empty():
    result = _parse_last_modified({})
    assert result == datetime.min


def test_parse_last_modified_empty_string():
    result = _parse_last_modified({"LastModifiedTime": ""})
    assert result == datetime.min


def test_parse_last_modified_invalid():
    result = _parse_last_modified({"LastModifiedTime": "not-a-date"})
    assert result == datetime.min


def test_parse_last_modified_custom_field():
    result = _parse_last_modified({"Created": "2024-01-01T00:00:00Z"}, field="Created")
    assert result == datetime(2024, 1, 1, tzinfo=timezone.utc)


# ---- get_drive_id_by_name -----------------------------------------------------


@mock.patch("sharepoint_rest_api.graph_client.requests.get")
@mock.patch("sharepoint_rest_api.graph_client.ConfidentialClientApplication")
def test_get_drive_id_by_name_no_site_id(mock_cca, mock_get):
    mock_app = mock_cca.return_value
    mock_app.acquire_token_for_client.return_value = {"access_token": "t"}
    client = GraphClient()
    result = client.get_drive_id_by_name("Documents", site_id=None)
    assert result is None
    mock_get.assert_not_called()


@mock.patch("sharepoint_rest_api.graph_client.requests.get")
@mock.patch("sharepoint_rest_api.graph_client.ConfidentialClientApplication")
def test_get_drive_id_by_name_found(mock_cca, mock_get):
    mock_app = mock_cca.return_value
    mock_app.acquire_token_for_client.return_value = {"access_token": "t"}
    mock_resp = mock.MagicMock()
    mock_resp.json.return_value = {"value": [{"id": "drive-abc-123", "name": "Documents"}]}
    mock_get.return_value = mock_resp

    client = GraphClient()
    result = client.get_drive_id_by_name("Documents", site_id="site123")
    assert result == "drive-abc-123"


@mock.patch("sharepoint_rest_api.graph_client.requests.get")
@mock.patch("sharepoint_rest_api.graph_client.ConfidentialClientApplication")
def test_get_drive_id_by_name_not_found(mock_cca, mock_get):
    mock_app = mock_cca.return_value
    mock_app.acquire_token_for_client.return_value = {"access_token": "t"}
    mock_resp = mock.MagicMock()
    mock_resp.json.return_value = {"value": []}
    mock_get.return_value = mock_resp

    client = GraphClient()
    result = client.get_drive_id_by_name("NonExistent", site_id="site123")
    assert result is None


@mock.patch("sharepoint_rest_api.graph_client.requests.get")
@mock.patch("sharepoint_rest_api.graph_client.ConfidentialClientApplication")
def test_get_drive_id_by_name_http_error(mock_cca, mock_get):
    mock_app = mock_cca.return_value
    mock_app.acquire_token_for_client.return_value = {"access_token": "t"}
    mock_get.side_effect = requests.exceptions.RequestException("timeout")

    client = GraphClient()
    result = client.get_drive_id_by_name("Documents", site_id="site123")
    assert result is None


@mock.patch("sharepoint_rest_api.graph_client.requests.get")
@mock.patch("sharepoint_rest_api.graph_client.ConfidentialClientApplication")
def test_get_drive_id_by_name_cache_hit(mock_cca, mock_get):
    mock_app = mock_cca.return_value
    mock_app.acquire_token_for_client.return_value = {"access_token": "t"}
    mock_resp = mock.MagicMock()
    mock_resp.json.return_value = {"value": [{"id": "drive-abc-123", "name": "Documents"}]}
    mock_get.return_value = mock_resp

    client = GraphClient()
    result1 = client.get_drive_id_by_name("Documents", site_id="site123")
    assert result1 == "drive-abc-123"
    assert mock_get.call_count == 1

    result2 = client.get_drive_id_by_name("Documents", site_id="site123")
    assert result2 == "drive-abc-123"
    assert mock_get.call_count == 1


# ---- _parse_order_by ----------------------------------------------------------


def test_parse_order_by_none():
    field, desc = GraphClient._parse_order_by(None)
    assert field is None
    assert desc is False


def test_parse_order_by_empty():
    field, desc = GraphClient._parse_order_by("")
    assert field is None
    assert desc is False


def test_parse_order_by_asc():
    field, desc = GraphClient._parse_order_by("LastModifiedTime asc")
    assert field == "LastModifiedTime"
    assert desc is False


def test_parse_order_by_desc():
    field, desc = GraphClient._parse_order_by("LastModifiedTime desc")
    assert field == "LastModifiedTime"
    assert desc is True


def test_parse_order_by_no_direction():
    field, desc = GraphClient._parse_order_by("LastModifiedTime")
    assert field == "LastModifiedTime"
    assert desc is False


# ---- download_file -----------------------------------------------------------


@mock.patch("sharepoint_rest_api.graph_client.requests.get")
@mock.patch("sharepoint_rest_api.graph_client.ConfidentialClientApplication")
def test_download_file_with_drive_id(mock_cca, mock_get):
    mock_app = mock_cca.return_value
    mock_app.acquire_token_for_client.return_value = {"access_token": "t"}
    mock_resp = mock.MagicMock()
    mock_resp.ok = True
    mock_resp.content = b"file-content"
    mock_get.return_value = mock_resp

    client = GraphClient()
    with mock.patch.object(GraphClient, "_get_site_id", return_value="site1"):
        resp = client.download_file("Shared Docs/file.pdf", drive_id="drive-123")

    assert resp.ok
    assert resp.content == b"file-content"
    url = mock_get.call_args[0][0]
    assert "/drives/" in url
    assert "root:" in url
    assert "/content" in url


@mock.patch("sharepoint_rest_api.graph_client.requests.get")
@mock.patch("sharepoint_rest_api.graph_client.ConfidentialClientApplication")
def test_download_file_without_drive_id(mock_cca, mock_get):
    mock_app = mock_cca.return_value
    mock_app.acquire_token_for_client.return_value = {"access_token": "t"}
    mock_resp = mock.MagicMock()
    mock_resp.ok = True
    mock_resp.content = b"file-content"
    mock_get.return_value = mock_resp

    client = GraphClient()
    with mock.patch.object(GraphClient, "_get_site_id", return_value="site1"):
        resp = client.download_file("Shared Docs/file.pdf")

    assert resp.ok
    url = mock_get.call_args[0][0]
    assert "/drive/root:" in url
    assert "/drives/" not in url
    assert "/content" in url


@mock.patch("sharepoint_rest_api.graph_client.requests.get")
@mock.patch("sharepoint_rest_api.graph_client.ConfidentialClientApplication")
def test_download_file_with_site_id(mock_cca, mock_get):
    mock_app = mock_cca.return_value
    mock_app.acquire_token_for_client.return_value = {"access_token": "t"}
    mock_resp = mock.MagicMock()
    mock_resp.ok = True
    mock_resp.content = b"data"
    mock_get.return_value = mock_resp

    client = GraphClient()
    resp = client.download_file("doc.pdf", site_id="my-site-id")
    assert resp.ok
    url = mock_get.call_args[0][0]
    assert "my-site-id" in url


@mock.patch("sharepoint_rest_api.graph_client.requests.get")
@mock.patch("sharepoint_rest_api.graph_client.ConfidentialClientApplication")
def test_download_file_http_error(mock_cca, mock_get):
    mock_app = mock_cca.return_value
    mock_app.acquire_token_for_client.return_value = {"access_token": "t"}
    mock_resp = mock.MagicMock()
    mock_resp.ok = False
    mock_resp.status_code = 404
    mock_resp.text = "Not Found"
    mock_get.return_value = mock_resp

    client = GraphClient()
    with mock.patch.object(GraphClient, "_get_site_id", return_value="site1"):
        with pytest.raises(GraphClientError, match="Graph file download failed"):
            client.download_file("missing.pdf")


@mock.patch("sharepoint_rest_api.graph_client.requests.get")
@mock.patch("sharepoint_rest_api.graph_client.ConfidentialClientApplication")
def test_download_file_request_exception(mock_cca, mock_get):
    mock_app = mock_cca.return_value
    mock_app.acquire_token_for_client.return_value = {"access_token": "t"}
    mock_get.side_effect = requests.exceptions.ConnectionError("refused")

    client = GraphClient()
    with mock.patch.object(GraphClient, "_get_site_id", return_value="site1"):
        with pytest.raises(GraphClientError, match="Graph file download failed"):
            client.download_file("doc.pdf")


# ---- download_item -----------------------------------------------------------


@mock.patch("sharepoint_rest_api.graph_client.requests.get")
@mock.patch("sharepoint_rest_api.graph_client.ConfidentialClientApplication")
def test_download_item_success(mock_cca, mock_get):
    mock_app = mock_cca.return_value
    mock_app.acquire_token_for_client.return_value = {"access_token": "t"}
    mock_resp = mock.MagicMock()
    mock_resp.ok = True
    mock_resp.content = b"item-content"
    mock_get.return_value = mock_resp

    client = GraphClient()
    resp = client.download_item("drive-abc", "item-xyz")
    assert resp.ok
    assert resp.content == b"item-content"
    url = mock_get.call_args[0][0]
    assert "/drives/drive-abc/items/item-xyz/content" in url


@mock.patch("sharepoint_rest_api.graph_client.requests.get")
@mock.patch("sharepoint_rest_api.graph_client.ConfidentialClientApplication")
def test_download_item_http_error(mock_cca, mock_get):
    mock_app = mock_cca.return_value
    mock_app.acquire_token_for_client.return_value = {"access_token": "t"}
    mock_resp = mock.MagicMock()
    mock_resp.ok = False
    mock_resp.status_code = 404
    mock_resp.text = "Not Found"
    mock_get.return_value = mock_resp

    client = GraphClient()
    with pytest.raises(GraphClientError, match="Graph item download failed"):
        client.download_item("drive-abc", "item-xyz")


@mock.patch("sharepoint_rest_api.graph_client.requests.get")
@mock.patch("sharepoint_rest_api.graph_client.ConfidentialClientApplication")
def test_download_item_request_exception(mock_cca, mock_get):
    mock_app = mock_cca.return_value
    mock_app.acquire_token_for_client.return_value = {"access_token": "t"}
    mock_get.side_effect = requests.exceptions.ConnectionError("refused")

    client = GraphClient()
    with pytest.raises(GraphClientError, match="Graph item download failed"):
        client.download_item("drive-abc", "item-xyz")


# ---- search with order_by (covers _parse_order_by + sort line) ---------------


@mock.patch("sharepoint_rest_api.graph_client.requests.post")
@mock.patch("sharepoint_rest_api.graph_client.ConfidentialClientApplication")
def test_search_with_order_by_and_post_filters(mock_cca, mock_post):
    mock_app = mock_cca.return_value
    mock_app.acquire_token_for_client.return_value = {"access_token": "t"}

    mock_resp = mock.MagicMock()
    mock_resp.json.return_value = {
        "value": [
            {
                "hitsContainers": [
                    {
                        "total": 2,
                        "hits": [
                            {
                                "hitId": "hit1",
                                "rank": 1,
                                "resource": {
                                    "id": "doc1",
                                    "name": "doc1.pdf",
                                    "webUrl": "https://sharepoint.com/site/doc1",
                                    "size": 512,
                                    "lastModifiedDateTime": "2024-01-01T00:00:00Z",
                                    "listItem": {"fields": {"ReportStatus": "Final"}},
                                    "parentReference": {
                                        "siteId": "s1",
                                        "sharepointIds": {"listId": "l1", "listItemId": "i1"},
                                    },
                                },
                            },
                            {
                                "hitId": "hit2",
                                "rank": 2,
                                "resource": {
                                    "id": "doc2",
                                    "name": "doc2.pdf",
                                    "webUrl": "https://sharepoint.com/site/doc2",
                                    "size": 512,
                                    "lastModifiedDateTime": "2023-06-01T00:00:00Z",
                                    "listItem": {"fields": {"ReportStatus": "Final"}},
                                    "parentReference": {
                                        "siteId": "s1",
                                        "sharepointIds": {"listId": "l1", "listItemId": "i2"},
                                    },
                                },
                            },
                        ],
                    }
                ]
            }
        ]
    }
    mock_post.return_value = mock_resp

    client = GraphClient()
    with mock.patch.object(GraphClient, "_fetch_item_fields"):
        items, total = client.search(
            filters={"ReportStatus": "Final"},
            searchable_properties=set(),
            order_by="LastModifiedTime desc",
        )
    assert total == 2
    assert len(items) == 2
    assert items[0]["LastModifiedTime"] >= items[1]["LastModifiedTime"]


@mock.patch("sharepoint_rest_api.graph_client.requests.post")
@mock.patch("sharepoint_rest_api.graph_client.ConfidentialClientApplication")
def test_search_with_order_by_no_post_filters_passes_sort_properties(mock_cca, mock_post):
    """Server-side sorting: sortProperties should be in the request body."""
    mock_app = mock_cca.return_value
    mock_app.acquire_token_for_client.return_value = {"access_token": "t"}

    mock_resp = mock.MagicMock()
    mock_resp.json.return_value = {
        "value": [
            {
                "hitsContainers": [
                    {
                        "total": 1,
                        "hits": [
                            {
                                "hitId": "hit1",
                                "rank": 1,
                                "resource": {
                                    "id": "doc1",
                                    "name": "doc1.pdf",
                                    "webUrl": "https://sharepoint.com/site/doc1",
                                    "size": 512,
                                    "lastModifiedDateTime": "2024-01-01T00:00:00Z",
                                    "parentReference": {
                                        "siteId": "s1",
                                        "sharepointIds": {"listId": "l1", "listItemId": "i1"},
                                    },
                                },
                            },
                        ],
                    }
                ]
            }
        ]
    }
    mock_post.return_value = mock_resp

    client = GraphClient()
    with mock.patch.object(GraphClient, "_fetch_item_fields"):
        client.search(order_by="RefinableDate11 desc")

    call_kwargs = mock_post.call_args
    body = call_kwargs[1]["json"] if "json" in call_kwargs[1] else call_kwargs[0][1]
    request_body = body["requests"][0]
    assert "sortProperties" in request_body
    assert request_body["sortProperties"] == [{"name": "RefinableDate11", "isDescending": True}]
