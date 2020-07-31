from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path(r'admin/', admin.site.urls),
    path(r'api/', include('sharepoint_rest_api.urls', namespace='sharepoint-api')),
]
