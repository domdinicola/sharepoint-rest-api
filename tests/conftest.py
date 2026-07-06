import os
import tempfile
from unittest import mock

from rest_framework.test import APIClient

import pytest

from sharepoint_rest_api.graph_client import _scan_cache
from tests.factories import UserFactory


@pytest.fixture(autouse=True)
def _clear_scan_cache():
    _scan_cache.clear()


@pytest.fixture(scope="session", autouse=True)
def _mock_sharepoint_auth():
    patcher = mock.patch("office365.runtime.auth.authentication_context.AuthenticationContext.authenticate_request")
    patcher.start()
    yield
    patcher.stop()


def pytest_configure(config):
    # enable this to remove deprecations
    os.environ["CELERY_TASK_ALWAYS_EAGER"] = "1"
    os.environ["SHAREPOINT_CONNECTION"] = "user"
    os.environ["STATIC_ROOT"] = tempfile.gettempdir()


@pytest.fixture
def client(user):
    client = APIClient()
    client.force_authenticate(user)
    return client


@pytest.fixture
def user(request, db):
    return UserFactory()


@pytest.fixture
def logged_user(client, user):
    client.force_authenticate(user)
    return user
