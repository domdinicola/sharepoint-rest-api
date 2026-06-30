from unittest.mock import MagicMock, patch

from sharepoint_rest_api.builders.camlquery_builder import recursive_builder, CamlQueryBuilder
from sharepoint_rest_api.builders.querystring_builder import QueryStringBuilder
from sharepoint_rest_api.builders.search_request_builder import SearchRequestBuilder


def test_recursive_builder_empty():
    assert recursive_builder([]) == ""


def test_recursive_builder_single():
    assert recursive_builder(["<Eq/>"]) == "<Eq/>"


def test_recursive_builder_two():
    assert recursive_builder(["<A/>", "<B/>"]) == "<And><B/><A/></And>"


def test_recursive_builder_two_custom_operator():
    assert recursive_builder(["<A/>", "<B/>"], "Or") == "<Or><B/><A/></Or>"


def test_recursive_builder_three():
    result = recursive_builder(["<A/>", "<B/>", "<C/>"])
    assert result == "<And><C/><And><B/><A/></And></And>"


def test_camlquery_builder_init_default():
    builder = CamlQueryBuilder()
    assert builder.filters == {}
    assert builder.scope is None


def test_camlquery_builder_init_with_filters_and_scope():
    builder = CamlQueryBuilder(filters={"a": "b"}, scope="RecursiveAll")
    assert builder.filters == {"a": "b"}
    assert builder.scope == "RecursiveAll"


def test_camlquery_builder_create_query_no_filters():
    result = CamlQueryBuilder().create_query()
    assert result == "<View><Query><Where></Where></Query></View>"


def test_camlquery_builder_create_query_no_filters_with_scope():
    result = CamlQueryBuilder(scope="RecursiveAll").create_query()
    assert result == '<View Scope="RecursiveAll"><Query><Where></Where></Query></View>'


def test_camlquery_builder_create_query_eq():
    result = CamlQueryBuilder({"name": "toro"}).create_query()
    expected = (
        '<View><Query><Where><Eq><FieldRef Name="Name" /><Value Type="Text">toro</Value></Eq></Where></Query></View>'
    )
    assert result == expected


def test_camlquery_builder_create_query_contains():
    result = CamlQueryBuilder({"name__contains": "tor"}).create_query()
    expected = (
        "<View><Query><Where>"
        '<Contains><FieldRef Name="Name" /><Value Type="Text">tor</Value></Contains>'
        "</Where></Query></View>"
    )
    assert result == expected


def test_camlquery_builder_create_query_gte_date():
    result = CamlQueryBuilder({"date__gte": "2020-01-01"}).create_query()
    expected = (
        "<View><Query><Where>"
        '<Geq><FieldRef Name="Date" /><Value Type="DateTime">2020-01-01T00:00:00Z</Value></Geq>'
        "</Where></Query></View>"
    )
    assert result == expected


def test_camlquery_builder_create_query_gt_date():
    result = CamlQueryBuilder({"date__gt": "2020-01-01"}).create_query()
    expected = (
        "<View><Query><Where>"
        '<Gt><FieldRef Name="Date" /><Value Type="DateTime">2020-01-01T00:00:00Z</Value></Gt>'
        "</Where></Query></View>"
    )
    assert result == expected


def test_camlquery_builder_create_query_lte_date():
    result = CamlQueryBuilder({"date__lte": "2020-01-01"}).create_query()
    expected = (
        "<View><Query><Where>"
        '<Leq><FieldRef Name="Date" /><Value Type="DateTime">2020-01-01T00:00:00Z</Value></Leq>'
        "</Where></Query></View>"
    )
    assert result == expected


def test_camlquery_builder_create_query_lt_date():
    result = CamlQueryBuilder({"date__lt": "2020-01-01"}).create_query()
    expected = (
        "<View><Query><Where>"
        '<Lt><FieldRef Name="Date" /><Value Type="DateTime">2020-01-01T00:00:00Z</Value></Lt>'
        "</Where></Query></View>"
    )
    assert result == expected


def test_camlquery_builder_create_query_not():
    result = CamlQueryBuilder({"name__not": "toro"}).create_query()
    expected = (
        '<View><Query><Where><Neq><FieldRef Name="Name" /><Value Type="Text">toro</Value></Neq></Where></Query></View>'
    )
    assert result == expected


