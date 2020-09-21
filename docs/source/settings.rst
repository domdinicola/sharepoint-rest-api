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
default values.

.. warning:: All the entries must be prefixed by ``SHAREPOINT_``. To change the credential file
            location you have to put in your settings.py::

                WFP_AUTH_OFFICE_MODEL= 'myapp.Office'



.. setting:: CACHE_DISABLED
.. setting:: TENANT
.. setting:: SITE
.. setting:: SITE_TYPE
.. setting:: USERNAME
.. setting:: PASSWORD
.. setting:: PAGE_SIZE


CACHE_DISABLED
---------------------
Default: ``False``

Setting to toggle cache used, based on url


TENANT
-----------------------
Default: ``https://unitst.sharepoint.com``

SharePoint tenant name


SITE
----------------------
Default: ``GLB-DRP``

SharePoint site name


SITE_TYPE
--------------------
Default: ``sites``

SharePoint site type (sites/teams)


USERNAME
------------------------
Default: ``invalid_username``

Tenant username


PASSWORD
----------------------------
Default: ``invalid_password``

Tenant password


PAGE_SIZE
---------------------------
Default: ``25``

Search API page size