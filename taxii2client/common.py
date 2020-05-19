import datetime
import re

import pytz
import requests
import requests.auth
import requests.structures
import six

from . import DEFAULT_USER_AGENT, MEDIA_TYPE_TAXII_V20, MEDIA_TYPE_TAXII_V21
from .exceptions import (
    InvalidArgumentsError, InvalidJSONError, TAXIIServiceException
)


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
    if precision == "second":
        pass  # Already precise to the second
    elif precision == "millisecond":
        ts = ts + "." + ms[:3]
    elif zoned.microsecond > 0:
        ts = ts + "." + ms.rstrip("0")
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

    Args:
        filter_kwargs: The filter information, as a mapping.

    Returns:
        query_params (dict): The query parameter map, mapping strings to
            strings.

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
                raise InvalidArgumentsError("No more than one value for filter"
                                            " 'added_after' may be given")

            query_params["added_after"] = ",".join(
                _ensure_datetime_to_string(val) for val in arglist
            )

        elif kwarg == "limit":
            query_params["limit"] = int(arglist[0])

        elif kwarg == "next":
            query_params["next"] = arglist

        else:
            query_params["match[" + kwarg + "]"] = ",".join(arglist)

    return query_params


def _to_json(resp):
    """
    Factors out some JSON parse code with error handling, to hopefully improve
    error messages.

    :param resp: A "requests" library response
    :return: Parsed JSON.
    :raises: InvalidJSONError If JSON parsing failed.
    """
    try:
        return resp.json()
    except ValueError as e:
        # Maybe better to report the original request URL?
        six.raise_from(InvalidJSONError(
            "Invalid JSON was received from " + resp.request.url
        ), e)


def _grab_total_items(resp):
    """Extracts the Total elements available on the Endpoint making the request"""
    try:
        results = re.match(r"^items (\d+)-(\d+)/(\d+)$", resp.headers["Content-Range"])
        return int(results.group(2)) - int(results.group(1)) + 1, int(results.group(3))
    except ValueError as e:
        six.raise_from(InvalidJSONError(
            "Invalid Content-Range was received from " + resp.request.url
        ), e)


class TokenAuth(requests.auth.AuthBase):
    def __init__(self, key):
        self.key = key

    def __call__(self, r):
        r.headers['Authorization'] = 'Token {}'.format(self.key)
        return r


class _TAXIIEndpoint(object):
    """Contains some data and functionality common to all TAXII endpoint
    classes: a URL, connection, and ability to close the connection.  It also
    yields support in subclasses for use as context managers, to ensure
    resources are released.

    """
    def __init__(self, url, conn=None, user=None, password=None, verify=True,
                 proxies=None, version="2.0", auth=None):
        """Create a TAXII endpoint.

        Args:
            user (str): username for authentication (optional)
            password (str): password for authentication (optional)
            verify (bool): validate the entity credentials (default: True)
            conn (_HTTPConnection): A connection to reuse (optional)
            proxies (dict): key/value pair for http/https proxy settings.
                (optional)
            version (str): The spec version this connection is meant to follow.

        """
        if (conn and ((user or password) or auth)) or ((user or password) and auth):
            raise InvalidArgumentsError("Only one of a connection, username/password, or auth object may"
                                        " be provided.")
        elif conn:
            self._conn = conn
        else:
            self._conn = _HTTPConnection(user, password, verify, proxies, version=version, auth=auth)

        # Add trailing slash to TAXII endpoint if missing
        # https://github.com/oasis-open/cti-taxii-client/issues/50
        if url[-1] == "/":
            self.url = url
        else:
            self.url = url + "/"

    def close(self):
        self._conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False


