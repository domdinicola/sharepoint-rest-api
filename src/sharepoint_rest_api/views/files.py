import json

from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from sharepoint_rest_api.serializers.files import UploadSerializer
from sharepoint_rest_api import config
from sharepoint_rest_api.client import SharePointClient


class UploadViewSet(ViewSet):
    serializer_class = UploadSerializer

    def list(self, request):
        return Response("Use the form to upload files")

    def create(self, request):
        file_uploaded = request.FILES.get('file_uploaded')
        folder = request.POST.get('folder')
        metadata = request.POST.get('metadata')

        if isinstance(metadata, str):
            metadata = json.loads(metadata)

        client = SharePointClient(
            url=f'{config.SHAREPOINT_TENANT}/{config.SHAREPOINT_SITE_TYPE}/{config.SHAREPOINT_SITE}', folder=folder)

        client.upload_file(file_uploaded, folder_name=folder, metadata=metadata)
        response = "{} uploaded ".format(file_uploaded.name)

        return Response(response)
