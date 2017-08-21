====================
`cti-taxii-client`
====================

NOTE: This is an `OASIS Open Repository <https://www.oasis-open.org/resources/open-repositories/>`_. See the `Governance`_ section for more information.

cti-taxii-client is a minimal implementation of client for the TAXII 2.0 server.  It supports the following TAXII 2.0 API services:

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

The TAXII client is intended to be used as a Python library.  There is no support to run it independently.

.. code:: python

  import taxii2client

  client = taxii2client.TAXII2Client("http://taxii_server", "user_id", "user_password")

The authorization information is stored in the TAXII client instance, so it need not be supplied explicitly when request services.

Once you have instantiated a TAXII client, you can get all meta data about the contents of the TAXII server as follows:

.. code:: python

  client.populate_available_information()

This will cache the server's information in the client instance in instance variables:

- api_roots
- title
- description
- default_api_root

Each api_root found on the server will be instantiated with its meta data

- name
- collections
- information

Each collection found in an api_root will be instantiated with its meta data

- media_types
- title
- can_write
- can_read
- description

Governance
==========

This GitHub public repository (
**https://github.com/oasis-open/cti-taxii-client** ) was created at the
request of the `OASIS Cyber Threat Intelligence (CTI)
TC <https://www.oasis-open.org/committees/cti/>`__ as an `OASIS Open
Repository <https://www.oasis-open.org/resources/open-repositories/>`__
to support development of open source resources related to Technical
Committee work.

While this Open Repository remains associated with the sponsor TC, its
development priorities, leadership, intellectual property terms,
participation rules, and other matters of governance are `separate and
distinct <https://github.com/oasis-open/cti-taxii-client/blob/master/CONTRIBUTING.md#governance-distinct-from-oasis-tc-process>`__
from the OASIS TC Process and related policies.

All contributions made to this Open Repository are subject to open
source license terms expressed in the `BSD-3-Clause
License <https://www.oasis-open.org/sites/www.oasis-open.org/files/BSD-3-Clause.txt>`__.
That license was selected as the declared `"Applicable
License" <https://www.oasis-open.org/resources/open-repositories/licenses>`__
when the Open Repository was created.

As documented in `"Public Participation
Invited <https://github.com/oasis-open/cti-taxii-client/blob/master/CONTRIBUTING.md#public-participation-invited>`__",
contributions to this OASIS Open Repository are invited from all
parties, whether affiliated with OASIS or not. Participants must have a
GitHub account, but no fees or OASIS membership obligations are
required. Participation is expected to be consistent with the `OASIS
Open Repository Guidelines and
Procedures <https://www.oasis-open.org/policies-guidelines/open-repositories>`__,
the open source
`LICENSE <https://github.com/oasis-open/cti-taxii-client/blob/master/LICENSE>`__
designated for this particular repository, and the requirement for an
`Individual Contributor License
Agreement <https://www.oasis-open.org/resources/open-repositories/cla/individual-cla>`__
that governs intellectual property.

.. raw:: html

   </div>

.. raw:: html

   <div>

.. rubric:: Statement of Purpose
   :name: statement-of-purpose

Statement of Purpose for this OASIS Open Repository (cti-taxii-client)
as
`proposed <https://lists.oasis-open.org/archives/cti/201707/msg00000.html>`__
and
`approved <https://lists.oasis-open.org/archives/cti/201707/msg00001.html>`__
[`bis <https://issues.oasis-open.org/browse/TCADMIN-2623>`__] by the TC:

The taxii-client under development in this GitHub repository is a Python
library and command line tool for making HTTPS requests to TAXII servers
in conformance with the TAXII specification.

.. raw:: html

   </div>

.. raw:: html

   <div>

.. rubric:: Additions to Statement of Purpose
   :name: additions-to-statement-of-purpose

Repository Maintainers may include here any clarifications — any
additional sections, subsections, and paragraphs that the Maintainer(s)
wish to add as descriptive text, reflecting (sub-) project status,
milestones, releases, modifications to statement of purpose, etc. The
project Maintainers will create and maintain this content on behalf of
the participants.

`Maintainers`
=============

Open Repository
`Maintainers <https://www.oasis-open.org/resources/open-repositories/maintainers-guide>`__
are responsible for oversight of this project's community development
activities, including evaluation of GitHub `pull
requests <https://github.com/oasis-open/cti-taxii-client/blob/master/CONTRIBUTING.md#fork-and-pull-collaboration-model>`__
and
`preserving <https://www.oasis-open.org/policies-guidelines/open-repositories#repositoryManagement>`__
open source principles of openness and fairness. Maintainers are
recognized and trusted experts who serve to implement community goals
and consensus design preferences.

Initially, the associated TC members have designated one or more persons
to serve as Maintainer(s); subsequently, participating community members
may select additional or substitute Maintainers, per `consensus
agreements <https://www.oasis-open.org/resources/open-repositories/maintainers-guide#additionalMaintainers>`__.

**Current Maintainers of this Open Repository**

-  `Greg Back <mailto:gback@mitre.org>`__; GitHub ID:
   https://github.com/gtback/; WWW: `MITRE
   Corporation <https://www.mitre.org/>`__
-  `Rich Piazza <mailto:rpiazza@mitre.org>`__; GitHub ID:
   https://github.com/rpiazza/; WWW: `MITRE
   Corporation <https://www.mitre.org/>`__

.. raw:: html

   </div>

.. raw:: html

   <div>

.. rubric:: About OASIS Open Repositories
   :name: about-oasis-open-repositories

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

.. raw:: html

   </div>

.. raw:: html

   <div>

.. rubric:: Feedback
   :name: feedback

Questions or comments about this Open Repository's activities should be
composed as GitHub issues or comments. If use of an issue/comment is not
possible or appropriate, questions may be directed by email to the
Maintainer(s) `listed above <#currentMaintainers>`__. Please send
general questions about Open Repository participation to OASIS Staff at
repository-admin@oasis-open.org and any specific CLA-related questions
to repository-cla@oasis-open.org.

.. raw:: html

   </div>

.. raw:: html

   </div>
