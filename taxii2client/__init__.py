from __future__ import unicode_literals

import datetime
import json
import time

import pytz
import requests
import six
import six.moves.urllib.parse as urlparse

MEDIA_TYPE_STIX_V20 = "application/vnd.oasis.stix+json; version=2.0"
MEDIA_TYPE_TAXII_V20 = "application/vnd.oasis.taxii+json; version=2.0"


class TAXIIServiceException(Exception):
    """Base class for exceptions raised by this library."""
    pass


class InvalidArgumentsError(TAXIIServiceException):
    """Invalid arguments were passed to a method."""
    pass


class AccessError(TAXIIServiceException):
    """Attempt was made to read/write to a collection when the collection
    doesn't allow that operation."""
    pass


def _format_datetime(dttm):
    """Convert a datetime object into a valid STIX timestamp string.

    1. Convert to timezone-aware
    2. Convert to UTC
    3. Format in ISO format
    4. Ensure correct precision
       a. Add subsecond value if non-zero and precision not defined
    5. Add "Z"

    """

    if dttm.tzinfo is None or dttm.tzinfo.utcoffset(dttm) is None:
        # dttm is timezone-naive; assume UTC
        zoned = pytz.utc.localize(dttm)
    else:
        zoned = dttm.astimezone(pytz.utc)
    ts = zoned.strftime("%Y-%m-%dT%H:%M:%S")
    ms = zoned.strftime("%f")
    precision = getattr(dttm, "precision", None)
    if precision == 'second':
        pass  # Already precise to the second
    elif precision == "millisecond":
        ts = ts + '.' + ms[:3]
    elif zoned.microsecond > 0:
        ts = ts + '.' + ms.rstrip("0")
    return ts + "Z"


def _ensure_datetime_to_string(maybe_dttm):
    """If maybe_dttm is a datetime instance, convert to a STIX-compliant
    string representation.  Otherwise return the value unchanged."""
    if isinstance(maybe_dttm, datetime.datetime):
        maybe_dttm = _format_datetime(maybe_dttm)
    return maybe_dttm


def _filter_kwargs_to_query_params(filter_kwargs):
    """
    Convert API keyword args to a mapping of URL query parameters.  Except for
    "added_after", all keywords are mapped to match filters, i.e. to a query
    parameter of the form "match[<kwarg>]".  "added_after" is left alone, since
    it's a special filter, as defined in the spec.

    Each value can be a single value or iterable of values.  "version" and
    "added_after" get special treatment, since they are timestamp-valued:
    datetime.datetime instances are supported and automatically converted to
    STIX-compliant strings.  Other than that, all values must be strings.  None
    values, empty lists, etc are silently ignored.

    :param filter_kwargs: The filter information, as a mapping
    :return: The query parameter map, mapping strings to strings.
    """
    query_params = {}
    for kwarg, arglist in six.iteritems(filter_kwargs):
        # If user passes an empty list, None, etc, silently skip?
        if not arglist:
            continue

        # force iterability, for the sake of code uniformity
        if not hasattr(arglist, "__iter__") or \
                isinstance(arglist, six.string_types):
            arglist = arglist,

        if kwarg == "version":
            query_params["match[version]"] = ",".join(
                _ensure_datetime_to_string(val) for val in arglist
            )

        elif kwarg == "added_after":
            if len(arglist) > 1:
                raise InvalidArgumentsError('No more than one value for filter'
                                            ' "added_after" may be given')

            query_params["added_after"] = ",".join(
                _ensure_datetime_to_string(val) for val in arglist
            )

        else:
            query_params["match["+kwarg+"]"] = ",".join(arglist)

    return query_params


class _TAXIIEndpoint(object):
    """Contains some data and functionality common to all TAXII endpoint
    classes: a URL, connection, and ability to close the connection.  It also
    yields support in subclasses for use as contextmanagers, to ensure
    resources are released.
    """
    def __init__(self, url, user=None, password=None, verify=True, conn=None):
        if conn and (user or password):
            raise InvalidArgumentsError("A connection and user/password may"
                                        " not both be provided.")
        elif conn:
            self._conn = conn
        else:
            self._conn = _HTTPConnection(user, password, verify)

        self.url = url

    def close(self):
        self._conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False


