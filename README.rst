SharePoint Rest API
===================


Installation
------------

.. code-block:: bash

    pip install sharepoint-rest-api


Setup
-----

Add `sharepoint_rest_api` to ``INSTALLED_APPS`` in settings

.. code-block:: bash

    INSTALLED_APPS = [
        'sharepoint_rest_api',
    ]


Contributing
------------

Environment Setup
~~~~~~~~~~~~~~~~~

To configure the development environment

.. code-block:: bash

    $ make develop


Coding Standards
~~~~~~~~~~~~~~~~

See `PEP 8 Style Guide for Python Code <https://www.python.org/dev/peps/pep-0008/>`_ for complete details on the coding standards.

To run checks on the code to ensure code is in compliance

.. code-block:: bash

    $ make lint


Testing
~~~~~~~

Testing is important and tests are located in `tests/` directory and can be run with;

.. code-block:: bash

    $ make test

Coverage report is viewable in `build/coverage` directory, and can be generated with;



Links
~~~~~

+--------------------+----------------+--------------+--------------------------+
| Stable             | |master-build| | |master-cov| |                          |
+--------------------+----------------+--------------+--------------------------+
| Development        | |dev-build|    | |dev-cov|    |                          |
+--------------------+----------------+--------------+--------------------------+
| Source Code        |https://github.com/domdinicola/sharepoint-rest-api        |
+--------------------+----------------+-----------------------------------------+
| Issue tracker      |https://github.com/domdinicola/sharepoint-rest-api/issues |
+--------------------+----------------+-----------------------------------------+


.. |master-build| image:: https://secure.travis-ci.org/domdinicola/sharepoint-rest-api.svg?branch=master
                    :target: http://travis-ci.org/domdinicola/sharepoint-rest-api/

.. |master-cov| image:: https://codecov.io/gh/domdinicola/sharepoint-rest-api/branch/master/graph/badge.svg
                    :target: https://codecov.io/gh/domdinicola/sharepoint-rest-api

.. |dev-build| image:: https://secure.travis-ci.org/domdinicola/sharepoint-rest-api.svg?branch=develop
                  :target: http://travis-ci.org/domdinicola/sharepoint-rest-api/

.. |dev-cov| image:: https://codecov.io/gh/domdinicola/sharepoint-rest-api/branch/develop/graph/badge.svg
                    :target: https://codecov.io/gh/domdinicola/sharepoint-rest-api



Compatibility Matrix
--------------------

Stable
~~~~~~

.. image:: https://travis-matrix-badges.herokuapp.com/repos/domdinicola/sharepoint-rest-api/branches/master


Develop
~~~~~~~

.. image:: https://travis-matrix-badges.herokuapp.com/repos/domdinicola/sharepoint-rest-api/branches/develop
