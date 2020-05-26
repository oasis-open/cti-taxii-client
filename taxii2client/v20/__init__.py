"""Python TAXII 2.0 Client API"""

from __future__ import unicode_literals

import json
import logging
import time

import six
import six.moves.urllib.parse as urlparse

from .. import MEDIA_TYPE_STIX_V20, MEDIA_TYPE_TAXII_V20
from ..common import (
    _filter_kwargs_to_query_params, _grab_total_items, _TAXIIEndpoint,
    _to_json
)
from ..exceptions import AccessError, ValidationError

# Module-level logger
log = logging.getLogger(__name__)
log.propagate = False

formatter = logging.Formatter("[%(name)s] [%(levelname)s] [%(asctime)s] %(message)s")

# Console Handler for taxii2client messages
ch = logging.StreamHandler()
ch.setFormatter(formatter)
log.addHandler(ch)


def as_pages(func, start=0, per_request=0, *args, **kwargs):
    """Creates a generator for TAXII 2.0 endpoints that support pagination."""
    resp = func(start=start, per_request=per_request, *args, **kwargs)
    yield _to_json(resp)
    total_obtained, total_available = _grab_total_items(resp)

    if total_obtained != per_request:
        log.warning("TAXII Server response with different amount of objects! Setting per_request=%s", total_obtained)
        per_request = total_obtained

    start += per_request
    while start < total_available:

        resp = func(start=start, per_request=per_request, *args, **kwargs)
        yield _to_json(resp)

        total_in_request, total_available = _grab_total_items(resp)
        total_obtained += total_in_request
        start += per_request


class Status(_TAXIIEndpoint):
    """TAXII Status Resource.

    This class represents the ``Get Status`` endpoint (section 4.3) and also
    contains the information about the Status Resource (section 4.3.1)

    """
    # We don't need to jump through the same lazy-load as with Collection,
    # since it's *far* less likely people will create these manually rather
    # than just getting them returned from Collection.add_objects(), and there
    # aren't other endpoints to call on the Status object.

    def __init__(self, url, conn=None, user=None, password=None, verify=True,
                 proxies=None, status_info=None, auth=None):
        """Create an API root resource endpoint.

        Args:
            url (str): URL of a TAXII status resource endpoint
            user (str): username for authentication (optional)
            password (str): password for authentication (optional)
            conn (_HTTPConnection): reuse connection object, as an alternative
                to providing username/password
            status_info (dict): Parsed JSON representing a response from the
                status endpoint, if already known.  If not given, the
                endpoint will be queried. (optional)
            verify (bool): validate the entity credentials. (default: True)
            proxies (dict): key/value pair for http/https proxy settings.
                (optional)

        """
        super(Status, self).__init__(url, conn, user, password, verify, proxies, auth=auth)
        self.__raw = None
        if status_info:
            self._populate_fields(**status_info)
            self.__raw = status_info
        else:
            self.refresh()

    def __nonzero__(self):
        return self.status == "complete"

    __bool__ = __nonzero__

    @property
    def _raw(self):
        """Get the "raw" status response (parsed JSON)."""
        return self.__raw

    @property
    def custom_properties(self):
        return self._custom_properties

    def refresh(self, accept=MEDIA_TYPE_TAXII_V20):
        """Updates Status information"""
        response = self.__raw = self._conn.get(self.url,
                                               headers={"Accept": accept})
        self._populate_fields(**response)

    def wait_until_final(self, poll_interval=1, timeout=60):
        """It will poll the URL to grab the latest status resource in a given
        timeout and time interval.

        Args:
            poll_interval (int): how often to poll the status service.
            timeout (int): how long to poll the URL until giving up. Use <= 0
                to wait forever

        """
        start_time = time.time()
        elapsed = 0
        while (self.status != "complete" and
                (timeout <= 0 or elapsed < timeout)):
            time.sleep(poll_interval)
            self.refresh()
            elapsed = time.time() - start_time

    def _populate_fields(self, id=None, status=None, total_count=None,
                         success_count=None, failure_count=None,
                         pending_count=None, request_timestamp=None,
                         successes=None, failures=None, pendings=None,
                         **kwargs):
        self.id = id  # required
        self.status = status  # required
        self.request_timestamp = request_timestamp  # optional
        self.total_count = total_count  # required
        self.success_count = success_count  # required
        self.failure_count = failure_count  # required
        self.pending_count = pending_count  # required
        self.successes = successes or []  # optional
        self.failures = failures or []  # optional
        self.pendings = pendings or []  # optional

        # Anything not captured by the optional arguments is treated as custom
        self._custom_properties = kwargs

        self._validate_status()

    def _validate_status(self):
        """Validates Status information. Raises errors for required
        properties."""
        if not self.id:
            msg = "No 'id' in Status for request '{}'"
            raise ValidationError(msg.format(self.url))

        if not self.status:
            msg = "No 'status' in Status for request '{}'"
            raise ValidationError(msg.format(self.url))

        if self.total_count is None:
            msg = "No 'total_count' in Status for request '{}'"
            raise ValidationError(msg.format(self.url))

        if self.success_count is None:
            msg = "No 'success_count' in Status for request '{}'"
            raise ValidationError(msg.format(self.url))

        if self.failure_count is None:
            msg = "No 'failure_count' in Status for request '{}'"
            raise ValidationError(msg.format(self.url))

        if self.pending_count is None:
            msg = "No 'pending_count' in Status for request '{}'"
            raise ValidationError(msg.format(self.url))

        if len(self.successes) != self.success_count:
            msg = "Found successes={}, but success_count={} in status '{}'"
            raise ValidationError(msg.format(self.successes,
                                             self.success_count,
                                             self.id))

        if len(self.pendings) != self.pending_count:
            msg = "Found pendings={}, but pending_count={} in status '{}'"
            raise ValidationError(msg.format(self.pendings,
                                             self.pending_count,
                                             self.id))

        if len(self.failures) != self.failure_count:
            msg = "Found failures={}, but failure_count={} in status '{}'"
            raise ValidationError(msg.format(self.failures,
                                             self.failure_count,
                                             self.id))

        if (self.success_count + self.pending_count + self.failure_count !=
                self.total_count):
            msg = ("(success_count={} + pending_count={} + "
                   "failure_count={}) != total_count={} in status '{}'")
            raise ValidationError(msg.format(self.success_count,
                                             self.pending_count,
                                             self.failure_count,
                                             self.total_count,
                                             self.id))