def test_camlquery_builder_create_query_multi_value():
    result = CamlQueryBuilder({"name": "a,b"}).create_query()
    assert (
        '<Or><Eq><FieldRef Name="Name" /><Value Type="Text">b</Value></Eq>'
        '<Eq><FieldRef Name="Name" /><Value Type="Text">a</Value></Eq></Or>'
    ) in result


def test_camlquery_builder_create_query_single_value():
    result = CamlQueryBuilder({"name": "a"}).create_query()
    assert "Or" not in result
    assert '<Eq><FieldRef Name="Name" /><Value Type="Text">a</Value></Eq>' in result


def test_camlquery_builder_create_query_two_filters():
    result = CamlQueryBuilder({"donor": "Australia", "recipient_office__contains": "Afghanistan"}).create_query()
    assert result.count("And") == 2
    assert "<And>" in result


def test_camlquery_builder_create_query_three_filters():
    result = CamlQueryBuilder(
        {
            "donor": "Australia",
            "recipient_office__contains": "Afghanistan",
            "donor_report_category": "Financial",
        }
    ).create_query()
    assert result.count("And") == 4


def test_camlquery_builder_create_query_unknown_operator():
    result = CamlQueryBuilder({"name__custom": "val"}).create_query()
    assert '<Eq><FieldRef Name="Name" /><Value Type="Text">val</Value></Eq>' in result


@patch("sharepoint_rest_api.builders.camlquery_builder.CamlQuery")
@patch("sharepoint_rest_api.builders.camlquery_builder.ViewScope")
def test_camlquery_builder_get_query(mock_view_scope, mock_caml_query):
    mock_view_scope.RecursiveAll = "RecursiveAll"
    mock_parsed = MagicMock()
    mock_caml_query.parse.return_value = mock_parsed

    builder = CamlQueryBuilder({"name": "val"})
    result = builder.get_query()

    mock_caml_query.parse.assert_called_once()
    call_arg = mock_caml_query.parse.call_args[0][0]
    assert '<Eq><FieldRef Name="Name" /><Value Type="Text">val</Value></Eq>' in call_arg
    assert result == mock_parsed


def test_querystring_builder_init_default():
    builder = QueryStringBuilder()
    assert builder.filters == {}


def test_querystring_builder_init_with_filters():
    builder = QueryStringBuilder({"name": "toro"})
    assert builder.filters == {"name": "toro"}


def test_querystring_builder_get_filter_querystring_empty():
    assert QueryStringBuilder().get_filter_querystring() == ""


def test_querystring_builder_get_filter_querystring_eq():
    result = QueryStringBuilder({"name": "toro"}).get_filter_querystring()
    assert result == "Name eq 'toro'"


def test_querystring_builder_get_filter_querystring_not():
    result = QueryStringBuilder({"name__not": "toro"}).get_filter_querystring()
    assert result == "Name ne 'toro'"


def test_querystring_builder_get_filter_querystring_contains():
    result = QueryStringBuilder({"name__contains": "tor"}).get_filter_querystring()
    assert result == "substringof('tor', Name)"


def test_querystring_builder_get_filter_querystring_contains_multi():
    result = QueryStringBuilder({"name__contains": "tor,loc"}).get_filter_querystring()
    assert result == "substringof('tor', Name) or substringof('loc', Name)"


def test_querystring_builder_get_filter_querystring_gte():
    result = QueryStringBuilder({"date__gte": "2020-01-01"}).get_filter_querystring()
    assert result == "Date ge datetime'2020-01-01T00:00:00Z'"


def test_querystring_builder_get_filter_querystring_gt():
    result = QueryStringBuilder({"date__gt": "2020-01-01"}).get_filter_querystring()
    assert result == "Date gt datetime'2020-01-01T00:00:00Z'"


def test_querystring_builder_get_filter_querystring_lte():
    result = QueryStringBuilder({"date__lte": "2020-01-01"}).get_filter_querystring()
    assert result == "Date le datetime'2020-01-01T00:00:00Z'"


def test_querystring_builder_get_filter_querystring_lt():
    result = QueryStringBuilder({"date__lt": "2020-01-01"}).get_filter_querystring()
    assert result == "Date lt datetime'2020-01-01T00:00:00Z'"