class Status(_TAXIIEndpoint):
    """TAXII Status Resource"""
    # We don't need to jump through the same lazy-load as with Collection, since
    # it's *far* less likely people will create these manually rather than
    # just getting them returned from Collection.add_objects(), and there aren't
    # other endpoints to call on the Status object.

    def __init__(self, url, user=None, password=None, conn=None, **kwargs):
        super(Status, self).__init__(url, user, password, conn)
        if kwargs:
            self._populate_fields(**kwargs)
        else:
            self.refresh()

    def __nonzero__(self):
        return self.status == "complete"
    __bool__ = __nonzero__

    def refresh(self):
        response = self._conn.get(self.url, accept=MEDIA_TYPE_TAXII_V20)
        self._populate_fields(**response)

    def _populate_fields(self, id, status, total_count, success_count,
                         failure_count, pending_count, request_timestamp=None,
                         successes=None, failures=None, pendings=None):
        self.id = id
        self.status = status
        self.total_count = total_count
        self.success_count = success_count
        self.failure_count = failure_count
        self.pending_count = pending_count
        # TODO: validate that len(successes) == success_count, etc.
        self.successes = successes or []
        self.failures = failures or []
        self.pendings = pendings or []


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

    def __init__(self, url, user=None, password=None, verify=True, conn=None, **kwargs):
        """
        Initialize a new Collection.  Either user/password or conn may be
        given, but not both.  The latter is intended for internal use, when
        sharing connection pools with an ApiRoot, mocking a connection for
        testing, etc.  Users should use user/password (if required) which will
        create a new connection.

        :param url: A TAXII endpoint for a collection
        :param user: User name for authentication (optional)
        :param password: Password for authentication (optional)
        :param verify: Either a boolean, in which case it controls whether we verify
            the server's TLS certificate, or a string, in which case it must be a path
            to a CA bundle to use. Defaults to `True` (optional)
        :param conn: A _HTTPConnection to reuse (optional)
        :param kwargs: Collection metadata, if known in advance (optional)
        """

        super(Collection, self).__init__(url, user, password, verify, conn)

        self._loaded = False

        # Since the API Root "Get Collections" endpoint returns information on
        # all collections as a list, it's possible that we can create multiple
        # Collection objects from a single HTTPS request, and not need to call
        # `refresh` for each one.
        if kwargs:
            self._populate_fields(**kwargs)
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
    def objects_url(self):
        return self.url + 'objects/'

    def _populate_fields(self, id=None, title=None, description=None,
                         can_read=None, can_write=None, media_types=None):
        if media_types is None:
            media_types = []
        self._id = id
        # TODO: ensure id doesn't change (or at least matches self.url)
        self._title = title
        self._description = description
        self._can_read = can_read
        self._can_write = can_write
        self._media_types = media_types

    def _ensure_loaded(self):
        if not self._loaded:
            self.refresh()

    def _verify_can_read(self):
        if not self.can_read:
            raise AccessError("Collection '%s' does not allow reading." % self.url)

    def _verify_can_write(self):
        if not self.can_write:
            raise AccessError("Collection '%s' does not allow writing." % self.url)

    def refresh(self):
        response = self._conn.get(self.url, accept=MEDIA_TYPE_TAXII_V20)
        self._populate_fields(**response)

        self._loaded = True

    def get_objects(self, **filter_kwargs):
        """Implement the ``Get Objects`` endpoint (section 5.3)"""
        self._verify_can_read()
        query_params = _filter_kwargs_to_query_params(filter_kwargs)
        return self._conn.get(self.objects_url, accept=MEDIA_TYPE_STIX_V20,
                              params=query_params)

    def get_object(self, obj_id, version=None):
        """Implement the ``Get an Object`` endpoint (section 5.5)"""
        self._verify_can_read()
        url = self.objects_url + str(obj_id) + '/'
        query_params = None
        if version:
            query_params = _filter_kwargs_to_query_params({"version": version})
        return self._conn.get(url, accept=MEDIA_TYPE_STIX_V20,
                              params=query_params)

    def add_objects(self, bundle, wait_for_completion=True, poll_interval=1,
                    timeout=60):
        """Implement the ``Add Objects`` endpoint (sectdion 5.4)

        Add objects to the collection.  This may be performed either
        synchronously or asynchronously.  To add asynchronously, set
        wait_for_completion to False.  If False, the latter two args are
        unused.  If the caller wishes to monitor the status of the addition,
        it may do so in its own way.  To add synchronously, set
        wait_for_completion to True, and optionally set the poll and timeout
        intervals.  After initiating the addition, the caller will block,
        and the TAXII "status" service will be polled until the timeout
        expires, or the operation completes.

        :param bundle: A STIX bundle with the objects to add (JSON as it would
            be parsed into native Python).
        :param wait_for_completion: Whether to wait for the add operation to
            complete before returning
        :param poll_interval: If waiting for completion, how often to poll
            the status service (seconds)
        :param timeout: If waiting for completion, how long to poll until
            giving up (seconds).  Use <= 0 to wait forever.
        :return: If wait_for_completion is False, a Status object corresponding
            to the initial status data returned from the service, is returned.
            The status may not yet be complete at this point.  If
            wait_for_completion is True, a Status object corresponding to the
            completed operation is returned if it didn't time out; otherwise
            a Status object corresponding to the most recent data obtained
            before the timeout, is returned.
        """
        self._verify_can_write()

        headers = {
            "Accept": MEDIA_TYPE_TAXII_V20,
            "Content-Type": MEDIA_TYPE_STIX_V20,
        }

        if isinstance(bundle, dict):
            if six.PY2:
                bundle = json.dumps(bundle, encoding="utf-8")
            else:
                bundle = json.dumps(bundle)

        status_json = self._conn.post(self.objects_url, headers=headers,
                                      data=bundle)

        status_url = urlparse.urljoin(self.url, "../../status/{}".format(
            status_json["id"]))

        status = Status(url=status_url, conn=self._conn, **status_json)

        if not wait_for_completion or status.status == "complete":
            return status

        # TODO: consider moving this to a "Status.wait_until_final()" function.
        start_time = time.time()
        elapsed = 0
        while status.status != "complete" and \
                (timeout <= 0 or elapsed < timeout):
            time.sleep(poll_interval)
            status.refresh()
            elapsed = time.time() - start_time

        return status

    def get_manifest(self, **filter_kwargs):
        """Implement the ``Get Object Manifests`` endpoint (section 5.6)."""
        self._verify_can_read()
        query_params = _filter_kwargs_to_query_params(filter_kwargs)
        return self._conn.get(self.url + 'manifest/', accept=MEDIA_TYPE_TAXII_V20,
                              params=query_params)