class Collection(_TAXIIEndpoint):
    """Information about a TAXII Collection.

    This class represents the ``Get a Collection`` endpoint (section 5.2), and
    contains the information returned in the ``Collection Resource`` (section
    5.2.1).

    Methods on this class can be used to invoke the following endpoints:
        - ``Get Objects`` (section 5.3)
        - ``Add Objects`` (section 5.4)
        - ``Get an Object`` (section 5.5)
        - ``Get Object Manifests`` (section 5.6)

    As obtained from an ApiRoot, an instance of this class shares connection(s)
    with all other collections obtained from the same ApiRoot, as well as the
    ApiRoot instance itself.  Closing one will close them all.  If this is
    undesirable, you may manually create Collection instances.

    """

    def __init__(self, url, conn=None, user=None, password=None, verify=True,
                 proxies=None, collection_info=None, auth=None):
        """
        Initialize a new Collection.  Either user/password or conn may be
        given, but not both.  The latter is intended for internal use, when
        sharing connection pools with an ApiRoot, mocking a connection for
        testing, etc.  Users should use user/password (if required) which will
        create a new connection.

        Args:
            url (str): A TAXII endpoint for a collection
            user (str): User name for authentication (optional)
            password (str): Password for authentication (optional)
            verify (bool): Either a boolean, in which case it controls whether
                we verify the server's TLS certificate, or a string, in which
                case it must be a path to a CA bundle to use. Defaults to
                `True` (optional)
            conn (_HTTPConnection): A connection to reuse (optional)
            collection_info: Collection metadata, if known in advance (optional)
            verify (bool): validate the entity credentials. (default: True)
            proxies (dict): key/value pair for http/https proxy settings.
                (optional)

        """

        super(Collection, self).__init__(url, conn, user, password, verify, proxies, auth=auth)

        self._loaded = False
        self.__raw = None

        # Since the API Root "Get Collections" endpoint returns information on
        # all collections as a list, it's possible that we can create multiple
        # Collection objects from a single HTTPS request, and not need to call
        # `refresh` for each one.
        if collection_info:
            self._populate_fields(**collection_info)
            self.__raw = collection_info
            self._loaded = True

    @property
    def id(self):
        self._ensure_loaded()
        return self._id

    @property
    def title(self):
        self._ensure_loaded()
        return self._title

    @property
    def description(self):
        self._ensure_loaded()
        return self._description

    @property
    def can_read(self):
        self._ensure_loaded()
        return self._can_read

    @property
    def can_write(self):
        self._ensure_loaded()
        return self._can_write

    @property
    def media_types(self):
        self._ensure_loaded()
        return self._media_types

    @property
    def custom_properties(self):
        self._ensure_loaded()
        return self._custom_properties

    @property
    def objects_url(self):
        return self.url + "objects/"

    @property
    def manifest_url(self):
        return self.url + "manifest/"

    @property
    def _raw(self):
        """Get the "raw" collection information response (parsed JSON)."""
        self._ensure_loaded()
        return self.__raw

    def _populate_fields(self, id=None, title=None, description=None,
                         can_read=None, can_write=None, media_types=None,
                         **kwargs):
        self._id = id  # required
        self._title = title  # required
        self._description = description  # optional
        self._can_read = can_read  # required
        self._can_write = can_write  # required
        self._media_types = media_types or []  # optional

        # Anything not captured by the optional arguments is treated as custom
        self._custom_properties = kwargs

        self._validate_collection()

    def _validate_collection(self):
        """Validates Collection information. Raises errors for required
        properties."""
        if not self._id:
            msg = "No 'id' in Collection for request '{}'"
            raise ValidationError(msg.format(self.url))

        if not self._title:
            msg = "No 'title' in Collection for request '{}'"
            raise ValidationError(msg.format(self.url))

        if self._can_read is None:
            msg = "No 'can_read' in Collection for request '{}'"
            raise ValidationError(msg.format(self.url))

        if self._can_write is None:
            msg = "No 'can_write' in Collection for request '{}'"
            raise ValidationError(msg.format(self.url))

        if self._id not in self.url:
            msg = "The collection '{}' does not match the url for queries '{}'"
            raise ValidationError(msg.format(self._id, self.url))

    def _ensure_loaded(self):
        if not self._loaded:
            self.refresh()

    def _verify_can_read(self):
        if not self.can_read:
            msg = "Collection '{}' does not allow reading."
            raise AccessError(msg.format(self.url))

    def _verify_can_write(self):
        if not self.can_write:
            msg = "Collection '{}' does not allow writing."
            raise AccessError(msg.format(self.url))

    def refresh(self, accept=MEDIA_TYPE_TAXII_V20):
        """Update Collection information"""
        response = self.__raw = self._conn.get(self.url,
                                               headers={"Accept": accept})
        self._populate_fields(**response)
        self._loaded = True

    def get_objects(self, accept=MEDIA_TYPE_STIX_V20, start=0, per_request=0, **filter_kwargs):
        """Implement the ``Get Objects`` endpoint (section 5.3). For pagination requests use ``as_pages`` method."""
        self._verify_can_read()
        query_params = _filter_kwargs_to_query_params(filter_kwargs)
        headers = {"Accept": accept}

        if per_request > 0:
            headers["Range"] = "items {}-{}".format(start, (start + per_request) - 1)

        return self._conn.get(self.objects_url, headers=headers, params=query_params)

    def get_object(self, obj_id, version=None, accept=MEDIA_TYPE_STIX_V20):
        """Implement the ``Get an Object`` endpoint (section 5.5)"""
        self._verify_can_read()
        url = self.objects_url + str(obj_id) + "/"
        query_params = None
        if version:
            query_params = _filter_kwargs_to_query_params({"version": version})
        return self._conn.get(url, headers={"Accept": accept}, params=query_params)

    def add_objects(self, bundle, wait_for_completion=True, poll_interval=1,
                    timeout=60, accept=MEDIA_TYPE_TAXII_V20,
                    content_type=MEDIA_TYPE_STIX_V20):
        """Implement the ``Add Objects`` endpoint (section 5.4)

        Add objects to the collection.  This may be performed either
        synchronously or asynchronously.  To add asynchronously, set
        wait_for_completion to False.  If False, the latter two args are
        unused.  If the caller wishes to monitor the status of the addition,
        it may do so in its own way.  To add synchronously, set
        wait_for_completion to True, and optionally set the poll and timeout
        intervals.  After initiating the addition, the caller will block,
        and the TAXII "status" service will be polled until the timeout
        expires, or the operation completes.

        Args:
            bundle: A STIX bundle with the objects to add (string, dict, binary)
            wait_for_completion (bool): Whether to wait for the add operation
                to complete before returning
            poll_interval (int): If waiting for completion, how often to poll
                the status service (seconds)
            timeout (int): If waiting for completion, how long to poll until
                giving up (seconds).  Use <= 0 to wait forever
            accept (str): media type to include in the ``Accept:`` header.
            content_type (str): media type to include in the ``Content-Type:``
                header.

        Returns:
            If ``wait_for_completion`` is False, a Status object corresponding
            to the initial status data returned from the service, is returned.
            The status may not yet be complete at this point.

            If ``wait_for_completion`` is True, a Status object corresponding
            to the completed operation is returned if it didn't time out;
            otherwise a Status object corresponding to the most recent data
            obtained before the timeout, is returned.

        """
        self._verify_can_write()

        headers = {
            "Accept": accept,
            "Content-Type": content_type,
        }

        if isinstance(bundle, dict):
            json_text = json.dumps(bundle, ensure_ascii=False)
            data = json_text.encode("utf-8")

        elif isinstance(bundle, six.text_type):
            data = bundle.encode("utf-8")

        elif isinstance(bundle, six.binary_type):
            data = bundle

        else:
            raise TypeError("Don't know how to handle type '{}'".format(
                type(bundle).__name__))

        status_json = self._conn.post(self.objects_url, headers=headers,
                                      data=data)

        status_url = urlparse.urljoin(
            self.url,
            "../../status/{}".format(status_json["id"])
        )

        status = Status(url=status_url, conn=self._conn,
                        status_info=status_json)

        if not wait_for_completion or status.status == "complete":
            return status

        status.wait_until_final(poll_interval, timeout)

        return status

    def get_manifest(self, accept=MEDIA_TYPE_TAXII_V20, start=0, per_request=0, **filter_kwargs):
        """Implement the ``Get Object Manifests`` endpoint (section 5.6). For pagination requests use ``as_pages`` method."""
        self._verify_can_read()
        query_params = _filter_kwargs_to_query_params(filter_kwargs)
        headers = {"Accept": accept}

        if per_request > 0:
            headers["Range"] = "items {}-{}".format(start, (start + per_request) - 1)

        return self._conn.get(self.manifest_url, headers=headers, params=query_params)


