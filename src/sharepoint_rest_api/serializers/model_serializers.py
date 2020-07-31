from django.conf import settings
from rest_framework import serializers
from rest_framework.reverse import reverse

from sharepoint_rest_api.models import SharePointLibrary, SharePointSite, SharePointTenant


class SharePointTenantSerializer(serializers.ModelSerializer):
    class Meta:
        model = SharePointTenant
        exclude = ('username', 'password')


class SharePointSiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = SharePointSite
        fields = '__all__'


class SharePointLibrarySerializer(serializers.ModelSerializer):
    site_name = serializers.ReadOnlyField(source='site.name')
    api_url = serializers.SerializerMethodField()

    def get_api_url(self, obj):
        reverse_url = reverse('sharepoint_rest_api:sharepoint-url-rest-list',
                              kwargs={'tenant': obj.site.tenant.name, 'site': obj.site.name, 'folder': obj.name})
        return settings.HOST + reverse_url

    class Meta:
        model = SharePointLibrary
        fields = ('name', 'site_name', 'active', 'library_url', 'api_url')
