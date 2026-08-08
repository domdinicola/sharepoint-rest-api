.. include:: globals.txt
.. _settings:

========
Settings
========

.. contents::
    :local:
    :depth: 1

Available settings
==================

Here's a full list of all available settings, in alphabetical order, and their
default values, each settings can be overriden though an env var.

.. warning:: All the entries must be prefixed by ``SHAREPOINT_``. To change the credential file
            location you have to put in your settings.py::

                SHAREPOINT_SITE= 'NEW-SITE'


.. setting:: CACHE_DISABLED
.. setting:: CONNECTION
.. setting:: PAGE_SIZE
.. setting:: PASSWORD
.. setting:: SITE
.. setting:: SITE_TYPE
.. setting:: TENANT
.. setting:: USERNAME
.. setting:: CLIENT_ID
.. setting:: CLIENT_SECRET
.. setting:: CLIENT_CERT_TENANT
.. setting:: CLIENT_CERT_PATH
.. setting:: CLIENT_CERT_PRIVATE_KEY
.. setting:: CLIENT_CERT_THUMBPRINT
.. setting:: CLIENT_CERT_PASSPHRASE
.. setting:: GRAPH_CLIENT_ID
.. setting:: GRAPH_CLIENT_SECRET
.. setting:: GRAPH_TENANT
.. setting:: GRAPH_REGION
.. setting:: GRAPH_PAGE_SIZE


CACHE_DISABLED
---------------------
Default: ``False``

Setting to toggle cache used, based on url


CONNECTION
----------------------------
Default: ``app``

Authentication mode for the SharePoint client. Supported values:

- ``"app"`` — Microsoft Entra ID app-only using client_id + client_secret.
- ``"user"`` — User credentials via the MSAL resource owner password flow.
- ``"cert"`` — Microsoft Entra ID app registration using client_id + certificate.


PAGE_SIZE
---------------------------
Default: ``25``

SharePoint REST API page size


PASSWORD
----------------------------
Default: ``invalid_password``

Tenant password

SITE
---------------------
Default: ``GLB-DRP``

SharePoint site name


SITE_TYPE
-------------------
Default: ``sites``

SharePoint site type (sites/teams)


TENANT
----------------------
Default: ``https://unitst.sharepoint.com``

SharePoint tenant name. Also used to derive the Microsoft Entra ID tenant name
(e.g. ``https://contoso.sharepoint.com`` -> ``contoso.onmicrosoft.com``) for the
``"app"`` and ``"user"`` authentication modes.


USERNAME
------------------------
Default: ``invalid_username``

Tenant username


CLIENT_ID
---------------------------
Default: ``invalid_client_id``

Client ID for Microsoft Entra ID app-only or certificate-based authentication.


CLIENT_SECRET
-------------------------------
Default: ``invalid_client_secret``

Client secret for Microsoft Entra ID app-only authentication (``"app"`` connection). Not used in certificate mode.


CLIENT_CERT_TENANT
------------------------------------
Default: ``invalid_cert_tenant``

Tenant ID (directory ID) for certificate-based authentication. Used when ``SHAREPOINT_CONNECTION`` is ``"cert"``.


CLIENT_CERT_PATH
-----------------------------------
Default: ``""``

Path to the certificate file (.pfx/.pem) for certificate-based authentication.


CLIENT_CERT_PRIVATE_KEY
-----------------------------------------
Default: ``""``

Private key string for certificate-based authentication. Alternative to ``CLIENT_CERT_PATH``.


CLIENT_CERT_THUMBPRINT
----------------------------------------
Default: ``""``

Thumbprint of the certificate for certificate-based authentication.


CLIENT_CERT_PASSPHRASE
----------------------------------------
Default: ``""``

Passphrase for the certificate private key, if required.


GRAPH_CLIENT_ID
--------------------------------
Default: ``invalid_graph_client_id``

Client ID for the Microsoft Entra ID app registration used with Microsoft Graph API.


GRAPH_CLIENT_SECRET
------------------------------------
Default: ``invalid_graph_client_secret``

Client secret for the Microsoft Entra ID app registration used with Microsoft Graph API.


GRAPH_TENANT
----------------------------
Default: ``""``

Tenant ID (directory ID) for Microsoft Graph API authentication.


GRAPH_REGION
----------------------------
Default: ``US``

Region for the Microsoft Graph API (e.g. ``US``, ``EU``).


GRAPH_PAGE_SIZE
--------------------------------
Default: ``25``

Page size for Microsoft Graph Search API results.
