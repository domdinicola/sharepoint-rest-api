from django.conf import settings
from rest_framework import serializers
from rest_framework.reverse import reverse

from sharepoint_rest_api.serializers.fields import (
    CapitalizeSearchSharePointField,
    RawSearchSharePointField,
    SearchSharePointField,
    SharePointPropertyField,
    UpperSharePointPropertyField,
)


class BaseSharePointItemSerializer(serializers.Serializer):

    id = UpperSharePointPropertyField()
    guid = UpperSharePointPropertyField()
    created = SharePointPropertyField()
    modified = SharePointPropertyField()
    title = SharePointPropertyField()
    url = SharePointPropertyField()
    resource_url = serializers.ReadOnlyField()
    download_url = serializers.SerializerMethodField()
    file_leaf_ref = SharePointPropertyField()
    file_ref = SharePointPropertyField()


class SharePointSettingsSerializer(BaseSharePointItemSerializer):
    def get_download_url(self, obj):
        filename = obj.properties.get('FileLeafRef', obj.properties.get('Title', ''))
        if filename:
            k = filename.rfind(".")
            if k > 0:
                filename = filename[:k] + "." + filename[k + 1:]
            else:
                filename = f'{filename}.pdf'
        relative_url = reverse('sharepoint_rest_api:sharepoint-settings-files-download', kwargs={
            'folder': self.context['folder'],
            'filename': filename
        })
        return f'{settings.HOST}{relative_url}'


class SharePointUrlSerializer(BaseSharePointItemSerializer):
    def get_download_url(self, obj):
        filename = obj.properties.get('FileLeafRef', obj.properties.get('Title', ''))
        if filename:
            k = filename.rfind(".")
            if k > 0:
                filename = filename[:k] + "." + filename[k + 1:]
            else:
                filename = f'{filename}.pdf'
        relative_url = reverse('sharepoint_rest_api:sharepoint-url-files-download', kwargs={
            'tenant': self.context['tenant'],
            'site': self.context['site'],
            'folder': self.context['folder'],
            'filename': filename
        })
        return f'{settings.HOST}{relative_url}'


class SharePointFileSerializer(serializers.Serializer):
    name = SharePointPropertyField()
    type_name = serializers.ReadOnlyField()
    url = serializers.ReadOnlyField()
    linking_uri = SharePointPropertyField()
    server_relative_url = SharePointPropertyField()
    unique_id = SharePointPropertyField()
    title = SharePointPropertyField()
    time_created = SharePointPropertyField()
    time_last_modified = SharePointPropertyField()

    def get_download_url(self, obj):
        relative_url = reverse('sharepoint_rest_api:sharepoint-files-download', kwargs={
            'tenant': self.context['tenant'],
            'site': self.context['site'],
            'folder': self.context['folder'],
            'filename': obj.properties['Name'].split('.')[0]})
        return f'{settings.HOST}{relative_url}'


class SharePointSearchSerializer(serializers.Serializer):

    rank = SearchSharePointField()
    doc_id = SearchSharePointField()
    work_id = SearchSharePointField()
    title = SearchSharePointField()
    author = SearchSharePointField()
    size = SearchSharePointField()
    path = SearchSharePointField()
    description = SearchSharePointField()
    write = SearchSharePointField()
    last_modified_time = SearchSharePointField()
    collapsing_status = SearchSharePointField()
    hit_highlighted_summary = SearchSharePointField()
    hit_highlighted_properties = SearchSharePointField()
    file_extension = SearchSharePointField()
    content_type_id = SearchSharePointField()
    parent_link = SearchSharePointField()
    views_life_time = SearchSharePointField()
    views_recent = SearchSharePointField()
    section_names = SearchSharePointField()
    section_indexes = SearchSharePointField()
    site_logo = SearchSharePointField()
    site_description = SearchSharePointField()
    site_name = SearchSharePointField()
    is_document = SearchSharePointField()
    file_type = SearchSharePointField()
    is_container = SearchSharePointField()
    web_template = SearchSharePointField()
    secondary_file_extension = SearchSharePointField()
    unique_id = SearchSharePointField()
    prog_id = SearchSharePointField()
    linking_url = SearchSharePointField()
    site_id = SearchSharePointField()
    web_id = SearchSharePointField()
    original_path = SearchSharePointField()
    result_type_id_list = SearchSharePointField()
    result_type_id = SearchSharePointField()
    render_template_id = SearchSharePointField()
    partition_id = SearchSharePointField()
    url_zone = SearchSharePointField()
    culture = SearchSharePointField()
    geo_location_source = SearchSharePointField()

    contentclass = RawSearchSharePointField()
    deeplinks = RawSearchSharePointField()
    importance = RawSearchSharePointField()
    docaclmeta = RawSearchSharePointField()

    pictureThumbnailURL = CapitalizeSearchSharePointField()
    serverRedirectedURL = CapitalizeSearchSharePointField()
    serverRedirectedEmbedURL = CapitalizeSearchSharePointField()
    serverRedirectedPreviewURL = CapitalizeSearchSharePointField()
    sPWebUrl = CapitalizeSearchSharePointField()
