#!/usr/bin/env python
import ast
import os
import re

from setuptools import find_packages, setup

HERE = os.path.abspath(os.path.dirname(__file__))
init = os.path.join(HERE, "src", "sharepoint_rest_api", "__init__.py")

_version_re = re.compile(r'__version__\s+=\s+(.*)')
_name_re = re.compile(r'NAME\s+=\s+(.*)')

with open(init, 'rb') as f:
    content = f.read().decode('utf-8')
    VERSION = str(ast.literal_eval(_version_re.search(content).group(1)))
    NAME = str(ast.literal_eval(_name_re.search(content).group(1)))


setup(
    name=NAME,
    version=VERSION,
    url='https://github.com/domdinicola/sharepoint-rest-api',
    author='Domenico Di Nicola',
    author_email='domdinicola@unicef.org',
    description='Provide REST API (DRF style) for SharePoint',
    platforms=['any'],
    license='Apache 2 License',
    classifiers=[
        'Environment :: Web Environment',
        'Programming Language :: Python :: 3.8',
        'Framework :: Django',
        'Framework :: Django :: 3.0',
        'Intended Audience :: Developers'],
    install_requires = [
        'django',
        'django-filter',
        'django-model-utils',
        'djangorestframework',
        'office365-rest-client',
    ],
    extras_require={
        'test': [
            'django-webtest',
            'factory-boy',
            'flake8',
            'isort',
            'mock',
            'pytest',
            'pytest-cov',
            'pytest-django',
            'pytest-echo',
            'pytest-pythonpath',
            'pytest-redis',
            'requests-mock',
            'unittest2',
            'vcrpy',
            'drf_api_checker',
        ],
    },
    package_dir={'': 'src'},
    packages=find_packages('src'),
    include_package_data=True,
)
