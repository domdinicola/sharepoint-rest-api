
import pytest

from sharepoint_rest_api.builders.querystring_builder import QueryStringBuilder


@pytest.mark.parametrize("filters,expected", [
    (dict(), ''),
    ({'name': 'toro'}, "Name eq 'toro'"),
    ({'name__not': 'toro'}, "Name ne 'toro'"),
    ({'name__contains': 'toro'}, "substringof('toro', Name)"),
    ({'name': 'toro,loco'}, "(Name eq 'toro' or Name eq 'loco')"),
    ({'date__gt': '2019-10-10'}, "Date gt datetime'2019-10-10T00:00:00Z'"),
    ({'date__gte': '2019-10-10'}, "Date ge datetime'2019-10-10T00:00:00Z'"),
    ({'date__lt': '2019-10-10'}, "Date lt datetime'2019-10-10T00:00:00Z'"),
    ({'date__lte': '2019-10-10'}, "Date le datetime'2019-10-10T00:00:00Z'"),
])
def test_no_querystring(filters, expected):
    qs = QueryStringBuilder(filters).get_querystring()
    assert qs == expected
