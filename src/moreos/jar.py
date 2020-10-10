"""Cookie jar logic for the moreos package."""
import typing
import urllib.parse

import attr

import moreos.policy

if typing.TYPE_CHECKING:
    import moreos.cookie
    import moreos.storage

R = typing.TypeVar("R")


class ClientAdapterInterface(typing.Generic[R]):
    """The interface expected by moreos to retrieve information from any client.

    The necessary methods to implement are:

    * ``request_uri``
    *
    """

    @staticmethod
    def uri(request: R) -> str:
        """Retrieve the URI of the request being made."""
        raise NotImplementedError(
            "request_uri needs to be implemented for a ClientAdapter"
        )

    #: Alias uri for use with RFC 2965 language
    absolute_uri = uri

    @staticmethod
    def parsed_uri(request: R) -> urllib.parse.ParseResult:
        """Parse the Request's absolute URI for later use."""
        return urllib.parse.urlparse(ClientAdapterInterface.uri(request))

    @staticmethod
    def hostname(request: R) -> typing.Optional[str]:
        """Retrieve the hostname from the request_uri."""
        parse_result = ClientAdapterInterface.parsed_uri(request)
        return parse_result.hostname

    #: Alias hostname for use with RFC 2965 language
    request_host = hostname

    @staticmethod
    def effective_hostname(request: R) -> typing.Optional[str]:
        """Calculate the effective hostname for a request.

        Specifically, if a hostname contains no dots (.), the effective
        hostname is the name with ".local" appended, otherwise the effective
        hostname is the same name as the hostname.

        See also: https://tools.ietf.org/html/rfc2965
        """
        hostname = ClientAdapterInterface.hostname(request)
        if hostname is None:
            return None
        if hostname.find(".") >= 0:
            return hostname
        return f"{hostname}.local"

    @staticmethod
    def port(request: R) -> typing.Optional[int]:
        """Retrieve the port portion of the request URL."""
        uri = ClientAdapterInterface.parsed_uri(request)
        return uri.port

    request_port = port

    @staticmethod
    def request_uri(request: R) -> str:
        """Retrieve the path in the Request's URI."""
        parse_result = ClientAdapterInterface.parsed_uri(request)
        return parse_result.path

    abs_path = request_uri


J = typing.TypeVar("J", bound="Jar")


@attr.s
class Jar(typing.Generic[R]):
    """A Cookie jar to store cookies received by clients."""

    storage: "moreos.storage.Storage" = attr.ib()  # TODO
    client_adapter: ClientAdapterInterface = attr.ib()  # TODO
    cookies: typing.Sequence["moreos.cookie.Cookie"] = attr.ib(factory=list)
    policy: moreos.policy.Policy = attr.ib(
        factory=moreos.policy.Policy.default
    )

    def match(
        self: J, request: R, *, purge_first=True
    ) -> typing.Sequence["moreos.cookie.Cookie"]:
        """Find stored cookies to be sent with a request."""
        if purge_first:
            self.storage.purge_expired_cookies()
        return []
