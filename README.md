SharePoint Rest API
===================

| Menu                 | Link                                                                                                                                                                       |
|----------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Coverage Development | [![codecov](https://codecov.io/gh/domdinicola/sharepoint-rest-api/branch/master/graph/badge.svg?token=hiBXw0smpH)](https://codecov.io/gh/domdinicola/sharepoint-rest-api)  |
| Coverage Stable      | [![codecov](https://codecov.io/gh/domdinicola/sharepoint-rest-api/branch/develop/graph/badge.svg?token=hiBXw0smpH)](https://codecov.io/gh/domdinicola/sharepoint-rest-api) |
| Source Code          | https://github.com/domdinicola/sharepoint-rest-api                                                                                                                         |
| Issue tracker        | https://github.com/domdinicola/sharepoint-rest-api/issues                                                                                                                  |
| Documentation        | https://sharepoint-rest-api.readthedocs.io/en/latest/                                                                                                                      |

Installation
------------

    pip install sharepoint-rest-api


Setup
-----

Add `sharepoint_rest_api` to ``INSTALLED_APPS`` in settings

    INSTALLED_APPS = [
        'sharepoint_rest_api',
    ]


Coding Standards
----------------

To run checks on the code to ensure code is in compliance

    $ ruff check
    $ ruff format


Testing
-------

Testing is important and tests are located in `tests/` directory and can be run with;

    $ uv run pytest test

Coverage report is viewable in `build/coverage` directory, and can be generated with;
