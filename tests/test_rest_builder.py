from unittest import mock

from sharepoint_rest_api.builders.rest_builder import GRAPH_SEARCH_URL, GRAPH_URL, RestBuilder


# ---- Constants ---------------------------------------------------------------


def test_graph_url():
    assert GRAPH_URL == "https://graph.microsoft.com/v1.0"


def test_graph_search_url():
    assert GRAPH_SEARCH_URL == "https://graph.microsoft.com/v1.0/search/query"


# ---- build_kql_clause --------------------------------------------------------


def test_kql_clause_eq():
    result = RestBuilder.build_kql_clause("Donor", "Red Cross")
    assert result == ['Donor:"Red Cross"']


def test_kql_clause_eq_multi():
    result = RestBuilder.build_kql_clause("Donor", "Red Cross,UNICEF")
    assert result == ['Donor:("Red Cross" OR "UNICEF")']


def test_kql_clause_not():
    result = RestBuilder.build_kql_clause("Donor__not", "Red Cross")
    assert result == ['Donor<>"Red Cross"']


def test_kql_clause_contains():
    result = RestBuilder.build_kql_clause("Donor__contains", "Cross")
    assert result == ['Donor:"Cross*"']


def test_kql_clause_not_in():
    result = RestBuilder.build_kql_clause("Donor__not_in", "Red Cross,UNICEF")
    assert result == ['-"Red Cross"', '-"UNICEF"']


def test_kql_clause_unknown_operator():
    result = RestBuilder.build_kql_clause("Donor__unknown", "val")
    assert result == ['Donor:"val"']


# ---- build_kql ---------------------------------------------------------------


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
    assert result == 'Donor<>"Red Cross"'


def test_kql_contains_filter():
    result = RestBuilder.build_kql(filters={"Donor__contains": "Cross"})
    assert result == 'Donor:"Cross*"'


def test_kql_not_in_filter():
    result = RestBuilder.build_kql(filters={"Donor__not_in": "Red Cross,UNICEF"})
    assert result == '-"Red Cross" AND -"UNICEF"'


def test_kql_unknown_operator():
    result = RestBuilder.build_kql(filters={"Donor__unknown": "val"})
    assert result == 'Donor:"val"'


def test_kql_search_with_filters():
    result = RestBuilder.build_kql(search="path:/docs", filters={"Donor": "Red Cross"})
    assert result == 'path:/docs AND Donor:"Red Cross"'


def test_kql_multiple_filters():
    result = RestBuilder.build_kql(filters={"Donor": "Red Cross", "ReportStatus": "Final"})
    assert 'Donor:"Red Cross"' in result
    assert 'ReportStatus:"Final"' in result
    assert " AND " in result


def test_kql_gte_falls_back_to_eq():
    result = RestBuilder.build_kql(filters={"Size__gte": "1000"})
    assert result == 'Size:"1000"'


# ---- build_search_request_body -----------------------------------------------


@mock.patch("sharepoint_rest_api.builders.rest_builder.config.GRAPH_REGION", "global")
def test_build_search_request_body():
    body = RestBuilder.build_search_request_body("test query", 0, 25)
    assert body == {
        "requests": [
            {
                "entityTypes": ["driveItem"],
                "query": {"queryString": "test query"},
                "region": "global",
                "from": 0,
                "size": 25,
            }
        ]
    }


# ---- build_batch_body --------------------------------------------------------


def test_build_batch_body():
    requests_list = [{"id": str(i), "method": "GET", "url": f"/items/{i}"} for i in range(5)]
    body = RestBuilder.build_batch_body(requests_list)
    assert body == {"requests": requests_list}


def test_build_batch_body_truncates():
    requests_list = [{"id": str(i), "method": "GET", "url": f"/items/{i}"} for i in range(30)]
    body = RestBuilder.build_batch_body(requests_list)
    assert len(body["requests"]) == 20
