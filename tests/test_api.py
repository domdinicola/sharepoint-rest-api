from pathlib import Path

from django.urls import reverse
from drf_api_checker.pytest import api_checker_datadir, contract, frozenfixture  # noqa
from drf_api_checker.recorder import Recorder

import pytest

from tests.api_checker import LastModifiedRecorder
from tests.factories import SharePointLibraryFactory, SharePointSiteFactory, SharePointTenantFactory
from tests.vcrpy import VCR


@frozenfixture()
def tenant(request, db):
    return SharePointTenantFactory(
        url='https://unitst.sharepoint.com/',
        username=None,
        password=None
    )


@frozenfixture()
def site(tenant, request, db):
    return SharePointSiteFactory(
        tenant=tenant,
        name='GLB-DRP',
        site_type='sites',
    )


@frozenfixture()
def library(site, request, db):
    return SharePointLibraryFactory(
        site=site,
        name='2020 Certified Reports'
    )


@pytest.mark.django_db
@contract(LastModifiedRecorder)
def test_api_sharepoint_tenants(request, django_app, library):
    return reverse('sharepoint_rest_api:sharepoint-tenant-list')


@pytest.mark.django_db
@contract(LastModifiedRecorder)
def test_api_sharepoint_sites(request, django_app, site):
    return reverse('sharepoint_rest_api:sharepoint-site-list')


@pytest.mark.django_db
@contract(LastModifiedRecorder)
def test_api_sharepoint_libraries(request, django_app, library):
    return reverse('sharepoint_rest_api:sharepoint-library-list')


@VCR.use_cassette(str(Path(__file__).parent / 'vcr_cassettes/api/list.yml'))
def test_api(api_checker_datadir, logged_user, library):  # noqa
    kwargs = {'tenant': library.site.tenant.name, 'site': library.site.name, 'folder': library.name}
    url = reverse('sharepoint_rest_api:sharepoint-url-rest-list', kwargs=kwargs)
    recorder = Recorder(api_checker_datadir, as_user=logged_user)
    recorder.assertGET(url)


@VCR.use_cassette(str(Path(__file__).parent / 'vcr_cassettes/api/caml-list.yml'))
def test_api_caml(api_checker_datadir, logged_user, library):  # noqa
    kwargs = {'tenant': library.site.tenant.name, 'site': library.site.name, 'folder': library.name}
    url = reverse('sharepoint_rest_api:sharepoint-url-caml-list', kwargs=kwargs)
    recorder = Recorder(api_checker_datadir, as_user=logged_user)
    recorder.assertGET(url)


@VCR.use_cassette(str(Path(__file__).parent / 'vcr_cassettes/api/simple-list.yml'))
def test_settings_api(api_checker_datadir, logged_user, library):  # noqa
    kwargs = {'folder': library.name}
    url = reverse('sharepoint_rest_api:sharepoint-settings-rest-list', kwargs=kwargs)
    recorder = Recorder(api_checker_datadir, as_user=logged_user)
    recorder.assertGET(url)


@VCR.use_cassette(str(Path(__file__).parent / 'vcr_cassettes/api/simple-caml-list.yml'))
def test_settings_api_caml(api_checker_datadir, logged_user, library):  # noqa
    kwargs = {'folder': library.name}
    url = reverse('sharepoint_rest_api:sharepoint-settings-caml-list', kwargs=kwargs)
    recorder = Recorder(api_checker_datadir, as_user=logged_user)
    recorder.assertGET(url)
