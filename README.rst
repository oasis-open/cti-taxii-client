|Build_Status| |Coverage| |Version|

cti-taxii-client
================

NOTE: This is an `OASIS TC Open Repository
<https://www.oasis-open.org/resources/open-repositories/>`_. See the
`Governance`_ section for more information.

cti-taxii-client is a minimal client implementation for the TAXII 2.X server.
It supports the following TAXII 2.X API services:

- Server Discovery
- Get API Root Information
- Get Status
- Get Collections
- Get a Collection
- Get Objects
- Add Objects
- Get an Object
- Delete an Object (2.1 only)
- Get Object Manifests
- Get Object Versions (2.1 only)

Installation
------------

The easiest way to install the TAXII client is with pip

.. code-block:: bash

   $ pip install taxii2-client

Usage
-----

The TAXII client is intended to be used as a Python library.  There are no
command line clients at this time.

``taxii2-client`` provides four classes:

- ``Server``
- ``ApiRoot``
- ``Collection``
- ``Status``

Each can be instantiated by passing a `url`, and (optional) `user` and
`password` arguments. The authorization information is stored in the instance,
so it need not be supplied explicitly when requesting services. By default, the
latest version of the supported spec will be imported. If you need a specific
version you can perform the following:

.. code-block:: python

   from taxii2client.v21 import Server
   server = Server('https://example.com/taxii2/', user='user_id', password='user_password')

Once you have instantiated a ``Server`` object, you can get all metadata about
its contents via its properties:

.. code-block:: python

   print(server.title)

This will lazily load and cache the server's information in the instance:

- ``api_roots``
- ``title``
- ``description``
- ``default`` (i.e. the default API root)
- ``contact``

You can follow references to ``ApiRoot`` objects,
``Collection`` objects, and (STIX) objects in those collections.

.. code-block:: python

   api_root = server.api_roots[0]
   collection = api_root.collections[0]
   collection.add_objects(stix_bundle)

Each ``ApiRoot`` has attributes corresponding to its meta data

- ``title``
- ``description``
- ``max_content_length``
- ``collections``

Each ``Collection`` has attributes corresponding to its meta data:

- ``id``
- ``title``
- ``description``
- ``alias`` (2.1 only)
- ``can_write``
- ``can_read``
- ``media_types``

A ``Collection`` can also be instantiated directly:

.. code-block:: python

    # Performing TAXII 2.0 Requests
    from taxii2client.v20 import Collection, as_pages

    collection = Collection('https://example.com/api1/collections/91a7b528-80eb-42ed-a74d-c6fbd5a26116')
    print(collection.get_object('indicator--252c7c11-daf2-42bd-843b-be65edca9f61'))

    # For normal (no pagination) requests
    print(collection.get_objects())
    print(collection.get_manifest())

    # For pagination requests.
    # Use *args for other arguments to the call and **kwargs to pass filter information
    for bundle in as_pages(collection.get_objects, per_request=50):
        print(bundle)

    for manifest_resource in as_pages(collection.get_manifest, per_request=50):
        print(manifest_resource)

    # ---------------------------------------------------------------- #
    # Performing TAXII 2.1 Requests
    from taxii2client.v21 import Collection, as_pages

    collection = Collection('https://example.com/api1/collections/91a7b528-80eb-42ed-a74d-c6fbd5a26116')
    print(collection.get_object('indicator--252c7c11-daf2-42bd-843b-be65edca9f61'))

    # For normal (no pagination) requests
    print(collection.get_objects())
    print(collection.get_manifest())

    # For pagination requests.
    # Use *args for other arguments to the call and **kwargs to pass filter information
    for envelope in as_pages(collection.get_objects, per_request=50):
        print(envelope)

    for manifest_resource in as_pages(collection.get_manifest, per_request=50):
        print(manifest_resource)

In addition to the object-specific properties and methods, all classes have a
``refresh()`` method that reloads the URL corresponding to that resource, to
ensure properties have the most up-to-date values.

Governance
----------

