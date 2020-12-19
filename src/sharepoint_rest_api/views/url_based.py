from django.core.cache import caches
from django.utils.functional import cached_property
from rest_framework.exceptions import PermissionDenied

from sharepoint_rest_api.client import SharePointClient, SharePointClientException
from sharepoint_rest_api.models import SharePointLibrary
from sharepoint_rest_api.serializers.sharepoint import SharePointUrlSerializer
from sharepoint_rest_api.views.base import (
    AbstractSharePointViewSet,
    CamlQuerySharePointViewSet,
    FileSharePointViewSet,
    RestQuerySharePointViewSet,
    SharePointSearchViewSet,
)

cache = caches['default']


class UrlBasedSharePointViewSet(AbstractSharePointViewSet):
    """
    Base viewset for URL based mode
    """

    def get_library(self):
        return SharePointLibrary.objects.get(
            site__tenant__url__contains=self.tenant, site__name=self.site, name=self.folder)

    def is_public(self):
        return self.get_library().public

    @property
    def tenant(self):
        return self.kwargs.get('tenant')

    @property
    def site(self):
        return self.kwargs.get('site')

    @property
    def folder(self):
        return self.kwargs.get('folder')

    @cached_property
    def client(self):
        dl = self.get_library()
        dl_info = {
            'url': dl.site.site_url(),
            'relative_url': dl.site.relative_url(),
            'folder': dl.name
        }
        if dl.site.tenant.username:
            dl_info['username'] = dl.site.tenant.username
            dl_info['password'] = dl.site.tenant.password
        try:
            client = SharePointClient(**dl_info)
        except SharePointClientException:
            raise PermissionDenied

        return client


class SharePointUrlRestViewSet(RestQuerySharePointViewSet, UrlBasedSharePointViewSet):
    """
    Viewset for SharePoint Rest (URL based)
    """
    serializer_class = SharePointUrlSerializer


class SharePointUrlCamlViewSet(CamlQuerySharePointViewSet, UrlBasedSharePointViewSet):
    """
    Viewset for SharePoint Caml (URL based)
    """
    serializer_class = SharePointUrlSerializer


class SharePointUrlFileViewSet(FileSharePointViewSet, UrlBasedSharePointViewSet):
    """
    Viewset for SharePoint File metadata (URL based)
    """


class SharePointUrlSearchViewSet(SharePointSearchViewSet, UrlBasedSharePointViewSet):
    """
    Viewset for SharePoint Search (URL based)
    """
