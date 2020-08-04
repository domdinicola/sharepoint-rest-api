from django.contrib import admin

from .models import SharePointLibrary, SharePointSite, SharePointTenant


@admin.register(SharePointTenant)
class SharepointTenantAdmin(admin.ModelAdmin):
    search_fields = ('url', )
    list_display = ('url', )


@admin.register(SharePointSite)
class SharepointSiteAdmin(admin.ModelAdmin):
    search_fields = ('name', )
    list_display = ('name', 'site_type', 'tenant')
    list_filter = ('site_type', 'tenant')


@admin.register(SharePointLibrary)
class DocumentLibraryAdmin(admin.ModelAdmin):
    search_fields = ('name', )
    list_display = ('name', 'site', 'active', 'public')
    list_filter = ('active', 'public')
