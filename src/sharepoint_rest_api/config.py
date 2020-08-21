import os

SHAREPOINT_CACHE_DISABLED = os.environ.get('SHAREPOINT_CACHE_DISABLED', False)
SHAREPOINT_TENANT = os.environ.get('SHAREPOINT_TENANT', 'https://unitst.sharepoint.com')
SHAREPOINT_SITE = os.environ.get('SHAREPOINT_SITE', 'GLB-DRP')
SHAREPOINT_SITE_TYPE = os.environ.get('SHAREPOINT_SITE_TYPE', 'sites')
SHAREPOINT_USERNAME = os.environ.get('SHAREPOINT_USERNAME', 'invalid_username')
SHAREPOINT_PASSWORD = os.environ.get('SHAREPOINT_PASSWORD', 'invalid_password')


SHAREPOINT_PAGE_SIZE = int(os.environ.get('SHAREPOINT_PAGE_SIZE', 25))
