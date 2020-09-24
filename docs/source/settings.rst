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
.. setting:: PAGE_SIZE
.. setting:: PASSWORD
.. setting:: SITE
.. setting:: SITE_TYPE
.. setting:: TENANT
.. setting:: USERNAME


CACHE_DISABLED
---------------------
Default: ``False``

Setting to toggle cache used, based on url


PAGE_SIZE
---------------------------
Default: ``25``

Search API page size


PASSWORD
----------------------------
Default: ``invalid_password``

Tenant password

SITE
----------------------
Default: ``GLB-DRP``

SharePoint site name


SITE_TYPE
--------------------
Default: ``sites``

SharePoint site type (sites/teams)


TENANT
-----------------------
Default: ``https://unitst.sharepoint.com``

SharePoint tenant name


USERNAME
------------------------
Default: ``invalid_username``

Tenant username