class ApiRoot(_TAXIIEndpoint):
    """Information about a TAXII API Root.

    This class corresponds to the ``Get API Root Information`` (section 4.2)
    and ``Get Collections`` (section 5.1) endpoints, and contains the
    information found in the corresponding ``API Root Resource``
    (section 4.2.1) and ``Collections Resource`` (section 5.1.1).

    As obtained from a Server, each ApiRoot instance gets its own connection
    pool(s).  Collections returned by instances of this class share the same
    pools as the instance, so closing one closes all.  Also, the same
    username/password is used to connect to them, as was used for this ApiRoot.
    If either of these is undesirable, Collection instances may be created
    manually.

    """

    def __init__(self, url, conn=None, user=None, password=None, verify=True,
                 proxies=None, auth=None):
        """Create an API root resource endpoint.

        Args:
            url (str): URL of a TAXII API root resource endpoint
            user (str): username for authentication (optional)
            password (str): password for authentication (optional)
            conn (_HTTPConnection): reuse connection object, as an alternative
                to providing username/password
            verify (bool): validate the entity credentials. (default: True)
            proxies (dict): key/value pair for http/https proxy settings.
                (optional)

        """
        super(ApiRoot, self).__init__(url, conn, user, password, verify, proxies, auth=auth)

        self._loaded_collections = False
        self._loaded_information = False
        self.__raw = None

    @property
    def collections(self):
        if not self._loaded_collections:
            self.refresh_collections()
        return self._collections

    @property
    def title(self):
        self._ensure_loaded_information()
        return self._title

    @property
    def description(self):
        self._ensure_loaded_information()
        return self._description

    @property
    def versions(self):
        self._ensure_loaded_information()
        return self._versions

    @property
    def max_content_length(self):
        self._ensure_loaded_information()
        return self._max_content_length

    @property
    def custom_properties(self):
        self._ensure_loaded_information()
        return self._custom_properties

    @property
    def _raw(self):
        """Get the "raw" API root information response (parsed JSON)."""
        self._ensure_loaded_information()
        return self.__raw

    def _ensure_loaded_information(self):
        if not self._loaded_information:
            self.refresh_information()

    def _validate_api_root(self):
        """Validates API Root information. Raises errors for required
        properties."""
        if not self._title:
            msg = "No 'title' in API Root for request '{}'"
            raise ValidationError(msg.format(self.url))

        if not self._versions:
            msg = "No 'versions' in API Root for request '{}'"
            raise ValidationError(msg.format(self.url))

        if self._max_content_length is None:
            msg = "No 'max_content_length' in API Root for request '{}'"
            raise ValidationError(msg.format(self.url))

    def _populate_fields(self, title=None, description=None, versions=None,
                         max_content_length=None, **kwargs):
        self._title = title  # required
        self._description = description  # optional
        self._versions = versions or []  # required
        self._max_content_length = max_content_length  # required

        # Anything not captured by the optional arguments is treated as custom
        self._custom_properties = kwargs

        self._validate_api_root()

    def refresh(self, accept=MEDIA_TYPE_TAXII_V20):
        """Update the API Root's information and list of Collections"""
        self.refresh_information(accept)
        self.refresh_collections(accept)

    def refresh_information(self, accept=MEDIA_TYPE_TAXII_V20):
        """Update the properties of this API Root.

        This invokes the ``Get API Root Information`` endpoint.
        """
        response = self.__raw = self._conn.get(self.url,
                                               headers={"Accept": accept})
        self._populate_fields(**response)
        self._loaded_information = True

    def refresh_collections(self, accept=MEDIA_TYPE_TAXII_V20):
        """Update the list of Collections contained by this API Root.

        This invokes the ``Get Collections`` endpoint.
        """
        url = self.url + "collections/"
        response = self._conn.get(url, headers={"Accept": accept})

        self._collections = []
        for item in response.get("collections", []):  # optional
            collection_url = url + item["id"] + "/"
            collection = Collection(collection_url, conn=self._conn,
                                    collection_info=item)
            self._collections.append(collection)

        self._loaded_collections = True

    def get_status(self, status_id, accept=MEDIA_TYPE_TAXII_V20):
        status_url = self.url + "status/" + status_id + "/"
        response = self._conn.get(status_url, headers={"Accept": accept})
        return Status(status_url, conn=self._conn, status_info=response)


