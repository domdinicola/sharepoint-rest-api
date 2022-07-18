import math
from urllib.parse import urlencode

from django.core.cache import caches
from django.http import HttpResponse, HttpResponseBadRequest
from django_filters.rest_framework import DjangoFilterBackend
from office365.runtime.client_request_exception import ClientRequestException
from office365.sharepoint.files.file import File
from rest_framework import viewsets
from rest_framework.decorators import action

from sharepoint_rest_api import config
from sharepoint_rest_api.serializers.sharepoint import SharePointFileSerializer, SharePointSearchSerializer
from sharepoint_rest_api.utils import get_cache_key

cache = caches['default']


class AbstractSharePointViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Base ViewSet for SharePoint Integration
    """
    serializer_class = None
    filter_backends = (DjangoFilterBackend, )
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

    def get_cache_key(self, **kwargs):
        keys = [key for key in [self.tenant, self.site, self.folder] if key]
        key = get_cache_key(keys, **kwargs)
        return key


class CamlQuerySharePointViewSet(AbstractSharePointViewSet):
    """
    Viewset for CamlQuery Integration
    """

    def get_queryset(self):
        kwargs = self.request.query_params.dict()
        cache_dict = kwargs.copy()
        cache_dict['caml'] = 'true'
        key = self.get_cache_key(**cache_dict)
        response = cache.get(key)
        if response is None:
            response = self.client.read_caml_items(filters=kwargs)
            cache.set(key, response)
        return response


class RestQuerySharePointViewSet(AbstractSharePointViewSet):
    """
    Viewset for Rest Integration
    """

    def get_queryset(self):
        kwargs = self.request.query_params.dict()
        key = self.get_cache_key(**kwargs)
        response = cache.get(key)
        if response is None:
            response = self.client.read_items(filters=kwargs)
            cache.set(key, response)
        return response


class FileSharePointViewSet(AbstractSharePointViewSet):
    """
    Base Viewset to handle SharePoint file metadata
    """
    serializer_class = SharePointFileSerializer
    lookup_field = 'filename'
    lookup_value_regex = '[^/]+'

    def get_object(self):
        filename = self.kwargs.get('filename', None)
        doc_file = self.client.read_file(f'{filename}')
        return doc_file

    def get_queryset(self):
        kwargs = self.request.query_params.dict()
        return self.client.read_files(filters=kwargs)

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
    """
    Base class for SharePoint Search API
    """
    serializer_class = SharePointSearchSerializer
    selected_fields = None
    total_rows = None

    def get_filters(self, kwargs):
        kwargs.pop('serializer', None)
        return kwargs

    def get_selected(self, selected):
        return selected.split(',') if selected else self.serializer_class._declared_fields.keys()

    def get_queryset(self):
        kwargs = self.request.query_params.dict()
        key = self.get_cache_key(**kwargs)
        search = kwargs.pop('search', None)
        selected = self.get_selected(kwargs.pop('selected', None))
        order_by = kwargs.pop('order_by', None)
        source_id = kwargs.pop('source_id', None)
        page = int(kwargs.pop('page', 1))
        filters = self.get_filters(kwargs)
        cached = cache.get(key)
        if cached is None:
            response, self.total_rows = self.client.search(
                search=search,
                filters=filters,
                select=selected,
                order_by=order_by,
                source_id=source_id,
                page=page
            )
            cache.set(key, (response, self.total_rows))
        else:
            response, self.total_rows = cached
        return response

    def list(self, request, *args, **kwargs):
        def get_link(page):
            last_dict = request.query_params.copy()
            if page == 0:
                return
            elif page == 1:
                last_dict.pop('page', None)
            elif page > 1:
                last_dict['page'] = str(page)
            return request.build_absolute_uri('?') + '?' + urlencode(last_dict)

        try:
            response = super().list(request, *args, **kwargs)
        except ClientRequestException as e:
            return HttpResponseBadRequest(str(e))
        current_page = int(self.request.query_params.get('page', 1))
        last_offset = math.ceil(self.total_rows / config.SHAREPOINT_PAGE_SIZE)
        prev_offset = current_page - 1
        next_offset = current_page + 1 if current_page < last_offset else 0

        response.data = {
            "first": get_link(1),
            "last": get_link(last_offset),
            "previous": get_link(prev_offset),
            "next": get_link(next_offset),
            "total_rows": self.total_rows,
            "items": response.data,
        }
        return response
