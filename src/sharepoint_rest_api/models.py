from urllib.parse import quote

from django.db import models
from django.utils.translation import gettext as _
from model_utils.models import TimeStampedModel


class SharePointTenant(TimeStampedModel):
    url = models.URLField(unique=True)
    username = models.CharField(verbose_name=_("Username"), max_length=64, null=True, blank=True)
    password = models.CharField(verbose_name=_("Password"), max_length=64, null=True, blank=True)

    @property
    def name(self):
        return self.url.split('//')[-1].split('.')[0]

    def __str__(self):
        return f'{self.url}'

    class Meta:
        ordering = ['url']
        verbose_name = 'SharePoint Tenant'
        verbose_name_plural = 'SharePoint Tenants'


class SharePointSite(TimeStampedModel):
    SITE = 'sites'
    TEAM = 'teams'

    SITE_TYPES = (
        (SITE, SITE),
        (TEAM, TEAM),
    )

    tenant = models.ForeignKey(SharePointTenant, related_name='sites', on_delete=models.deletion.CASCADE)
    name = models.CharField(verbose_name=_("Name"), max_length=32)
    site_type = models.CharField(verbose_name=_("Site Type"), max_length=16, choices=SITE_TYPES, default=SITE)

    class Meta:
        ordering = ['name']
        verbose_name = 'SharePoint Site'
        verbose_name_plural = 'SharePoint Sites'

    def __str__(self):
        return f'{self.tenant} ({self.name})'

    def relative_url(self):
        return f'{self.site_type}/{self.name}'

    def site_url(self):
        return f'{self.tenant}{self.site_type}/{self.name}'


class SharePointLibrary(TimeStampedModel):
    name = models.CharField(verbose_name=_("Name"), max_length=64)
    site = models.ForeignKey(SharePointSite, related_name='libraries', on_delete=models.deletion.CASCADE)
    active = models.BooleanField(verbose_name=_("Active"), default=True)
    public = models.BooleanField(verbose_name=_("Public"), default=True)

    class Meta:
        ordering = ['name']
        unique_together = ('name', 'site', )
        verbose_name = 'SharePoint Document Library'
        verbose_name_plural = 'SharePoint Document Libraries'

    def __str__(self):
        return f'{self.name} ({self.site.name}) [{self.site.tenant}]'

    @property
    def library_url(self):
        return str(self.site.tenant) + quote(f'{self.site.site_type}/{self.site.name}/{self.name}')
