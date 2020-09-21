.. include:: globals.txt
.. _install:

======================
Install
======================

add SharePoint REST API in your INSTALLED APPS in your settings.py

.. code-block:: python

    INSTALLED_APPS = (
        ...
        'sharepoint_rest_api',
        ...
    )




.. note::
    assure following urls have been imported in your urls.py

.. code-block:: python

    path(r'api/', include('sharepoint_rest_api.urls', namespace='sharepoint')),


Available settings
======================

Please see :ref:`settings`

