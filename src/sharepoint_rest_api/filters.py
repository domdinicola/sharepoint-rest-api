from django_filters import rest_framework as filters

from sharepoint_rest_api.models import SharePointLibrary


class SharePointLibraryFilter(filters.FilterSet):

    class Meta:
        model = SharePointLibrary
        fields = {
            'site': ['exact', 'in'],
            'active': ['exact', ],
        }
