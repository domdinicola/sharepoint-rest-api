.. include:: globals.txt
.. currentmodule:: sharepoint_rest_api.client
.. _client:


======
Client
======

Class to create a SharePoint Client used to be the interface with SharePoint

.. contents::
    :local:
    :depth: 1


Authentication modes
====================

The ``SharePointClient`` supports three authentication modes, configured via the
``SHAREPOINT_CONNECTION`` setting:

- ``"app"`` — Microsoft Entra ID app-only using client_id + client_secret.
- ``"user"`` — User credentials via the MSAL resource owner password flow
  (requires a registered ``client_id`` and the tenant name).
- ``"cert"`` — Microsoft Entra ID app registration using client_id + certificate.
  This is the recommended approach for app-only access.

For the ``"app"`` and ``"user"`` modes, the following additional settings are used:

- ``SHAREPOINT_CLIENT_ID``
- ``SHAREPOINT_CLIENT_SECRET`` (``"app"`` mode only)
- ``SHAREPOINT_USERNAME`` and ``SHAREPOINT_PASSWORD`` (``"user"`` mode only)

The Microsoft Entra ID tenant name is derived from ``SHAREPOINT_TENANT``
(e.g. ``https://contoso.sharepoint.com`` -> ``contoso.onmicrosoft.com``).

For certificate-based authentication, the following additional settings are used:

- ``SHAREPOINT_CLIENT_ID``
- ``SHAREPOINT_CLIENT_CERT_TENANT``
- ``SHAREPOINT_CLIENT_CERT_PATH`` or ``SHAREPOINT_CLIENT_CERT_PRIVATE_KEY``
- ``SHAREPOINT_CLIENT_CERT_THUMBPRINT``
- ``SHAREPOINT_CLIENT_CERT_PASSPHRASE`` (optional)


Microsoft Graph API client
==========================

This library also provides a ``GraphClient`` that accesses SharePoint content
via the Microsoft Graph API using MSAL (client credentials flow). It uses
the ``/search/query`` endpoint and supports batched field enrichment.

Configure it via the ``GRAPH_*`` settings (``GRAPH_CLIENT_ID``,
``GRAPH_CLIENT_SECRET``, ``GRAPH_TENANT``, etc.) or environment variables.

.. autoclass:: sharepoint_rest_api.graph_client.GraphClient
    :members:

.. autoclass:: sharepoint_rest_api.client.SharePointClient
    :members:
