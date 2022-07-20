from rest_framework import routers

from sharepoint_rest_api.views.files import UploadViewSet
from sharepoint_rest_api.views.model_views import (
    SharePointLibraryViewSet,
    SharePointSiteViewSet,
    SharePointTenantViewSet,
)
from sharepoint_rest_api.views.settings_based import (
    SharePointSettingsCamlViewSet,
    SharePointSettingsFileViewSet,
    SharePointSettingsRestViewSet,
    SharePointSettingsSearchViewSet,
)
from sharepoint_rest_api.views.url_based import (
    SharePointUrlCamlViewSet,
    SharePointUrlFileViewSet,
    SharePointUrlRestViewSet,
)

app_name = 'sharepoint_rest_api'

router = routers.DefaultRouter()

# model
router.register(r'tenants', SharePointTenantViewSet, basename='sharepoint-tenant')
router.register(r'sites', SharePointSiteViewSet, basename='sharepoint-site')
router.register(r'libraries', SharePointLibraryViewSet, basename='sharepoint-library')

# url based
router.register(r'sharepoint/upload', UploadViewSet, basename="upload")
router.register(r'sharepoint/(?P<tenant>[\w\-]+)/(?P<site>[\w\-]+)/(?P<folder>[\w\W]+)/files',
                SharePointUrlFileViewSet, basename='sharepoint-url-files')
router.register(r'sharepoint/(?P<tenant>[\w\-]+)/(?P<site>[\w\-]+)/(?P<folder>[\w\W]+)/rest',
                SharePointUrlRestViewSet, basename='sharepoint-url-rest')
router.register(r'sharepoint/(?P<tenant>[\w\-]+)/(?P<site>[\w\-]+)/(?P<folder>[\w\W]+)/caml',
                SharePointUrlCamlViewSet, basename='sharepoint-url-caml')
router.register(r'sharepoint/(?P<tenant>[\w\-]+)/(?P<site>[\w\-]+)/search',
                SharePointSettingsSearchViewSet, basename='sharepoint-url-search')

# settings based
router.register(r'sharepoint/(?P<folder>[\w\W]+)/rest',
                SharePointSettingsRestViewSet, basename='sharepoint-settings-rest')
router.register(r'sharepoint/(?P<folder>[\w\W]+)/caml',
                SharePointSettingsCamlViewSet, basename='sharepoint-settings-caml')
router.register(r'sharepoint/(?P<folder>[\w\W]+)/files',
                SharePointSettingsFileViewSet, basename='sharepoint-settings-files')
router.register(r'sharepoint/search', SharePointSettingsSearchViewSet, basename='sharepoint-settings-search')

urlpatterns = router.urls
