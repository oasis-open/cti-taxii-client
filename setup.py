#!/usr/bin/env python
from codecs import open

from setuptools import find_packages, setup


def get_long_description():
    with open('README.rst')as f:
        return f.read()


setup(
    name='taxii2-client',
    version='0.3.1',
    description='TAXII 2 Client Library',
    long_description=get_long_description(),
    url='https://github.com/oasis-open/cti-taxii-client',
    author='OASIS Cyber Threat Intelligence Technical Committee',
    author_email='cti-users@lists.oasis-open.org',
    maintainer='Greg Back',
    maintainer_email='gback@mitre.org',
    license='BSD',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Security',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
    keywords="taxii taxii2 client json cti cyber threat intelligence",
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
    }
)
