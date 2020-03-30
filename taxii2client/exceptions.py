"""TAXII2 Error Classes."""


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


class ValidationError(TAXIIServiceException):
    """Data validation failed for a property or group of properties"""
    pass


class InvalidJSONError(TAXIIServiceException):
    """A server endpoint gave us invalid JSON"""
    pass
