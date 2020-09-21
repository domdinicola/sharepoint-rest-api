.. include:: globals.txt
.. currentmodule:: sharepoint_rest_api.models
.. _models:

=======
Models
=======


SharePointTenant
================

.. autoclass:: sharepoint_rest_api.models.SharePointTenant

    .. attribute:: url

        URL field

    .. attribute:: parent (related name: children)

        username. ForeignKey to :class:`~wfp_auth.models.AbstractOffice`


SharePointSite
==============

.. autoclass:: wfp_auth.models.Office

    Base Office class that extends from :class:`~wfp_auth.models.AbstractOffice`.
    Applications can customize Office class using :setting:`WFP_AUTH_OFFICE_MODEL`


    .. attribute:: type

        Required. One of [HQ, REGIONAL, COUNTRY, SUB, SPECIAL, LIASION, SUPPORT, WAREHOUSE, CLUSTER, RESPONSE]:
            * HQ    : HeadQuarters
            * REGIONAL: Regional Bureau
            * COUNTRY: Country Office
            * SUB: Sub Office
            * SPECIAL: Special Office
            * LIASION: Liaison Office
            * SUPPORT: Support Office
            * WAREHOUSE: Warehouse Office
            * CLUSTER: Cluster Office
            * RESPONSE: Emer. Response Coord. Office

    .. attribute:: code

        Required. Unique. Up to 8 characters.
            country.iso_code * type_code
        Es.
           * HeadQuarter:  **ITHQ**
           * Bankgok Regional Bureau: **THRB**
           * Kenya Country Office: **KECO**

    .. attribute:: country

        Required. ForeignKey to :class:`~geo.models.Country`

    .. attribute:: location

        Optional. ForeignKey to :class:`~geo.models.Location`

    .. attribute:: duty_station

        Optional. ForeignKey to :class:`~wfp_auth.models.DutyStation`


    .. attribute:: wings_code

        Optional.

    .. attribute:: timezone

        Optional.

    .. attribute:: foodsat_prefix

        Optional. 10 characters or fewer.

    .. attribute:: capi_id

        Field to synchronize data using CommonApi.

WFPUser
========

.. seealso:: :class:`~django.contrib.auth.models.User`

.. autoclass:: wfp_auth.models.WFPUser

    .. attribute:: indexno

        Optional. WFP index number

    .. attribute:: office

        Optional. ForeignKey to :class:`~wfp_auth.models.Office`

    .. attribute:: division

        Optional. ForeignKey to :class:`~wfp_auth.models.Division`

    .. attribute:: country

        Optional. ForeignKey to :class:`~geo.models.Country`

    .. attribute:: username

        Optional. Unique.

    .. attribute:: first_name

        Optional.

    .. attribute:: last_name

        Optional.

    .. attribute:: email

        Optional. Unique. 254 characters or fewer.

    .. attribute:: is_staff

        Required.

    .. attribute:: is_active

        Required.

    .. attribute:: date_joined

        Auto.

    .. attribute:: timezone

        Optional.

    .. attribute:: functional_areas

        Optional. ManyToManyField to :class:`~wfp_auth.models.FunctionalArea`


UserRole
=========

.. autoclass:: wfp_auth.models.UserRole


    .. attribute:: user

        Required. ForeignKey to :class:`~wfp_auth.models.WFPUser`

    .. attribute:: role

        Required. ForeignKey to :class:`~django.contrib.auth.models.Group`

    .. attribute:: office

        Optional. ForeignKey to :class:`~wfp_auth.models.Office`

    .. attribute:: division

        Optional. ForeignKey to :class:`~wfp_auth.models.Division`


DutyStation
===========

.. autoclass:: wfp_auth.models.DutyStation

    .. attribute:: country

        Required. ForeignKey to :class:`~geo.models.Country`

    .. attribute:: location_name

        Required. 128 characters or fewer.

    .. attribute:: code

        Required. 16 characters or fewer.

    .. attribute:: capi_id

        Field to synchronize data using CommonApi.



SharePointLibrary
=================

.. autoclass:: wfp_auth.models.Division

    .. attribute:: name

        Required. 255 characters or fewer.

    .. attribute:: code

        Required. Unique. 8 characters or fewer.

    .. attribute:: parent (related name: children)

        Optional. ForeignKey to :class:`~wfp_auth.models.Division`

    .. attribute:: office

        Optional. ForeignKey to :class:`~wfp_auth.models.Office`

    .. attribute:: wings_cost_centre

        Required. 100 characters or fewer.

    .. attribute:: chief

        Optional. ForeignKey to :class:`~wfp_auth.models.WFPUser`

    .. attribute:: wings_cost_centre

        Optional.

    .. attribute:: capi_id

        Field to synchronize data using CommonApi.


FunctionalArea
==============

.. autoclass:: wfp_auth.models.FunctionalArea

    .. attribute:: name

        Required. 100 characters or fewer.

    .. attribute:: enabled

        Boolean. Field to flag enabled functional areas.

    .. attribute:: capi_id

        Field to synchronize data using CommonApi.


PositionTitle
=============

.. autoclass:: wfp_auth.models.PositionTitle

    .. attribute:: label

        Required. 100 characters or fewer.

    .. attribute:: capi_id

        Field to synchronize data using CommonApi.


OrganisationalStructurePositionTitle
====================================

.. autoclass:: wfp_auth.models.OrganisationalStructurePositionTitle

    .. attribute:: user

        Required. ForeignKey to :class:`~wfp_auth.models.WFPUser`

    .. attribute:: title

        Required. ForeignKey to :class:`~django.contrib.auth.models.PositionTitle`

    .. attribute:: office

        Optional. ForeignKey to :class:`~wfp_auth.models.Office`

    .. attribute:: division

        Optional. ForeignKey to :class:`~wfp_auth.models.Division`



Mixins
=============

.. autoclass:: wfp_auth.utils.SelectedOfficeMixin

    ..  wfp_auth.utils.SelectedOfficeMixin.selected_office automethod::

    ..  wfp_auth.utils.SelectedOfficeMixin.get_initial automethod::

    ..  wfp_auth.utils.SelectedOfficeMixin.get_context_data automethod::