def test_querystring_builder_get_filter_querystring_multi_value():
    result = QueryStringBuilder({"name": "a,b"}).get_filter_querystring()
    assert result == "(Name eq 'a' or Name eq 'b')"


def test_querystring_builder_get_filter_querystring_single_value():
    result = QueryStringBuilder({"name": "a"}).get_filter_querystring()
    assert result == "Name eq 'a'"


def test_querystring_builder_get_filter_querystring_unknown_operator():
    result = QueryStringBuilder({"name__unknown": "val"}).get_filter_querystring()
    assert result == "Name eq 'val'"


def test_querystring_builder_get_querystring_empty():
    assert QueryStringBuilder().get_querystring() == ""


def test_querystring_builder_get_querystring_with_filters():
    assert QueryStringBuilder({"name": "toro"}).get_querystring() == "Name eq 'toro'"


def test_search_request_builder_init_default():
    builder = SearchRequestBuilder()
    assert builder.search is None
    assert builder.filters == {}
    assert builder.select is None
    assert builder.order_by is None
    assert builder.source_id is None
    assert builder.start_row is None


def test_search_request_builder_init_with_all_params():
    builder = SearchRequestBuilder(
        search="test",
        filters={"a": "b"},
        select=["prop1"],
        order_by="created",
        source_id="src123",
        start_row=0,
    )
    assert builder.search == "test"
    assert builder.filters == {"a": "b"}
    assert builder.select == ["prop1"]
    assert builder.order_by == "created"
    assert builder.source_id == "src123"
    assert builder.start_row == 0


def test_search_request_builder_get_select_properties_none():
    assert SearchRequestBuilder().get_select_properties() is None


def test_search_request_builder_get_select_properties_list():
    builder = SearchRequestBuilder(select=["a", "b"])
    assert builder.get_select_properties() == ["a", "b"]


def test_search_request_builder_get_order_by_none():
    assert SearchRequestBuilder().get_order_by() is None


@patch("sharepoint_rest_api.builders.search_request_builder.Sort")
def test_search_request_builder_get_order_by_ascending(mock_sort):
    SearchRequestBuilder(order_by="created").get_order_by()
    mock_sort.assert_called_once_with("Created", 0)


@patch("sharepoint_rest_api.builders.search_request_builder.Sort")
def test_search_request_builder_get_order_by_descending(mock_sort):
    SearchRequestBuilder(order_by="-created").get_order_by()
    mock_sort.assert_called_once_with("Created", 1)


@patch("sharepoint_rest_api.builders.search_request_builder.Sort")
def test_search_request_builder_get_order_by_multi(mock_sort):
    SearchRequestBuilder(order_by="created,-name").get_order_by()
    assert mock_sort.call_count == 2
    mock_sort.assert_any_call("Created", 0)
    mock_sort.assert_any_call("Name", 1)


def test_search_request_builder_get_query_no_filters_no_search():
    assert SearchRequestBuilder().get_query() == "*"


def test_search_request_builder_get_query_no_filters_with_search():
    assert SearchRequestBuilder(search="humanitarian").get_query() == "humanitarian"


def test_search_request_builder_get_query_eq():
    result = SearchRequestBuilder(filters={"Name": "toro"}).get_query()
    assert result == 'Name:"toro"'


def test_search_request_builder_get_query_not():
    result = SearchRequestBuilder(filters={"Name__not": "toro"}).get_query()
    assert result == 'Name<>"toro"'


def test_search_request_builder_get_query_not_in_single():
    result = SearchRequestBuilder(filters={"Name__not_in": "toro"}).get_query()
    assert result == 'Name:(-"toro")'


def test_search_request_builder_get_query_not_in_multi():
    result = SearchRequestBuilder(filters={"Name__not_in": "toro,capri"}).get_query()
    assert result == 'Name:(-"toro" -"capri")'


def test_search_request_builder_get_query_between():
    result = SearchRequestBuilder(filters={"Date__between": "2019-01-01__2020-01-01"}).get_query()
    assert result == "Date:2019-01-01..2020-01-01"


