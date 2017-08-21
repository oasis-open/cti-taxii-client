====================
`cti-taxii-client`
====================

NOTE: This is an `OASIS Open Repository
<https://www.oasis-open.org/resources/open-repositories/>`_. See the
`Governance`_ section for more information.

cti-taxii-client is a minimal implementation of client for the TAXII 2.0 server.
It supports the following TAXII 2.0 API services:

- Server Discovery
- Get API Root Information
- Get Status
- Get Collections
- Get a Collection
- Get Objects
- Add Objects
- Get an Object
- Get Object Manifests

`Installation`
==============

The easiest way to install the TAXII client is with pip::

  $ pip install taxii2-client


`Usage`
=======

The TAXII client is intended to be used as a Python library.  There are no
command line clients at this time.

``taxii2-client`` provides four classes:

- ``Server``
- ``ApiRoot``
- ``Collection``
- ``Status``

Each can be instantiated by passing a `url`, and (optional) `user` and
`password` arguments.

.. code:: python

  from taxii2client import Collection
  collection = Collection('https://example.com/api1/collections/91a7b528-80eb-42ed-a74d-c6fbd5a26116')
  collection.get_object('indicator--252c7c11-daf2-42bd-843b-be65edca9f61')

You can also traverse parent-to-child relationships directly:

.. code:: python

  from taxii2client import Server
  server = Server('https://example.com/taxii/', 'user_id', 'user_password')
  api_root = server.api_roots[0]
  collection = api_root.collections[0]
  collection.add_objects(stix_bundle)

In addition to the object-specific properties and methods, all classes have a
``refresh()`` method that reloads the URL corresponding to that resource, to
ensure properties have the most up-to-date values.


Governance
==========

This GitHub public repository (
**https://github.com/oasis-open/cti-taxii-client** ) was created at the request
of the `OASIS Cyber Threat Intelligence (CTI) TC
<https://www.oasis-open.org/committees/cti/>`__ as an `OASIS Open Repository
<https://www.oasis-open.org/resources/open-repositories/>`__ to support
development of open source resources related to Technical Committee work.

While this Open Repository remains associated with the sponsor TC, its
development priorities, leadership, intellectual property terms, participation
rules, and other matters of governance are `separate and distinct
<https://github.com/oasis-open/cti-taxii-client/blob/master/CONTRIBUTING.md#governance-distinct-from-oasis-tc-process>`__
from the OASIS TC Process and related policies.

All contributions made to this Open Repository are subject to open source
license terms expressed in the `BSD-3-Clause License
<https://www.oasis-open.org/sites/www.oasis-open.org/files/BSD-3-Clause.txt>`__.
That license was selected as the declared `"Applicable License"
<https://www.oasis-open.org/resources/open-repositories/licenses>`__ when the
Open Repository was created.

As documented in `"Public Participation Invited
<https://github.com/oasis-open/cti-taxii-client/blob/master/CONTRIBUTING.md#public-participation-invited>`__",
contributions to this OASIS Open Repository are invited from all parties,
whether affiliated with OASIS or not. Participants must have a GitHub account,
but no fees or OASIS membership obligations are required. Participation is
expected to be consistent with the `OASIS Open Repository Guidelines and
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

Open Repository `Maintainers
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

Current Maintainers of this Open Repository
-------------------------------------------

-  `Greg Back <mailto:gback@mitre.org>`__; GitHub ID:
   https://github.com/gtback/; WWW: `MITRE
   Corporation <https://www.mitre.org/>`__
-  `Rich Piazza <mailto:rpiazza@mitre.org>`__; GitHub ID:
   https://github.com/rpiazza/; WWW: `MITRE
   Corporation <https://www.mitre.org/>`__

About OASIS Open Repositories
-----------------------------

-  `Open Repositories: Overview and
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

Questions or comments about this Open Repository's activities should be composed
as GitHub issues or comments. If use of an issue/comment is not possible or
appropriate, questions may be directed by email to the Maintainer(s) `listed
above <#currentMaintainers>`__. Please send general questions about Open
Repository participation to OASIS Staff at repository-admin@oasis-open.org and
any specific CLA-related questions to repository-cla@oasis-open.org.