class ApiRoot(_TAXIIEndpoint):
    """Information about a TAXII API Root.

    This class corresponds to the ``Get API Root Information`` (section 4.2) and
    ``Get Collections`` (section 5.1) endpoints, and contains the information
    found in the corresponding ``API Root Resource`` (section 4.2.1) and
    ``Collections Resource`` (section 5.1.1).

    As obtained from a Server, each ApiRoot instance gets its own connection
    pool(s).  Collections returned by instances of this class share the same
    pools as the instance, so closing one closes all.  Also, the same
    username/password is used to connect to them, as was used for this ApiRoot.
    If either of these is undesirable, Collection instances may be created
    manually.
    """

    def __init__(self, url, user=None, password=None, conn=None):

        super(ApiRoot, self).__init__(url, user, password, conn)

        self._loaded_collections = False
        self._loaded_information = False

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

    def _ensure_loaded_information(self):
        if not self._loaded_information:
            self.refresh_information()

    def refresh(self):
        """Update the API Root's information and list of Collections"""
        self.refresh_information()
        self.refresh_collections()

    def refresh_information(self):
        """Update the properties of this API Root.

        This invokes the ``Get API Root Information`` endpoint.
        """
        response = self._conn.get(self.url, accept=MEDIA_TYPE_TAXII_V20)

        self._title = response['title']
        self._description = response['description']
        self._versions = response['versions']
        self._max_content_length = response['max_content_length']

        self._loaded_information = True

    def refresh_collections(self):
        """Update the list of Collections contained by this API Root.

        This invokes the ``Get Collections`` endpoint.
        """
        url = self.url + 'collections/'
        response = self._conn.get(url, accept=MEDIA_TYPE_TAXII_V20)

        self._collections = []
        for item in response['collections']:
            collection_url = url + item['id'] + "/"
            collection = Collection(collection_url, conn=self._conn, **item)
            self._collections.append(collection)

        self._loaded_collections = True

    def get_status(self, status_id):
        status_url = self.url + "status/" + status_id + "/"
        info = self._conn.get(status_url, accept=MEDIA_TYPE_TAXII_V20)
        return Status(status_url, conn=self._conn, **info)


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

    def __init__(self, url, user=None, password=None, conn=None):
        """
        :param url: URL of a TAXII server discovery endpoint
        :param user: username for authentication (optional)
        :param password: password for authentication (optional)
        :param conn: A connection object, as an alternative to providing
            username/password
        """

        super(Server, self).__init__(url, user, password, conn)

        self._user = user
        self._password = password
        self._loaded = False

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

    def _ensure_loaded(self):
        if not self._loaded:
            self.refresh()

    def refresh(self):
        response = self._conn.get(self.url, accept=MEDIA_TYPE_TAXII_V20)

        self._title = response['title']
        self._description = response.get('description')
        self._contact = response.get('contact')
        roots = response.get('api_roots', [])
        self._api_roots = [ApiRoot(url, conn=self._conn)
                           for url in roots]
        # If 'default' is one of the existing API Roots, reuse that object
        # rather than creating a duplicate. The TAXII 2.0 spec says that the
        # `default` API Root MUST be an item in `api_roots`.
        root_dict = dict(zip(roots, self._api_roots))
        self._default = root_dict.get(response.get('default'))

        self._loaded = True