This GitHub public repository (
**https://github.com/oasis-open/cti-taxii-client** ) was created at the request
of the `OASIS Cyber Threat Intelligence (CTI) TC
<https://www.oasis-open.org/committees/cti/>`__ as an `OASIS TC Open Repository
<https://www.oasis-open.org/resources/open-repositories/>`__ to support
development of open source resources related to Technical Committee work.

While this TC Open Repository remains associated with the sponsor TC, its
development priorities, leadership, intellectual property terms, participation
rules, and other matters of governance are `separate and distinct
<https://github.com/oasis-open/cti-taxii-client/blob/master/CONTRIBUTING.md#governance-distinct-from-oasis-tc-process>`__
from the OASIS TC Process and related policies.

All contributions made to this TC Open Repository are subject to open source
license terms expressed in the `BSD-3-Clause License
<https://www.oasis-open.org/sites/www.oasis-open.org/files/BSD-3-Clause.txt>`__.
That license was selected as the declared `"Applicable License"
<https://www.oasis-open.org/resources/open-repositories/licenses>`__ when the
TC Open Repository was created.

As documented in `"Public Participation Invited
<https://github.com/oasis-open/cti-taxii-client/blob/master/CONTRIBUTING.md#public-participation-invited>`__",
contributions to this OASIS TC Open Repository are invited from all parties,
whether affiliated with OASIS or not. Participants must have a GitHub account,
but no fees or OASIS membership obligations are required. Participation is
expected to be consistent with the `OASIS TC Open Repository Guidelines and
Procedures
<https://www.oasis-open.org/policies-guidelines/open-repositories>`__, the open
source `LICENSE
<https://github.com/oasis-open/cti-taxii-client/blob/master/LICENSE>`__
designated for this particular repository, and the requirement for an
`Individual Contributor License Agreement
<https://www.oasis-open.org/resources/open-repositories/cla/individual-cla>`__
that governs intellectual property.

Maintainers
-----------

TC Open Repository `Maintainers
<https://www.oasis-open.org/resources/open-repositories/maintainers-guide>`__
are responsible for oversight of this project's community development
activities, including evaluation of GitHub `pull requests
<https://github.com/oasis-open/cti-taxii-client/blob/master/CONTRIBUTING.md#fork-and-pull-collaboration-model>`__
and `preserving
<https://www.oasis-open.org/policies-guidelines/open-repositories#repositoryManagement>`__
open source principles of openness and fairness. Maintainers are recognized and
trusted experts who serve to implement community goals and consensus design
preferences.

Initially, the associated TC members have designated one or more persons to
serve as Maintainer(s); subsequently, participating community members may select
additional or substitute Maintainers, per `consensus agreements
<https://www.oasis-open.org/resources/open-repositories/maintainers-guide#additionalMaintainers>`__.

Current Maintainers of this TC Open Repository
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  `Chris Lenk <mailto:clenk@mitre.org>`__; GitHub ID:
   https://github.com/clenk/; WWW: `MITRE
   Corporation <https://www.mitre.org/>`__
-  `Rich Piazza <mailto:rpiazza@mitre.org>`__; GitHub ID:
   https://github.com/rpiazza/; WWW: `MITRE
   Corporation <https://www.mitre.org/>`__
-  `Jason Keirstead <mailto:Jason.Keirstead@ca.ibm.com>`__; GitHub ID:
   https://github.com/JasonKeirstead; WWW: `IBM <http://www.ibm.com/>`__

About OASIS TC Open Repositories
--------------------------------

-  `TC Open Repositories: Overview and
   Resources <https://www.oasis-open.org/resources/open-repositories/>`__
-  `Frequently Asked
   Questions <https://www.oasis-open.org/resources/open-repositories/faq>`__
-  `Open Source
   Licenses <https://www.oasis-open.org/resources/open-repositories/licenses>`__
-  `Contributor License Agreements
   (CLAs) <https://www.oasis-open.org/resources/open-repositories/cla>`__
-  `Maintainers' Guidelines and
   Agreement <https://www.oasis-open.org/resources/open-repositories/maintainers-guide>`__

Feedback
--------

Questions or comments about this TC Open Repository's activities should be composed
as GitHub issues or comments. If use of an issue/comment is not possible or
appropriate, questions may be directed by email to the Maintainer(s) `listed
above <#currentMaintainers>`__. Please send general questions about Open
Repository participation to OASIS Staff at repository-admin@oasis-open.org and
any specific CLA-related questions to repository-cla@oasis-open.org.

.. |Build_Status| image:: https://github.com/oasis-open/cti-taxii-client/workflows/cti-taxii-client%20test%20harness/badge.svg
   :target: https://github.com/oasis-open/cti-taxii-client/actions?query=workflow%3A%22cti-taxii-client+test+harness%22
.. |Coverage| image:: https://codecov.io/gh/oasis-open/cti-taxii-client/branch/master/graph/badge.svg
   :target: https://codecov.io/gh/oasis-open/cti-taxii-client
.. |Version| image:: https://img.shields.io/pypi/v/taxii2-client.svg?maxAge=3600
   :target: https://pypi.python.org/pypi/taxii2-client/