class _HTTPConnection(object):
    """This library uses the ``requests`` library, which presents a convenience
    API which hides many network details like actual connection objects.  So
    this class doesn't represent a traditional ``connection`` either.  It's a
    sort of approximation: sets of connections (or connection pools) and common
    metadata for a particular server interaction.  You can send requests to
    any hosts via the same instance; hosts/ports are not checked and new
    connection pools pop into existence as needed, but all connections are
    closed when the close() method is called.  So this is intended to be used
    for an independent self-contained interaction.

    Attributes:
        session (requests.Session): A requests session object.

    """

    def __init__(self, user=None, password=None, verify=True, proxies=None,
                 user_agent=DEFAULT_USER_AGENT, version="2.0", auth=None):
        """Create a connection session.

        Args:
            user (str): username for authentication (optional)
            password (str): password for authentication (optional)
            verify (bool): validate the entity credentials. (default: True)
            proxies (dict): key/value pair for http/https proxy settings.
                (optional)
            user_agent (str): A value to use for the User-Agent header in
                requests.  If not given, use a default value which represents
                this library.
            version (str): The spec version this connection is meant to follow.
        """
        self.session = requests.Session()
        self.session.verify = verify
        # enforce that we always have a connection-default user agent.
        self.user_agent = user_agent or DEFAULT_USER_AGENT

        if user and password:
            self.session.auth = requests.auth.HTTPBasicAuth(user, password)
        elif auth:
            self.session.auth = auth

        if proxies:
            self.session.proxies.update(proxies)
        self.version = version

    def valid_content_type(self, content_type, accept):
        """Check that the server is returning a valid Content-Type

        Args:
            content_type (str): ``Content-Type:`` header value
            accept (str): media type to include in the ``Accept:`` header.

        """
        accept_tokens = accept.replace(' ', '').split(';')
        content_type_tokens = content_type.replace(' ', '').split(';')

        if self.version == "2.0":
            return (
                    all(elem in content_type_tokens for elem in accept_tokens) and
                    (content_type_tokens[0] == 'application/vnd.oasis.taxii+json' or
                     content_type_tokens[0] == 'application/vnd.oasis.stix+json')
            )
        else:
            return (
                    all(elem in content_type_tokens for elem in accept_tokens) and
                    content_type_tokens[0] == 'application/taxii+json'
            )

    def get(self, url, headers=None, params=None):
        """Perform an HTTP GET, using the saved requests.Session and auth info.
        If "Accept" isn't one of the given headers, a default TAXII mime type is
        used.  Regardless, the response type is checked against the accept
        header value, and an exception is raised if they don't match.

        Args:
            url (str): URL to retrieve
            headers (dict): Any other headers to be added to the request.
            params: dictionary or bytes to be sent in the query string for the
                request. (optional)

        """

        merged_headers = self._merge_headers(headers)

        if self.version == "2.0":
            media_type = MEDIA_TYPE_TAXII_V20
        else:
            media_type = MEDIA_TYPE_TAXII_V21

        if "Accept" not in merged_headers:
            merged_headers["Accept"] = media_type
        accept = merged_headers["Accept"]

        resp = self.session.get(url, headers=merged_headers, params=params)

        resp.raise_for_status()

        content_type = resp.headers["Content-Type"]

        if not self.valid_content_type(content_type=content_type, accept=accept):
            msg = "Unexpected Response. Got Content-Type: '{}' for Accept: '{}'"
            raise TAXIIServiceException(msg.format(content_type, accept))

        if "Range" in merged_headers and self.version == "2.0":
            return resp
        else:
            return _to_json(resp)

    def post(self, url, headers=None, params=None, **kwargs):
        """Send a JSON POST request with the given request headers, additional
        URL query parameters, and the given JSON in the request body.  The
        extra query parameters are merged with any which already exist in the
        URL.  The 'json' and 'data' parameters may not both be given.

        Args:
            url (str): URL to retrieve
            headers (dict): Any other headers to be added to the request.
            params: dictionary or bytes to be sent in the query string for the
                request. (optional)
            json: json to send in the body of the Request.  This must be a
                JSON-serializable object. (optional)
            data: raw request body data.  May be a dictionary, list of tuples,
                bytes, or file-like object to send in the body of the Request.
                (optional)
        """

        if len(kwargs) > 1:
            raise InvalidArgumentsError("Too many extra args ({} > 1)".format(
                len(kwargs)))

        if kwargs:
            kwarg = next(iter(kwargs))
            if kwarg not in ("json", "data"):
                raise InvalidArgumentsError("Invalid kwarg: " + kwarg)

        resp = self.session.post(url, headers=headers, params=params, **kwargs)
        resp.raise_for_status()
        return _to_json(resp)

    def delete(self, url, headers=None, params=None, **kwargs):
        """Perform HTTP DELETE"""
        # TODO: May need more work...
        resp = self.session.delete(url, headers=headers, params=params, **kwargs)
        resp.raise_for_status()

    def close(self):
        """Closes connections.  This object is no longer usable."""
        self.session.close()

    def _merge_headers(self, call_specific_headers):
        """
        Merge headers from different sources together.  Headers passed to the
        post/get methods have highest priority, then headers associated with
        the connection object itself have next priority.

        :param call_specific_headers: A header dict from the get/post call, or
            None (the default for those methods).
        :return: A key-case-insensitive MutableMapping object which contains
            the merged headers.  (This doesn't actually return a dict.)
        """

        # A case-insensitive mapping is necessary here so that there is
        # predictable behavior.  If a plain dict were used, you'd get keys in
        # the merged dict which differ only in case.  The requests library
        # would merge them internally, and it would be unpredictable which key
        # is chosen for the final set of headers.  Another possible approach
        # would be to upper/lower-case everything, but this seemed easier.  On
        # the other hand, I don't know if CaseInsensitiveDict is public API...?

        # First establish defaults
        merged_headers = requests.structures.CaseInsensitiveDict({
            "User-Agent": self.user_agent
        })

        # Then overlay with specifics from post/get methods
        if call_specific_headers:
            merged_headers.update(call_specific_headers)

        # Special "User-Agent" header check, to ensure one is always sent.
        # The call-specific overlay could have null'd out that header.
        if not merged_headers.get("User-Agent"):
            merged_headers["User-Agent"] = self.user_agent

        return merged_headers
