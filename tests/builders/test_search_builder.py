import pytest

from sharepoint_rest_api.builders.search_request_builder import SearchRequestBuilder


@pytest.mark.parametrize("filters,expected", [
    (dict(), '*'),
    ({'Name': 'toro'}, "Name:toro"),
    ({'Name__not': 'toro'}, "Name<>toro"),
    ({'Name__contains': 'toro'}, "Name:toro*"),
    ({'Name': 'toro,loco'}, "Name:(toro OR loco)"),
    ({'Date__gt': '2019-10-10'}, "Date>2019-10-10"),
    ({'Date__gte': '2019-10-10'}, "Date>=2019-10-10"),
    ({'Date__lt': '2019-10-10'}, "Date<2019-10-10"),
    ({'Date__lte': '2019-10-10'}, "Date<=2019-10-10"),
    ({'Date__between': '2019-10-10__2020-10-10'}, "Date:2019-10-10..2020-10-10"),
    ({'FileType': 'pdf', 'Title__contains': 'Humanitarian', 'LastModifiedTime__gte': '2019-10-10'},
     "FileType:pdf AND Title:Humanitarian* AND LastModifiedTime>=2019-10-10"),
])
def test_no_querystring(filters, expected):
    qs = SearchRequestBuilder(filters).get_query()
    assert qs == expected
