.. include:: globals.txt
.. _install:

======================
Install
======================

add SharePoint REST API in your INSTALLED APPS in your settings.py and configure your settingss

.. code-block:: python

    INSTALLED_APPS = (
        ...
        'sharepoint_rest_api',
        ...
    )

include your the library urls in the main url.py

.. code-block:: python

    path(r'api/', include('sharepoint_rest_api.urls', namespace='sharepoint')),


setup your settings
===================

Please see :ref:`settings`

