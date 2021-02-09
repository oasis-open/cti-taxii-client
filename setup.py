#!/usr/bin/env python
from codecs import open
import os

from setuptools import find_packages, setup

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VERSION_FILE = os.path.join(BASE_DIR, 'taxii2client', 'version.py')


def get_version():
    with open(VERSION_FILE) as f:
        for line in f.readlines():
            if line.startswith('__version__'):
                version = line.split()[-1].strip('"')
                return version
        raise AttributeError("Package does not have a __version__")


def get_long_description():
    with open('README.rst') as f:
        return f.read()


setup(
    name='taxii2-client',
    version=get_version(),
    description='TAXII 2 Client Library',
    long_description=get_long_description(),
    long_description_content_type='text/x-rst',
    url='https://oasis-open.github.io/cti-documentation/',
    author='OASIS Cyber Threat Intelligence Technical Committee',
    author_email='cti-users@lists.oasis-open.org',
    maintainer='Emmanuelle Vargas-Gonzalez',
    maintainer_email='emmanuelle@mitre.org',
    license='BSD',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Security',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
    keywords='taxii taxii2 client json cti cyber threat intelligence',
    packages=find_packages(exclude=['*.test']),
    install_requires=[
        'requests',
        'six',
        'pytz',
    ],
    extras_require={
        'test': [
            'coverage',
            'pytest',
            'pytest-cov',
            'responses',
            'tox',
        ],
        'docs': [
            'sphinx',
            'sphinx-prompt',
        ]
    },
    project_urls={
        'Documentation': 'https://taxii2client.readthedocs.io/',
        'Source Code': 'https://github.com/oasis-open/cti-taxii-client/',
        'Bug Tracker': 'https://github.com/oasis-open/cti-taxii-client/issues/',
    },
)
