#!/usr/bin/env python
from setuptools import find_packages, setup


def get_version():
    with open('taxii2_client/version.py') as f:
        for line in f.readlines():
            if line.startswith("__version__"):
                version = line.split()[-1].strip('"')
                return version
        raise AttributeError("Package does not have a __version__")


install_requires = [
    'requests',
]

setup(
    name='taxii2_client',
    description="Provide access to a TAXII server",
    version=get_version(),
    packages=find_packages(),
    install_requires=install_requires,
    keywords="taxii taxii2 json cti cyber threat intelligence",
)