def test_search_request_builder_get_query_contains():
    result = SearchRequestBuilder(filters={"Name__contains": "tor"}).get_query()
    assert result == 'Name:"tor*"'


def test_search_request_builder_get_query_gte():
    result = SearchRequestBuilder(filters={"Date__gte": "2020-01-01"}).get_query()
    assert result == 'Date>="2020-01-01"'


def test_search_request_builder_get_query_gt():
    result = SearchRequestBuilder(filters={"Date__gt": "2020-01-01"}).get_query()
    assert result == 'Date>"2020-01-01"'


def test_search_request_builder_get_query_lte():
    result = SearchRequestBuilder(filters={"Date__lte": "2020-01-01"}).get_query()
    assert result == 'Date<="2020-01-01"'


def test_search_request_builder_get_query_lt():
    result = SearchRequestBuilder(filters={"Date__lt": "2020-01-01"}).get_query()
    assert result == 'Date<"2020-01-01"'


def test_search_request_builder_get_query_multi_value_or():
    result = SearchRequestBuilder(filters={"Name": "toro,capri"}).get_query()
    assert result == 'Name:("toro" OR "capri")'


def test_search_request_builder_get_query_single_value():
    result = SearchRequestBuilder(filters={"Name": "toro"}).get_query()
    assert result == 'Name:"toro"'


def test_search_request_builder_get_query_unknown_operator():
    result = SearchRequestBuilder(filters={"Name__custom": "val"}).get_query()
    assert result == 'Name:"val"'


def test_search_request_builder_get_query_multiple_filters():
    result = SearchRequestBuilder(filters={"FileType": "pdf", "Title__contains": "Humanitarian"}).get_query()
    assert " AND " in result
    assert 'FileType:"pdf"' in result
    assert 'Title:"Humanitarian*"' in result


def test_search_request_builder_get_query_search_with_filters():
    result = SearchRequestBuilder(search="test", filters={"Name": "toro"}).get_query()
    assert result == 'test Name:"toro"'


def test_search_request_builder_get_query_all_operators():
    result = SearchRequestBuilder(
        filters={
            "Name": "toro",
            "Title__contains": "help",
            "Date__gt": "2020-01-01",
            "Amount__gte": "100",
            "Date__lt": "2020-12-31",
            "Amount__lte": "500",
            "Status__not": "closed",
            "Tag__not_in": "old,archived",
            "Range__between": "1__10",
        }
    ).get_query()
    assert 'Name:"toro"' in result
    assert 'Title:"help*"' in result
    assert 'Date>"2020-01-01"' in result
    assert 'Amount>="100"' in result
    assert 'Date<"2020-12-31"' in result
    assert 'Amount<="500"' in result
    assert 'Status<>"closed"' in result
    assert 'Tag:(-"old" -"archived")' in result
    assert "Range:1..10" in result
    assert result.count(" AND ") == 8


@patch("sharepoint_rest_api.builders.search_request_builder.Sort")
@patch("sharepoint_rest_api.builders.search_request_builder.config")
def test_search_request_builder_build_all_params(mock_config, mock_sort):
    mock_config.SHAREPOINT_PAGE_SIZE = 25
    mock_sort.return_value = mock_sort

    builder = SearchRequestBuilder(
        search="test",
        filters={"Name": "toro"},
        select=["prop1"],
        order_by="created",
        source_id="src123",
        start_row=10,
    )
    result = builder.build()

    assert result == {
        "query_text": 'test Name:"toro"',
        "sort_list": [mock_sort],
        "select_properties": ["prop1"],
        "start_row": 10,
        "row_limit": 25,
        "trim_duplicates": False,
        "SourceId": "src123",
    }


@patch("sharepoint_rest_api.builders.search_request_builder.Sort")
@patch("sharepoint_rest_api.builders.search_request_builder.config")
def test_search_request_builder_build_defaults(mock_config, mock_sort):
    mock_config.SHAREPOINT_PAGE_SIZE = 50

    builder = SearchRequestBuilder()
    result = builder.build()

    assert result["query_text"] == "*"
    assert result["sort_list"] is None
    assert result["select_properties"] is None
    assert result["start_row"] is None
    assert result["row_limit"] == 50
    assert result["trim_duplicates"] is False
    assert result["SourceId"] is None
