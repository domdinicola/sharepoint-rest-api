# to regenerate cassettes
# comment the mock_client fixture (since is mocking the login)
from pathlib import Path

from drf_api_checker.pytest import frozenfixture

from pytest import fixture
from unittest import mock

from sharepoint_rest_api.client import SharePointClient
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


@fixture()
def sh_client(library, request, db):
    dl_info = {
        'url': library.site.site_url(),
        'relative_url': library.site.relative_url(),
        'folder': library.name
    }
    return SharePointClient(**dl_info)


@fixture(scope='session', autouse=True)
def mock_client():
    patcher = mock.patch('office365.runtime.auth.authentication_context.AuthenticationContext')
    my_mock = patcher.start()
    my_mock.acquire_token.return_value = True
    yield
    patcher.stop()  # not needed just for clarity


@VCR.use_cassette(str(Path(__file__).parent / 'vcr_cassettes/client/folders.yml'))
def test_folders(library, sh_client, mock_client):
    items = sh_client.read_folders(library.name)
    assert len(items) == 100


@VCR.use_cassette(str(Path(__file__).parent / 'vcr_cassettes/client/items.yml'))
def test_items(sh_client, mock_client):
    items = sh_client.read_items()
    assert len(items) == 56


@VCR.use_cassette(str(Path(__file__).parent / 'vcr_cassettes/client/caml_items.yml'))
def test_caml_items(sh_client, mock_client):
    items = sh_client.read_caml_items()
    assert len(items) == 56


@VCR.use_cassette(str(Path(__file__).parent / 'vcr_cassettes/client/files.yml'))
def test_files(sh_client, mock_client):
    items = sh_client.read_files()
    assert len(items) == 56
