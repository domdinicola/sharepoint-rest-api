import os

from django.conf import settings


def env_or_settings(name, default):
    return os.environ.get(name, getattr(settings, name, default))


SHAREPOINT_TENANT = env_or_settings("SHAREPOINT_TENANT", "https://unitst.sharepoint.com")
SHAREPOINT_SITE = env_or_settings("SHAREPOINT_SITE", "GLB-DRP")
SHAREPOINT_SITE_TYPE = env_or_settings("SHAREPOINT_SITE_TYPE", "sites")
SHAREPOINT_CONNECTION = env_or_settings("SHAREPOINT_CONNECTION", "app")
SHAREPOINT_CLIENT_CERT_TENANT = env_or_settings("SHAREPOINT_CLIENT_CERT_TENANT", "invalid_cert_tenant")
SHAREPOINT_CLIENT_CERT_PATH = env_or_settings("SHAREPOINT_CLIENT_CERT_PATH", "")
SHAREPOINT_CLIENT_CERT_PRIVATE_KEY = env_or_settings("SHAREPOINT_CLIENT_CERT_PRIVATE_KEY", "")
SHAREPOINT_CLIENT_CERT_THUMBPRINT = env_or_settings("SHAREPOINT_CLIENT_CERT_THUMBPRINT", "")
SHAREPOINT_CLIENT_CERT_PASSPHRASE = env_or_settings("SHAREPOINT_CLIENT_CERT_PASSPHRASE", "")
SHAREPOINT_CLIENT_ID = env_or_settings("SHAREPOINT_CLIENT_ID", "invalid_client_id")
SHAREPOINT_CLIENT_SECRET = env_or_settings("SHAREPOINT_CLIENT_SECRET", "invalid_client_secret")
SHAREPOINT_USERNAME = env_or_settings("SHAREPOINT_USERNAME", "invalid_username")
SHAREPOINT_PASSWORD = env_or_settings("SHAREPOINT_PASSWORD", "invalid_password")
SHAREPOINT_PAGE_SIZE = int(env_or_settings("SHAREPOINT_PAGE_SIZE", 25))

GRAPH_CLIENT_ID = env_or_settings("GRAPH_CLIENT_ID", "invalid_graph_client_id")
GRAPH_CLIENT_SECRET = env_or_settings("GRAPH_CLIENT_SECRET", "invalid_graph_client_secret")
GRAPH_TENANT = env_or_settings("GRAPH_TENANT", "")
GRAPH_REGION = env_or_settings("GRAPH_REGION", "US")
GRAPH_PAGE_SIZE = int(env_or_settings("GRAPH_PAGE_SIZE", 25))
GRAPH_API_RETRY_COUNT = int(env_or_settings("GRAPH_API_RETRY_COUNT", 1))
