import datetime

from drf_api_checker.recorder import Recorder
from rest_framework.response import Response
from rest_framework.test import APIClient

from tests.factories import UserFactory


class LastModifiedRecorder(Recorder):

    @property
    def client(self):
        user = UserFactory(is_superuser=True)
        client = APIClient()
        client.force_authenticate(user)
        return client

    def assert_modified(self, response: Response, stored: Response, path: str):
        value = response['modified']
        assert datetime.datetime.strptime(value, '%Y-%m-%dT%H:%M:%S.%f%z')

    def assert_created(self, response: Response, stored: Response, path: str):
        value = response['created']
        assert datetime.datetime.strptime(value, '%Y-%m-%dT%H:%M:%S.%f%z')


class ExpectedErrorRecorder(Recorder):
    expect_errors = True
