.. include:: globals.txt
.. _install:

======================
Install
======================

Add SharePoint REST API to your ``INSTALLED_APPS`` in your settings.py and configure
your settings.

.. code-block:: python

    INSTALLED_APPS = (
        ...
        'sharepoint_rest_api',
        ...
    )

Include the library urls in your main url.py:

.. code-block:: python

    path(r'api/', include('sharepoint_rest_api.urls', namespace='sharepoint')),


Create your tenant, site and library objects in your models, then configure
your settings.

Please see :ref:`settings`


Authentication
==============

The library supports two API backends:

**SharePoint REST API (legacy)**
  Uses the ``SharePointClient`` with one of three authentication modes
  (configured via ``SHAREPOINT_CONNECTION``):

  - ``"app"`` — SharePoint App-Only (ACS). **Deprecated by Microsoft** and
    no longer works for new tenants.
  - ``"user"`` — User credentials (username + password).
  - ``"cert"`` — Microsoft Entra ID app registration with a certificate.
    The recommended approach for app-only access.

**Microsoft Graph API (recommended)**
  Uses the ``GraphClient`` with MSAL client credentials flow. Configure via
  ``GRAPH_CLIENT_ID``, ``GRAPH_CLIENT_SECRET``, ``GRAPH_TENANT`` environment
  variables or Django settings.
