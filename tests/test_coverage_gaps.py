import pytest
from rest_framework.fields import SkipField

from sharepoint_rest_api.builders.camlquery_builder import CamlQueryBuilder, recursive_builder
from sharepoint_rest_api.builders.rest_builder import RestBuilder
from sharepoint_rest_api.models import SharePointLibrary, SharePointSite, SharePointTenant
from sharepoint_rest_api.serializers.fields import (
    CapitalizeSearchSharePointField,
    RawSearchSharePointField,
    SearchSharePointField,
    SharePointPropertyManyField,
    UpperSharePointPropertyField,
)
from sharepoint_rest_api.serializers.sharepoint import (
    SharePointSettingsSerializer,
    SharePointUrlSerializer,
)
from sharepoint_rest_api.utils import first_upper, get_cache_key


# ---- utils.py coverage (line 18: first_upper empty string) ----


def test_first_upper_empty():
    assert first_upper("") == ""


# ---- models.py coverage (lines 51, 79: __str__) ----


@pytest.mark.django_db
def test_sharepoint_site_str():
    tenant = SharePointTenant.objects.create(url="https://contoso.sharepoint.com")
    site = SharePointSite.objects.create(tenant=tenant, name="MySite")
    assert str(site) == "https://contoso.sharepoint.com (MySite)"


@pytest.mark.django_db
def test_sharepoint_library_str():
    tenant = SharePointTenant.objects.create(url="https://contoso.sharepoint.com")
    site = SharePointSite.objects.create(tenant=tenant, name="MySite")
    lib = SharePointLibrary.objects.create(name="Documents", site=site)
    assert str(lib) == "Documents (MySite) [https://contoso.sharepoint.com]"


# ---- camlquery_builder.py line 83 coverage ----


def test_caml_create_query_multiple_filters():
    result = CamlQueryBuilder(filters={"Donor": "Red Cross", "Status": "Final"}).create_query()
    assert "<And>" in result


def test_caml_recursive_builder_empty():
    assert recursive_builder([]) == ""


def test_caml_recursive_builder_single():
    assert recursive_builder(["<Eq>...</Eq>"]) == "<Eq>...</Eq>"


def test_caml_recursive_builder_double():
    result = recursive_builder(["<A>1</A>", "<A>2</A>"])
    assert "And" in result
    assert "<A>2</A>" in result
    assert "<A>1</A>" in result


def test_caml_recursive_builder_triple():
    result = recursive_builder(["<A>1</A>", "<A>2</A>", "<A>3</A>"])
    assert "And" in result
    assert "<A>3</A>" in result


# ---- serializers/fields.py coverage ----


def test_upper_property_field_super_fallback():
    field = UpperSharePointPropertyField(source="uuid")
    with pytest.raises(SkipField):
        field.get_attribute({"not_uuid": "val"})


def test_property_many_field_with_values():
    field = SharePointPropertyManyField(source="donors")
    result = field.get_attribute({"Donors": "Red Cross; UNICEF"})
    assert result == ["Red Cross", "UNICEF"]


def test_property_many_field_super_fallback():
    field = SharePointPropertyManyField(source="donors")
    with pytest.raises(SkipField):
        field.get_attribute({"Other": "val"})


def test_raw_search_field_missing_key():
    field = RawSearchSharePointField(source="missing_field")
    result = field.get_attribute({"other": "val"})
    assert result == "N/A"


def test_search_field_missing_key():
    field = SearchSharePointField(source="last_name")
    result = field.get_attribute({"other": "val"})
    assert result == "N/A"


def test_capitalize_search_field_missing_key():
    field = CapitalizeSearchSharePointField(source="example")
    result = field.get_attribute({"other": "val"})
    assert result == "N/A"


# ---- serializers/sharepoint.py coverage ----


def test_sharepoint_settings_serializer_empty_filename():
    data = {"FileLeafRef": "", "Title": ""}
    serializer = SharePointSettingsSerializer(data=data, context={"folder": "docs"})
    assert serializer.is_valid()


def test_sharepoint_settings_serializer_no_dot():
    data = {"FileLeafRef": "report", "Title": "Report"}
    serializer = SharePointSettingsSerializer(data=data, context={"folder": "docs"})
    assert serializer.is_valid()


def test_sharepoint_url_serializer_empty_filename():
    data = {"FileLeafRef": "", "Title": ""}
    serializer = SharePointUrlSerializer(
        data=data,
        context={"tenant": "t", "site": "s", "folder": "docs"},
    )
    assert serializer.is_valid()


def test_sharepoint_url_serializer_no_dot():
    data = {"FileLeafRef": "report", "Title": "Report"}
    serializer = SharePointUrlSerializer(
        data=data,
        context={"tenant": "t", "site": "s", "folder": "docs"},
    )
    assert serializer.is_valid()


# ---- rest_builder.py coverage (build_kql exclusion filter) ----


def test_kql_exclusion_filter():
    result = RestBuilder.build_kql(filters={"-Donor": "Red Cross"})
    assert result == '-Donor:"Red Cross"'


# ---- utils.py get_cache_key coverage ----


def test_get_cache_key_with_args():
    key = get_cache_key(("foo", "bar"), key1="val1")
    assert isinstance(key, int)
