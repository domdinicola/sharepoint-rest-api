import pytest

from sharepoint_rest_api.builders.search_request_builder import SearchRequestBuilder


@pytest.mark.parametrize("filters,expected", [
    (dict(), '*'),
    ({'name': 'toro'}, "Name:toro"),
    ({'name__not': 'toro'}, "Name<>toro"),
    ({'name__contains': 'toro'}, "Name:toro*"),
    ({'name': 'toro,loco'}, "Name:(toro OR loco)"),
    ({'date__gt': '2019-10-10'}, "Date>2019-10-10"),
    ({'date__gte': '2019-10-10'}, "Date>=2019-10-10"),
    ({'date__lt': '2019-10-10'}, "Date<2019-10-10"),
    ({'date__lte': '2019-10-10'}, "Date<=2019-10-10"),
    ({'date__between': '2019-10-10__2020-10-10'}, "Date:2019-10-10..2020-10-10"),
    ({'file_type': 'pdf', 'title__contains': 'Humanitarian', 'last_modified_time__gte': '2019-10-10'},
     "FileType:pdf AND Title:Humanitarian* AND LastModifiedTime>=2019-10-10"),
])
def test_no_querystring(filters, expected):
    qs = SearchRequestBuilder(filters).get_query()
    assert qs == expected
