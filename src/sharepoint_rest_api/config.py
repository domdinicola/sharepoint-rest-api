import os

SHAREPOINT_TENANT = os.environ.get('SHAREPOINT_TENANT', 'https://tenant.sharepoint.com')
SHAREPOINT_SITE = os.environ.get('SHAREPOINT_SITE', 'SITE')
SHAREPOINT_SITE_TYPE = os.environ.get('SHAREPOINT_SITE_TYPE', 'sites')
SHAREPOINT_USERNAME = os.environ.get('SHAREPOINT_USERNAME', 'invalid_username')
SHAREPOINT_PASSWORD = os.environ.get('SHAREPOINT_PASSWORD', 'invalid_password')
