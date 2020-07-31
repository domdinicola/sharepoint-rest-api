from django.core.cache import caches
from django.http import Http404, HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from office365.runtime.client_request_exception import ClientRequestException
from office365.sharepoint.files.file import File
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ErrorDetail
from rest_framework.filters import OrderingFilter, SearchFilter

from sharepoint_rest_api.serializers.sharepoint import SharePointFileSerializer, SharePointSearchSerializer
from sharepoint_rest_api.utils import get_cache_key

cache = caches['default']


class AbstractSharePointViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = None
    filter_backends = (SearchFilter, DjangoFilterBackend, OrderingFilter)
    tenant = None
    site = None
    folder = None

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx.update({
            'tenant': self.tenant,
            'site': self.site,
            'folder': self.folder
        })
        return ctx

    def handle_exception(self, exc):
        response = super().handle_exception(exc)
        if isinstance(exc, Http404):
            response.data['detail'] = ErrorDetail('No document found using selected filters', 'not_found')
        return response

    def get_cache_key(self, **kwargs):
        key = get_cache_key([self.tenant, self.site, self.folder], **kwargs)
        return key


class CamlQuerySharePointViewSet(AbstractSharePointViewSet):

    def get_queryset(self):
        kwargs = self.request.query_params.dict()
        cache_dict = kwargs.copy()
        cache_dict['caml'] = 'true'
        try:
            key = self.get_cache_key(**cache_dict)
            response = cache.get(key)
            if response is None:
                response = self.client.read_caml_items(filters=kwargs)
                cache.set(key, response)
            return response
        except ClientRequestException:
            raise Http404


class RestQuerySharePointViewSet(AbstractSharePointViewSet):

    def get_queryset(self):
        kwargs = self.request.query_params.dict()
        try:
            key = self.get_cache_key(**kwargs)
            response = cache.get(key)
            if response is None:
                response = self.client.read_items(filters=kwargs)
                cache.set(key, response)
            return response
        except ClientRequestException:
            raise Http404


class FileSharePointMixin:
    serializer_class = SharePointFileSerializer
    lookup_field = 'filename'
    lookup_value_regex = '[^/]+'

    def get_object(self):
        filename = self.kwargs.get('filename', None)
        try:
            doc_file = self.client.read_file(f'{filename}')
        except ClientRequestException:
            raise Http404
        return doc_file

    def get_queryset(self):
        kwargs = self.request.query_params.dict()
        try:
            return self.client.read_files(filters=kwargs)
        except ClientRequestException:
            raise Http404

    @action(detail=True, methods=['get'])
    def download(self, request, *args, **kwargs):
        sh_file = self.get_object()
        relative_url = sh_file.properties['ServerRelativeUrl']
        response = File.open_binary(self.client.context, relative_url)

        django_response = HttpResponse(
            content=response.content,
            status=response.status_code,
            content_type=response.headers['Content-Type'],
        )
        django_response['Content-Disposition'] = 'attachment; filename=%s' % sh_file.properties['Name']
        return django_response


class SharePointSearchViewSet(AbstractSharePointViewSet):
    serializer_class = SharePointSearchSerializer

    def get_queryset(self):
        kwargs = self.request.query_params.dict()
        try:
            key = self.get_cache_key(**kwargs)
            response = cache.get(key)
            if response is None:
                response = self.client.search(filters=kwargs)
                cache.set(key, response)
            return response
        except ClientRequestException:
            raise Http404
