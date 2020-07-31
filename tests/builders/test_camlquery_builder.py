
import pytest

from sharepoint_rest_api.builders.camlquery_builder import CamlQueryBuilder


@pytest.mark.parametrize("filters,expected", [
    (dict(), ''),
    ({'donor': 'Australia'}, '<Eq><FieldRef Name="Donor" /><Value Type="Text">Australia</Value></Eq>'),
    ({'donor__not': 'Australia'}, '<Neq><FieldRef Name="Donor" /><Value Type="Text">Australia</Value></Neq>'),
    ({'recipient_office__contains': 'Afghanistan'},
     '<Contains><FieldRef Name="RecipientOffice" /><Value Type="Text">Afghanistan</Value></Contains>'),
    ({'report_end_date__gt': '2019-10-10'},
     '<Gt><FieldRef Name="ReportEndDate" /><Value Type="DateTime">2019-10-10T00:00:00Z</Value></Gt>'),
    ({'report_end_date__gte': '2019-10-10'},
     '<Geq><FieldRef Name="ReportEndDate" /><Value Type="DateTime">2019-10-10T00:00:00Z</Value></Geq>'),
    ({'report_end_date__lt': '2019-10-10'},
     '<Lt><FieldRef Name="ReportEndDate" /><Value Type="DateTime">2019-10-10T00:00:00Z</Value></Lt>'),
    ({'report_end_date__lte': '2019-10-10'},
     '<Leq><FieldRef Name="ReportEndDate" /><Value Type="DateTime">2019-10-10T00:00:00Z</Value></Leq>'),
    ({'report_group': 'Grant,US Gov'},
     '<Or><Eq><FieldRef Name="ReportGroup" /><Value Type="Text">US Gov</Value></Eq>'
     '<Eq><FieldRef Name="ReportGroup" /><Value Type="Text">Grant</Value></Eq></Or>'),
    ({'donor': 'Australia', 'recipient_office__contains': 'Afghanistan'},
     '<And>'
     '<Contains><FieldRef Name="RecipientOffice" /><Value Type="Text">Afghanistan</Value></Contains>'
     '<Eq><FieldRef Name="Donor" /><Value Type="Text">Australia</Value></Eq>'
     '</And>'
     ),
    ({'donor': 'Australia', 'recipient_office__contains': 'Afghanistan', 'donor_report_category': 'Financial'},
     '<And>'
     '<Eq><FieldRef Name="DonorReportCategory" /><Value Type="Text">Financial</Value></Eq>'
     '<And>'
     '<Contains><FieldRef Name="RecipientOffice" /><Value Type="Text">Afghanistan</Value></Contains>'
     '<Eq><FieldRef Name="Donor" /><Value Type="Text">Australia</Value></Eq>'
     '</And>'
     '</And>'
     ),
])
def test_no_querystring(filters, expected):
    qs = CamlQueryBuilder(filters).create_query()
    assert qs == f'<View><Query><Where>{expected}</Where></Query></View>'
