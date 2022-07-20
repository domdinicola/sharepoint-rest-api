from rest_framework import serializers


class UploadSerializer(serializers.Serializer):
    file_uploaded = serializers.FileField(required=True)
    folder = serializers.CharField(required=True)
    metadata = serializers.JSONField(default=dict)

    class Meta:
        fields = ['file_uploaded']
