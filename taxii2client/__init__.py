"""Python TAXII 2.1 APIs"""
from .version import __version__

DEFAULT_USER_AGENT = "taxii2-client/" + __version__
MEDIA_TYPE_STIX_V20 = "application/vnd.oasis.stix+json; version=2.0"
MEDIA_TYPE_TAXII_V20 = "application/vnd.oasis.taxii+json; version=2.0"
MEDIA_TYPE_TAXII_V21 = "application/taxii+json; version=2.1"
