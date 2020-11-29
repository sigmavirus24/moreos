"""Declare the interface we expect other adapters to have."""
import zope.interface

from moreos import _common_types as _ct


class IRequest(zope.interface.Interface):
    """Interface for interacting with an HTTP Client's Request."""

    def uri(request: _ct.HttpRequest) -> str:  # noqa: N805
        """Retrieve the URI for the request.

        :returns:
            The request URI for this HTTP client
        :rtype:
            str
        """
        pass
