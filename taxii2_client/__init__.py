import requests
from requests.auth import HTTPBasicAuth
import os

os.environ["NO_PROXY"] = "localhost"

MEDIA_TYPE_STIX_V20 = "application/vnd.oasis.stix+json; version=2.0"
MEDIA_TYPE_TAXII_V20 = "application/vnd.oasis.taxii+json; version=2.0"


class Status(object):
    def __init__(self, id, status, total_count, success_count, failure_count, pending_count, request_timestamp=None,
                 successes=None, failures=None, pendings=None):
        self.id_ = id
        self.status = status
        self.total_count = total_count
        self.success_count = success_count
        self.failure_count = failure_count
        self.pending_count = pending_count


class Collection(object):
    def __init__(self, api_root, id, media_types, title=None, can_write=True, can_read=True, description=None):
        self.id_ = id
        self.api_root = api_root
        self.taxii_client = api_root.taxii_client
        self.media_types = media_types
        self.title = title
        self.can_write = can_write
        self.can_read = can_read
        self.description = description

    def get_object(self, obj_id):
        if not self.can_read:
            raise ValueError("Collection %s of %s does not allow reading" % (self.id_, self.api_root.uri))
        return self.taxii_client.send_request("get",
                                              "/".join([self.api_root.uri, "collections", self.id_, "objects", obj_id]),
                                              {"Accept": MEDIA_TYPE_STIX_V20})

    def get_objects(self, filters=None):
        if not self.can_read:
            raise ValueError("Collection %s of %s does not allow reading" % (self.id_, self.api_root.uri))
        return self.taxii_client.send_request("get",
                                              "/".join([self.api_root.uri, "collections", self.id_, "objects"]),
                                              {"Accept": MEDIA_TYPE_STIX_V20},
                                              params=filters)


    def add_objects(self, bundle):
        if not self.can_write:
            raise ValueError("Collection %s of %s does not allow writing" % (self.id_, self.api_root.uri))
        info = self.taxii_client.send_request("post",
                                              "/".join([self.api_root.uri, "collections", self.id_, "objects"])+"/",
                                              {"Accept": MEDIA_TYPE_TAXII_V20,
                                               "Content-Type": MEDIA_TYPE_STIX_V20},
                                              json=bundle)
        return Status(**info)

    def get_manifest(self, filters=None):
        return self.taxii_client.send_request("get",
                                              "/".join([self.api_root.uri, "collections", self.id_, "manifest"]),
                                              {"Accept": MEDIA_TYPE_TAXII_V20})

class ApiRoot(object):

    def __init__(self, uri, taxii_client, name, collections=None, status=None, information=None):
        self.uri = uri
        self.taxii_client = taxii_client
        self.name = name
        self.collections = self.get_collections(True)
        self.information = self.get_information(True)

    def get_collections(self, refresh=False):
        if refresh or not self.collections:
            info = self.taxii_client.send_request("get",
                                                  self.uri + "/" + "collections",
                                                  {"Accept": MEDIA_TYPE_TAXII_V20})
            self.collections = []
            for collection in info["collections"]:
                c = Collection(self, **collection)
                self.collections.append(c)
        return self.collections

    def get_information(self, refresh=False):
        if refresh or not self.information:
            self.information = self.taxii_client.send_request("get",
                                                              self.uri,
                                                              {"Accept": MEDIA_TYPE_TAXII_V20})
        return self.information

    def get_collection(self, id_, refresh=False):
        for c in self.get_collections(refresh):
            if c.id_ == id_:
                return c

    def get_status(self, id_):
        info = self.taxii_client.send_request("get",
                                              "/".join([self.uri, "status", id_]),
                                              {"Accept": MEDIA_TYPE_TAXII_V20})
        return Status(**info)


class TAXII2Client(object):

    def __init__(self, server_uri, user, password):
        self.server_uri = server_uri
        self.api_roots = []
        self.server_title = None
        self.server_description = None
        self.server_contact = None
        self.default_api_root = None
        self.auth_info = HTTPBasicAuth(user, password)

    def populate_available_information(self):
        info = self.send_request("get",
                                 self.server_uri + "/" + "taxii",
                                 {"Accept": MEDIA_TYPE_TAXII_V20})
        for api_root in info["api_roots"]:
            ar = ApiRoot(self.canonicalize_api_root_uri(api_root), self, self.get_api_root_name(api_root))
            self.api_roots.append(ar)
        self.server_title = info["title"]
        self.server_description = info["description"]
        if info["default"]:
            self.default_api_root = self.get_api_root(info["default"])

    def refresh_available_information(self):
        pass

    def get_api_root(self, name):
        for a_r in self.api_roots:
            if a_r.name == name:
                return a_r

    def send_request(self, request_type, url, headers, json=None, params=None):
        # could be fancier to make the call, but not sure its worth it
        if request_type == "get":
            resp = requests.get(url, headers=headers, params=params, auth=self.auth_info)
        elif request_type == "post":
            resp = requests.post(url, headers=headers, params=params, json=json, auth=self.auth_info)
        else:
            raise ValueError("request type %s not supported" % request_type)
        resp.raise_for_status()
        return resp.json()

    #def get_collections(self, api_root, refresh=False):
    #    return api_root.get_collection(refresh)

    @staticmethod
    def canonicalize_api_root_uri(api_root_uri):
        if api_root_uri.endswith("/"):
            api_root_uri = api_root_uri[:-1]
        return api_root_uri


    @staticmethod
    def get_api_root_name(api_root_uri):
        if api_root_uri.endswith("/"):
            api_root_uri = api_root_uri[:-1]
        return api_root_uri.split('/')[-1]




