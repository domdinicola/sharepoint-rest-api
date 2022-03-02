import os

from django.conf import settings


def env_or_settings(name, default):
    return os.environ.get(name, getattr(settings, name, default))


SHAREPOINT_TENANT = env_or_settings('SHAREPOINT_TENANT', 'https://unitst.sharepoint.com')
SHAREPOINT_SITE = env_or_settings('SHAREPOINT_SITE', 'GLB-DRP')
SHAREPOINT_SITE_TYPE = env_or_settings('SHAREPOINT_SITE_TYPE', 'sites')
SHAREPOINT_CONNECTION = env_or_settings('SHAREPOINT_CONNECTION', 'app')
SHAREPOINT_CLIENT_ID = env_or_settings('SHAREPOINT_CLIENT_ID', 'invalid_client_id')
SHAREPOINT_CLIENT_SECRET = env_or_settings('SHAREPOINT_CLIENT_SECRET', 'invalid_client_secret')
SHAREPOINT_USERNAME = env_or_settings('SHAREPOINT_USERNAME', 'invalid_username')
SHAREPOINT_PASSWORD = env_or_settings('SHAREPOINT_PASSWORD', 'invalid_password')
SHAREPOINT_PAGE_SIZE = int(env_or_settings('SHAREPOINT_PAGE_SIZE', 25))
