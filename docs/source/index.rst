.. include:: globals.txt
.. _index:

Welcome to SharePoint REST API's documentation!
===============================================

|app| provides REST API to connect to SharePoint, similarly to Django Rest Framework.

The library allows you to query specific library or use the search API.
You can work in two modality: URLs or Settings.

URL based mode
--------------

URL mode would specify: tenant and site in the url

.. note::
    "api/sharepoint/<tenant>/<site>/<library>/<search-type>/?<filter>=<value>"

Settings based mode
-------------------

Settings mode would use... settings

SHAREPOINT_TENANT
SHAREPOINT_SITE

.. note::
    "api/sharepoint/<library>/<search-type>/?<filter>=<value>"


.. toctree::
   :maxdepth: 2
   :caption: Contents:



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`


Overview
======================
.. toctree::
    :maxdepth: 1

    install
    settings
    api
    serializers
    client
    builders
    models
    utils
    changes
    intershpinx
