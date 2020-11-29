"""Cookie jar logic for the moreos package."""
import typing
import urllib.parse

import attr

from moreos import _common_types as _ct
import moreos.client_adapters.interface
import moreos.policy
import moreos.storage

if typing.TYPE_CHECKING:
    import moreos.cookie


_RI = typing.TypeVar("_RI", bound="_RequestInfo")


@attr.s
class _RequestInfo:
    uri: str = attr.ib()
    parsed_uri: urllib.parse.ParseResult = attr.ib(init=False)

    def __attrs_post_init__(self: _RI) -> None:
        self.parsed_uri = urllib.parse.urlparse(self.uri)

    def absolute_uri(self: _RI) -> str:
        """Alias uri for use with RFC 2965 language."""
        return self.uri

    def hostname(self: _RI) -> typing.Optional[str]:
        """Retrieve the hostname from the request_uri."""
        parse_result = self.parsed_uri
        return parse_result.hostname

    #: Alias hostname for use with RFC 2965 language
    request_host = hostname

    def effective_hostname(self: _RI) -> typing.Optional[str]:
        """Calculate the effective hostname for a request.

        Specifically, if a hostname contains no dots (.), the effective
        hostname is the name with ".local" appended, otherwise the effective
        hostname is the same name as the hostname.

        See also: https://tools.ietf.org/html/rfc2965
        """
        hostname = self.hostname()
        if hostname is None:
            return None
        if hostname.find(".") >= 0:
            return hostname
        return f"{hostname}.local"

    def port(self: _RI) -> typing.Optional[int]:
        """Retrieve the port portion of the request URL."""
        uri = self.parsed_uri
        return uri.port

    request_port = port

    def request_uri(self: _RI) -> str:
        """Retrieve the path in the Request's URI."""
        parse_result = self.parsed_uri
        return parse_result.path

    abs_path = request_uri


J = typing.TypeVar("J", bound="Jar[typing.Any]")


@attr.s(frozen=True)
class Jar(typing.Generic[_ct.HttpRequest]):
    """A Cookie jar to store cookies received by clients."""

    #: The adapter that retrieves values from the requests for a given HTTP
    #: library
    client_adapter: moreos.client_adapters.interface.IRequest = attr.ib(
        validator=attr.validators.provides(
            moreos.client_adapters.interface.IRequest
        )
    )
    #: The backend used to store cookies. Can be configured by the user.
    #: Defaults to using in memory backend for storage
    storage: moreos.storage.Storage = attr.ib(
        factory=lambda: moreos.storage.Storage(moreos.storage.InMemory())
    )
    #: The configured policy for this cookie jar.
    policy: moreos.policy.Policy[_ct.HttpRequest] = attr.ib(
        factory=moreos.policy.Policy.default
    )

    def _info(self: J, request: _ct.HttpRequest) -> _RequestInfo:
        return _RequestInfo(uri=self.client_adapter.uri(request))

    def cookies_for(
        self: J, request: _ct.HttpRequest, *, purge_first: bool = True
    ) -> typing.Iterable["moreos.cookie.Cookie"]:
        """Find stored cookies to be sent with a request."""
        if purge_first:
            self.storage.purge_expired_cookies()
        info = self._info(request)
        hostname = info.effective_hostname()
        if hostname:
            return self.storage.find(domain=hostname)
        return []