class _HTTPConnection(object):
    """This library uses the "requests" library, which presents a convenience
    API which hides many network details like actual connection objects.  So
    this class doesn't represent a traditional "connection" either.  It's a
    sort of approximation: sets of connections (or connection pools) and common
    metadata for a particular server interaction.  You can send requests to
    any hosts via the same instance; hosts/ports are not checked and new
    connection pools pop into existence as needed, but all connections are
    closed when the close() method is called.  So this is intended to be used
    for an independent self-contained interaction.
    """

    def __init__(self, user=None, password=None, verify=True):
        self.session = requests.Session()
        self.session.verify = verify
        if user and password:
            self.session.auth = requests.auth.HTTPBasicAuth(user, password)

    def get(self, url, accept, params=None):
        """Perform an HTTP GET, using the saved requests.Session and auth info.

        Args:
            url (str): URL to retrieve
            accept (str): media type to include in the ``Accept:`` header. This
                function checks that the ``Content-Type:`` header on the HTTP
                response matches this media type.
        """
        headers = {
            'Accept': accept
        }
        resp = self.session.get(url, headers=headers, params=params)

        resp.raise_for_status()

        content_type = resp.headers['Content-Type']
        if not content_type.startswith(accept):
            msg = "Unexpected Response Content-Type: {}"
            raise TAXIIServiceException(msg.format(content_type))

        return resp.json()

    def post(self, url, headers=None, params=None, data=None):
        """Send a JSON POST request with the given request headers, additional
        URL query parameters, and the given JSON in the request body.  The
        extra query parameters are merged with any which already exist in the
        URL.
        """
        resp = self.session.post(url, headers=headers, params=params, data=data)
        resp.raise_for_status()
        return resp.json()

    def close(self):
        """Closes connections.  This object is no longer usable."""
        self.session.close()


def get_collection_by_id(api_root, coll_id):
    for collection in api_root.collections:
        if collection.id == coll_id:
            return collection

    return None


def canonicalize_url(api_root_url):
    api_root_url = urlparse.urlsplit(api_root_url).geturl()
    if not api_root_url.endswith("/"):
        api_root_url += "/"
    return api_root_url
