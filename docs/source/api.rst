.. include:: globals.txt
.. currentmodule:: sharepoint_rest_api.views
.. _api:

===
API
===

.. contents::
    :local:
    :depth: 1


Base Views
==========

.. autofunction:: sharepoint_rest_api.views.base.AbstractSharePointViewSet
.. autofunction:: sharepoint_rest_api.views.base.CamlQuerySharePointViewSet
.. autofunction:: sharepoint_rest_api.views.base.RestQuerySharePointViewSet
.. autofunction:: sharepoint_rest_api.views.base.FileSharePointMixin
.. autofunction:: sharepoint_rest_api.views.base.SharePointSearchViewSet



Model Views
===========
.. autofunction:: sharepoint_rest_api.views.model_views.SharePointTenantViewSet
.. autofunction:: sharepoint_rest_api.views.model_views.SharePointSiteViewSet
.. autofunction:: sharepoint_rest_api.views.model_views.SharePointLibraryViewSet


Settings Based Views
====================

.. autofunction:: sharepoint_rest_api.views.settings_based.SettingsBasedSharePointViewSet
.. autofunction:: sharepoint_rest_api.views.settings_based.SharePointSettingsRestViewSet
.. autofunction:: sharepoint_rest_api.views.settings_based.SharePointSettingsCamlViewSet
.. autofunction:: sharepoint_rest_api.views.settings_based.SharePointSettingsFileViewSet
.. autofunction:: sharepoint_rest_api.views.settings_based.SharePointSettingsSearchViewSet


URL Based Views
===============

.. autofunction:: sharepoint_rest_api.views.url_based.UrlBasedSharePointViewSet
.. autofunction:: sharepoint_rest_api.views.url_based.SharePointUrlRestViewSet
.. autofunction:: sharepoint_rest_api.views.url_based.SharePointUrlCamlViewSet
.. autofunction:: sharepoint_rest_api.views.url_based.SharePointUrlFileViewSet
