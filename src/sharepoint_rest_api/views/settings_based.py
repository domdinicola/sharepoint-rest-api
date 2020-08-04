from django.core.cache import caches
from rest_framework.exceptions import PermissionDenied

from sharepoint_rest_api import config
from sharepoint_rest_api.client import SharePointClient, SharePointClientException
from sharepoint_rest_api.models import SharePointLibrary
from sharepoint_rest_api.serializers.sharepoint import SharePointSettingsSerializer
from sharepoint_rest_api.views.base import (
    AbstractSharePointViewSet,
    CamlQuerySharePointViewSet,
    FileSharePointMixin,
    RestQuerySharePointViewSet,
    SharePointSearchViewSet,
)

cache = caches['default']


class SettingsBasedSharePointViewSet(AbstractSharePointViewSet):

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

    @property
    def client(self):
        key = self.get_cache_key(**{'client': 'client'})
        client = cache.get(key)
        if client is None:
            dl_info = {
                'url': f'{self.tenant}/{self.site_type}/{self.site}',
                'relative_url': f'{self.site_type}/{self.site}',
                'folder': self.folder
            }
            try:
                client = SharePointClient(**dl_info)
                cache.set(key, client)
            except SharePointClientException:
                raise PermissionDenied

        return client


class SharePointSettingsRestViewSet(SettingsBasedSharePointViewSet, RestQuerySharePointViewSet):
    serializer_class = SharePointSettingsSerializer


class SharePointSettingsCamlViewSet(SettingsBasedSharePointViewSet, CamlQuerySharePointViewSet):
    serializer_class = SharePointSettingsSerializer


class SharePointSettingsFileViewSet(FileSharePointMixin, SettingsBasedSharePointViewSet):
    pass


class SharePointSettingsSearchViewSet(SharePointSearchViewSet, SettingsBasedSharePointViewSet):
    pass
