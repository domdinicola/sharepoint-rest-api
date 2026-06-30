from django.utils.functional import cached_property

from sharepoint_rest_api import config
from sharepoint_rest_api.graph_client import GraphClient, GraphClientError
from sharepoint_rest_api.views.base import SharePointSearchViewSet

from rest_framework.exceptions import PermissionDenied


class GraphBasedSearchViewSet(SharePointSearchViewSet):
    """ViewSet that uses Microsoft Graph Search API instead of SharePoint Search API."""

    @cached_property
    def client(self):
        try:
            return GraphClient(
                url=f"{config.SHAREPOINT_TENANT}/{config.SHAREPOINT_SITE_TYPE}/{config.SHAREPOINT_SITE}",
                relative_url=f"{config.SHAREPOINT_SITE_TYPE}/{config.SHAREPOINT_SITE}",
                folder=self.folder,
            )
        except GraphClientError:
            raise PermissionDenied
