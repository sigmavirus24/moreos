"""Declare the Requests client interface and register it."""
import typing

import zope.interface
import zope.interface.verify

if typing.TYPE_CHECKING:
    import requests

from . import interface


@zope.interface.implementer(interface.IRequest)
class Requests:
    """ClientAdapter used with the Requests library."""

    def uri(
        self: "Requests",
        request: typing.Any,
    ) -> str:
        """Retrieve the URL of a PreparedRequest from Requests."""
        request = typing.cast("requests.PreparedRequest", request)
        return typing.cast("str", request.url)
