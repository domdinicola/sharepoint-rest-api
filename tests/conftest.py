import os
import tempfile

from rest_framework.test import APIClient

import pytest

from tests.factories import UserFactory


def pytest_configure(config):
    # enable this to remove deprecations
    os.environ['CELERY_TASK_ALWAYS_EAGER'] = "1"
    os.environ['SHAREPOINT_CONNECTION'] = "user"
    os.environ['STATIC_ROOT'] = tempfile.gettempdir()


@pytest.fixture()
def client(user):
    client = APIClient()
    client.force_authenticate(user)
    return client


@pytest.fixture()
def user(request, db):
    return UserFactory()


@pytest.fixture()
def logged_user(client, user):
    client.force_authenticate(user)
    return user


# @pytest.fixture()
# def group():
#     return GroupFactory()
