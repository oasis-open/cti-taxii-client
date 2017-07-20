import pytest
import responses
import requests

from taxii2_client import (Collection, ApiRoot, ServerInfo, TAXII2Client,
                           MEDIA_TYPE_STIX_V20, MEDIA_TYPE_TAXII_V20)

TAXII_SERVER = 'example.com'
DISCOVERY_URL = 'https://{}/taxii/'.format(TAXII_SERVER)
API_ROOT_URL = 'https://{}/api1/'.format(TAXII_SERVER)
COLLECTIONS_URL = API_ROOT_URL + 'collections/'
COLLECTION_URL = COLLECTIONS_URL + '91a7b528-80eb-42ed-a74d-c6fbd5a26116/'


DISCOVERY_RESPONSE = """{
  "title": "Some TAXII Server",
  "description": "This TAXII Server contains a listing of...",
  "contact": "string containing contact information",
  "default": "https://example.com/api2/",
  "api_roots": [
    "https://example.com/api1/",
    "https://example.com/api2/",
    "https://example.net/trustgroup1/"
  ]
}"""
API_ROOT_RESPONSE = """{
  "title": "Malware Research Group",
  "description": "A trust group setup for malware researchers",
  "versions": ["taxii-2.0"],
  "max_content_length": 9765625
}"""
COLLECTIONS_RESPONSE = """{
  "collections": [
    {
      "id": "91a7b528-80eb-42ed-a74d-c6fbd5a26116",
      "title": "High Value Indicator Collection",
      "description": "This data collection is for collecting high value IOCs",
      "can_read": true,
      "can_write": false,
      "media_types": [
        "application/vnd.oasis.stix+json; version=2.0"
      ]
    },
    {
      "id": "52892447-4d7e-4f70-b94d-d7f22742ff63",
      "title": "Indicators from the past 24-hours",
      "description": "This data collection is for collecting current IOCs",
      "can_read": true,
      "can_write": false,
      "media_types": [
        "application/vnd.oasis.stix+json; version=2.0"
      ]
    }
  ]
}"""
COLLECTION_RESPONSE = """{
  "id": "91a7b528-80eb-42ed-a74d-c6fbd5a26116",
  "title": "High Value Indicator Collection",
  "description": "This data collection is for collecting high value IOCs",
  "can_read": true,
  "can_write": false,
  "media_types": [
    "application/vnd.oasis.stix+json; version=2.0"
  ]
}"""


@pytest.fixture
def client():
    return TAXII2Client(None, None)


@responses.activate
def test_server(client):
    responses.add(responses.GET, DISCOVERY_URL, body=DISCOVERY_RESPONSE,
                  status=200, content_type=MEDIA_TYPE_TAXII_V20)
    server = ServerInfo('example.com', client=client)

    assert server._loaded is False
    assert server.title == "Some TAXII Server"
    assert server._loaded is True
    assert server.description == "This TAXII Server contains a listing of..."
    assert server.contact == "string containing contact information"
    assert len(server.api_roots) == 3
    assert server.default is not None

    assert server.api_roots[1] == server.default

    api_root = server.api_roots[0]
    assert api_root.url == API_ROOT_URL
    # The URL is populated based on the discovery response, so the rest of the
    # information is not loaded yet.
    assert api_root._loaded_information is False


@responses.activate
def test_minimal_server_response(client):
    # `title` is the only required field on a Discove
    response = '{"title": "Some TAXII Server"}'
    responses.add(responses.GET, DISCOVERY_URL, body=response,
                  status=200, content_type=MEDIA_TYPE_TAXII_V20)
    server = ServerInfo('example.com', client=client)

    assert server.title == "Some TAXII Server"
    assert server.description is None
    assert server.contact is None
    assert server.api_roots == []
    assert server.default is None


@responses.activate
def test_server_with_no_default(client):
    response = """{
      "title": "Some TAXII Server",
      "description": "This TAXII Server contains a listing of...",
      "contact": "string containing contact information",
      "api_roots": [
        "https://example.com/api1/",
        "https://example.com/api2/",
        "https://example.net/trustgroup1/"
      ]
    }"""
    responses.add(responses.GET, DISCOVERY_URL, body=response,
                  status=200, content_type=MEDIA_TYPE_TAXII_V20)
    server = ServerInfo('example.com', client=client)

    assert len(server.api_roots) == 3
    assert server.default is None


@responses.activate
def test_api_root(client):
    responses.add(responses.GET, API_ROOT_URL, API_ROOT_RESPONSE,
                  status=200, content_type=MEDIA_TYPE_TAXII_V20)

    api_root = ApiRoot(API_ROOT_URL, client=client)

    assert api_root._loaded_information is False
    assert api_root.title == "Malware Research Group"
    assert api_root._loaded_information is True
    assert api_root.description == "A trust group setup for malware researchers"
    assert api_root.versions == ['taxii-2.0']
    assert api_root.max_content_length == 9765625


@responses.activate
def test_api_root_collections(client):
    responses.add(responses.GET, COLLECTIONS_URL, COLLECTIONS_RESPONSE, status=200,
                  content_type=MEDIA_TYPE_TAXII_V20)

    api_root = ApiRoot(API_ROOT_URL, client=client)

    assert api_root._loaded_collections is False
    assert len(api_root.collections) == 2
    assert api_root._loaded_collections is True

    coll = api_root.collections[0]
    # A collection populated from an API Root is automatically loaded
    assert coll._loaded is True
    assert coll.id == '91a7b528-80eb-42ed-a74d-c6fbd5a26116'
    assert coll.url == COLLECTION_URL
    assert coll.title == "High Value Indicator Collection"
    assert coll.description == "This data collection is for collecting high value IOCs"
    assert coll.can_read is True
    assert coll.can_write is False
    assert coll.media_types == [MEDIA_TYPE_STIX_V20]


@responses.activate
def test_collection(client):
    responses.add(responses.GET, COLLECTION_URL, COLLECTION_RESPONSE,
                  status=200, content_type=MEDIA_TYPE_TAXII_V20)

    coll = Collection(COLLECTION_URL, client=client)

    assert coll._loaded is False
    assert coll.id == '91a7b528-80eb-42ed-a74d-c6fbd5a26116'
    assert coll._loaded is True
    assert coll.url == COLLECTION_URL
    assert coll.title == "High Value Indicator Collection"
    assert coll.description == "This data collection is for collecting high value IOCs"
    assert coll.can_read is True
    assert coll.can_write is False
    assert coll.media_types == [MEDIA_TYPE_STIX_V20]


def test_collection_unexpected_kwarg():
    with pytest.raises(TypeError):
        coll = Collection(url="", client=None, foo="bar")
