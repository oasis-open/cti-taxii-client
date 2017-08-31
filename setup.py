#!/usr/bin/env python
from codecs import open
import os.path

from setuptools import find_packages, setup

here = os.path.abspath(os.path.dirname(__file__))


def get_version():
    with open('taxii2client/version.py', encoding="utf-8") as f:
        for line in f.readlines():
            if line.startswith("__version__"):
                version = line.split()[-1].strip('"')
                return version
        raise AttributeError("Package does not have a __version__")


with open(os.path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()


setup(
    name='taxii2-client',
    version=get_version(),
    description='TAXII 2 Client Library',
    long_description=long_description,
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
    ],
    keywords="taxii taxii2 client json cti cyber threat intelligence",
    packages=find_packages(),
    install_requires=[
        'requests',
        'six',
    ],
    extras_require={
        'test': [
            'coverage',
            'pytest',
            'pytest-cov',
            'responses',
            'tox',
        ],
    }
)