class Server(_TAXIIEndpoint):
    """Information about a server hosting a Discovery service.

    This class corresponds to the Server Discovery endpoint (section 4.1) and
    the Discovery Resource returned from that endpoint (section 4.1.1).

    ApiRoot instances obtained from an instance of this class are
    created with the same username/password as was used in this instance.  If
    that's incorrect, an ApiRoot instance may be created directly with the
    desired username and password.  Also, they use separate connection pools
    so that they can be independent: closing one won't close others, and
    closing this server object won't close any of the ApiRoot objects (which
    may refer to different hosts than was used for discovery).

    """

    def __init__(self, url, conn=None, user=None, password=None, verify=True,
                 proxies=None, auth=None):
        """Create a server discovery endpoint.

        Args:
            url (str): URL of a TAXII server discovery endpoint
            user (str): username for authentication (optional)
            password (str): password for authentication (optional)
            conn (_HTTPConnection): reuse connection object, as an alternative
                to providing username/password
            verify (bool): validate the entity credentials. (default: True)
            proxies (dict): key/value pair for http/https proxy settings.
                (optional)

        """
        super(Server, self).__init__(url, conn, user, password, verify, proxies, auth=auth)

        self._user = user
        self._password = password
        self._verify = verify
        self._proxies = proxies
        self._loaded = False
        self.__raw = None
        self._auth = auth

    @property
    def title(self):
        self._ensure_loaded()
        return self._title

    @property
    def description(self):
        self._ensure_loaded()
        return self._description

    @property
    def contact(self):
        self._ensure_loaded()
        return self._contact

    @property
    def default(self):
        self._ensure_loaded()
        return self._default

    @property
    def api_roots(self):
        self._ensure_loaded()
        return self._api_roots

    @property
    def custom_properties(self):
        self._ensure_loaded()
        return self._custom_properties

    @property
    def _raw(self):
        """Get the "raw" server discovery response (parsed JSON)."""
        self._ensure_loaded()
        return self.__raw

    def _ensure_loaded(self):
        if not self._loaded:
            self.refresh()

    def _validate_server(self):
        """Validates server information. Raises errors for required properties.
        """
        if not self._title:
            msg = "No 'title' in Server Discovery for request '{}'"
            raise ValidationError(msg.format(self.url))

    def _populate_fields(self, title=None, description=None, contact=None,
                         api_roots=None, default=None, **kwargs):
        self._title = title  # required
        self._description = description  # optional
        self._contact = contact  # optional
        roots = api_roots or []  # optional
        self._api_roots = [ApiRoot(url,
                                   user=self._user,
                                   password=self._password,
                                   verify=self._verify,
                                   proxies=self._proxies,
                                   auth=self._auth)
                           for url in roots]
        # If 'default' is one of the existing API Roots, reuse that object
        # rather than creating a duplicate. The TAXII 2.0 spec says that the
        # `default` API Root MUST be an item in `api_roots`.
        root_dict = dict(zip(roots, self._api_roots))
        self._default = root_dict.get(default)  # optional

        # Anything not captured by the optional arguments is treated as custom
        self._custom_properties = kwargs

        self._validate_server()

    def refresh(self):
        """Update the Server information and list of API Roots"""
        response = self.__raw = self._conn.get(self.url)
        self._populate_fields(**response)
        self._loaded = True
