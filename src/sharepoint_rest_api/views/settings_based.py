from django.core.cache import caches
from django.utils.functional import cached_property
from rest_framework.exceptions import PermissionDenied

from sharepoint_rest_api import config
from sharepoint_rest_api.client import SharePointClient, SharePointClientException
from sharepoint_rest_api.models import SharePointLibrary
from sharepoint_rest_api.serializers.sharepoint import SharePointSettingsSerializer
from sharepoint_rest_api.views.base import (
    AbstractSharePointViewSet,
    CamlQuerySharePointViewSet,
    FileSharePointViewSet,
    RestQuerySharePointViewSet,
    SharePointSearchViewSet,
)

cache = caches['default']


class SettingsBasedSharePointViewSet(AbstractSharePointViewSet):
    """
    Base viewset for settings based mode
    """

    def is_public(self):
        return SharePointLibrary.objects.filter(name=self.folder, public=True)

    @property
    def tenant(self):
        return config.SHAREPOINT_TENANT

    @property
    def site(self):
        return config.SHAREPOINT_SITE

    @property
    def folder(self):
        return self.kwargs.get('folder', 'Documents')

    @property
    def site_type(self):
        return config.SHAREPOINT_SITE_TYPE

    @cached_property
    def client(self):
        dl_info = {
            'url': f'{self.tenant}/{self.site_type}/{self.site}',
            'relative_url': f'{self.site_type}/{self.site}',
            'folder': self.folder
        }
        try:
            client = SharePointClient(**dl_info)
        except SharePointClientException:
            raise PermissionDenied

        return client


class SharePointSettingsRestViewSet(SettingsBasedSharePointViewSet, RestQuerySharePointViewSet):
    """
    Viewset for SharePoint Rest (settings based)
    """
    serializer_class = SharePointSettingsSerializer


class SharePointSettingsCamlViewSet(SettingsBasedSharePointViewSet, CamlQuerySharePointViewSet):
    """
    Viewset for SharePoint Caml (settings based)
    """
    serializer_class = SharePointSettingsSerializer


class SharePointSettingsFileViewSet(FileSharePointViewSet, SettingsBasedSharePointViewSet):
    """
    Viewset for SharePoint File metadata (settings based)
    """


class SharePointSettingsSearchViewSet(SharePointSearchViewSet, SettingsBasedSharePointViewSet):
    """
    Viewset for SharePoint Search (settings based)
    """
