.. include:: globals.txt
.. currentmodule:: sharepoint_rest_api.models
.. _models:

=======
Models
=======

.. contents::
    :local:
    :depth: 1

SharePointTenant
================

.. autoclass:: sharepoint_rest_api.models.SharePointTenant

    .. attribute:: url
    .. attribute:: username
    .. attribute:: password

SharePointSite
==============

.. autoclass:: sharepoint_rest_api.models.SharePointSite

    .. attribute:: tenant
    .. attribute:: name
    .. attribute:: site_type


SharePointLibrary
=================

.. autoclass:: sharepoint_rest_api.models.SharePointLibrary

    .. attribute:: name
    .. attribute:: site
    .. attribute:: active
    .. attribute:: public
