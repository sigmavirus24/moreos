"""Cookie jar logic for the moreos package."""
import abc
import typing
import urllib.parse

import attr

from moreos import _common_types as _ct
import moreos.policy
import moreos.storage

if typing.TYPE_CHECKING:
    import moreos.cookie
    import requests


CAI = typing.TypeVar(
    "CAI", bound="ClientAdapterInterface[typing.Any]", covariant=True
)


class ClientAdapterInterface(
    typing.Generic[_ct.HttpRequest], metaclass=abc.ABCMeta
):
    """The interface expected by moreos to retrieve information from any client.

    The necessary methods to implement are:

    * ``uri``
    """

    @classmethod
    @abc.abstractmethod
    def uri(cls: typing.Type[CAI], request: _ct.HttpRequest) -> str:
        """Retrieve the URI of the request being made."""
        pass

    @classmethod
    def absolute_uri(cls: typing.Type[CAI], request: _ct.HttpRequest) -> str:
        """Alias uri for use with RFC 2965 language."""
        return cls.uri(request)

    @classmethod
    def parsed_uri(
        cls: typing.Type[CAI], request: _ct.HttpRequest
    ) -> urllib.parse.ParseResult:
        """Parse the Request's absolute URI for later use."""
        return urllib.parse.urlparse(cls.uri(request))

    @classmethod
    def hostname(
        cls: typing.Type[CAI], request: _ct.HttpRequest
    ) -> typing.Optional[str]:
        """Retrieve the hostname from the request_uri."""
        parse_result = cls.parsed_uri(request)
        return parse_result.hostname

    #: Alias hostname for use with RFC 2965 language
    request_host = hostname

    @classmethod
    def effective_hostname(
        cls: typing.Type[CAI], request: _ct.HttpRequest
    ) -> typing.Optional[str]:
        """Calculate the effective hostname for a request.

        Specifically, if a hostname contains no dots (.), the effective
        hostname is the name with ".local" appended, otherwise the effective
        hostname is the same name as the hostname.

        See also: https://tools.ietf.org/html/rfc2965
        """
        hostname = cls.hostname(request)
        if hostname is None:
            return None
        if hostname.find(".") >= 0:
            return hostname
        return f"{hostname}.local"

    @classmethod
    def port(
        cls: typing.Type[CAI], request: _ct.HttpRequest
    ) -> typing.Optional[int]:
        """Retrieve the port portion of the request URL."""
        uri = cls.parsed_uri(request)
        return uri.port

    request_port = port

    @classmethod
    def request_uri(cls: typing.Type[CAI], request: _ct.HttpRequest) -> str:
        """Retrieve the path in the Request's URI."""
        parse_result = cls.parsed_uri(request)
        return parse_result.path

    abs_path = request_uri


class RequestsAdapter(ClientAdapterInterface["requests.PreparedRequest"]):
    """ClientAdapter used with the Requests library."""

    @classmethod
    def uri(
        cls: typing.Type["RequestsAdapter"],
        request: "requests.PreparedRequest",
    ) -> str:
        """Retrieve the URL of a PreparedRequest from Requests."""
        return typing.cast("str", request.url)


J = typing.TypeVar("J", bound="Jar[typing.Any]")


@attr.s
class Jar(typing.Generic[_ct.HttpRequest]):
    """A Cookie jar to store cookies received by clients."""

    #: The backend used to store cookies. Can be configured by the user.
    #: Defaults to using in memory backend for storage
    storage: moreos.storage.Storage = attr.ib(
        factory=lambda: moreos.storage.Storage(moreos.storage.InMemory())
    )
    #: The adapter that retrieves values from the requests for a given HTTP
    #: library
    client_adapter: ClientAdapterInterface[_ct.HttpRequest] = attr.ib()
    #: The configured policy for this cookie jar.
    policy: moreos.policy.Policy[_ct.HttpRequest] = attr.ib(
        factory=moreos.policy.Policy.default
    )

    def cookies_for(
        self: J, request: _ct.HttpRequest, *, purge_first: bool = True
    ) -> typing.Sequence["moreos.cookie.Cookie"]:
        """Find stored cookies to be sent with a request."""
        if purge_first:
            self.storage.purge_expired_cookies()
        return []
