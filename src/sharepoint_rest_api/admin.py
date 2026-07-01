from django.contrib import admin

from .models import SharePointLibrary, SharePointSite, SharePointTenant


@admin.register(SharePointTenant)
class SharepointTenantAdmin(admin.ModelAdmin):
    search_fields = ("url",)
    list_display = ("url",)
    fieldsets = (
        (None, {"fields": ("url", "username", "password")}),
        (
            "Client Certificate",
            {
                "fields": (
                    "client_id",
                    "client_cert_tenant",
                    "client_cert_path",
                    "client_cert_thumbprint",
                    "client_cert_passphrase",
                ),
            },
        ),
    )


@admin.register(SharePointSite)
class SharepointSiteAdmin(admin.ModelAdmin):
    search_fields = ("name",)
    list_display = ("name", "site_type", "tenant")
    list_filter = ("site_type", "tenant")


@admin.register(SharePointLibrary)
class DocumentLibraryAdmin(admin.ModelAdmin):
    search_fields = ("name",)
    list_display = ("name", "site", "active", "public")
    list_filter = ("active", "public")
