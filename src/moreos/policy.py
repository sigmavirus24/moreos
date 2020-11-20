"""Policies for managing cookie jars."""
import enum
import ipaddress
import typing

import attr

from moreos import _common_types as _ct
from moreos import cookie as _cookie


class DomainMatching(enum.IntFlag):
    """Define the algorithms used for domain matching within a domain policy.

    * ``strict_equality``, as its name ideally implies, will check only for
      equality of the domains (after they've been noramlized to all lower case)

    * ``reject_ipaddress`` will refuse to domain-match a request host if that
      host is an IP Address

    * ``reject_wellknown_public_suffixes_as_domain`` refuses to match or
      accept a Domain attribute with a well-known suffix, e,g., com, co.uk,
      etc.
    """

    #: Strict equality matching will ensure that
    strict_equality = 1
    reject_ipaddress = 2
    reject_wellknown_public_suffixes_as_domain = 4
    # next - 8


@attr.s(frozen=True)
class DomainPolicy:
    """Configuration of the domain policy, as input to the Policy object.

    See also: https://tools.ietf.org/html/rfc6265#section-5.1.3
    """

    block_list: typing.Optional[typing.Sequence[str]] = attr.ib(default=None)
    allow_list: typing.Optional[typing.Sequence[str]] = attr.ib(default=None)
    matching: DomainMatching = attr.ib(
        default=DomainMatching.strict_equality
        | DomainMatching.reject_ipaddress
        | DomainMatching.reject_wellknown_public_suffixes_as_domain
    )

    def match(
        self: "DomainPolicy", request_host: str, cookie_domain: str
    ) -> bool:
        """Check if the request_host and cookie_domain domain match.

        References:
        * https://tools.ietf.org/html/rfc6265#section-5.1.3
        """
        request_host, cookie_domain = (
            request_host.lower(),
            cookie_domain.lower(),
        )

        if request_host == cookie_domain:
            # In this case, they match exactly so that's perfect to return
            return True

        if self.matching & DomainMatching.strict_equality:
            return False

        if (
            self.matching
            & DomainMatching.reject_wellknown_public_suffixes_as_domain
            and cookie_domain in _wellknown_public_suffixes
        ):
            return False

        reject_ipaddress = self.matching & DomainMatching.reject_ipaddress
        if (
            request_host == ""
            or request_host[0] == "."
            or request_host[-1] == "."
            or (_is_ipaddress(request_host) and reject_ipaddress)
        ):
            return False

        index = request_host.index(cookie_domain)
        if index <= 0 or not cookie_domain.startswith("."):
            return False

        if (
            cookie_domain == ""
            or cookie_domain[1:] == ""
            or cookie_domain[1] == "."
            or cookie_domain[-1] == "."
            or (_is_ipaddress(cookie_domain[1:]) and reject_ipaddress)
        ):
            return False

        return True


_wellknown_public_suffixes = frozenset(
    [
        "com",
        "org",
        "edu",
        "co",
        "co.uk",
        "io",
        "net",
        "int",
        "gov",
        "mil",
        "ly",
    ]
)


def _is_ipaddress(domain: str) -> bool:
    # ipaddress doesn't accept IPv6 hostnames like '[::1]' but requires
    # the IPv6 address alone.
    domain = domain.strip("[]")
    try:
        ipaddress.ip_address(domain)
    except ValueError:
        # If it's an invalid IP Addresss or a domain (e.g., example.com)
        # then the `ipaddress` standard library will raise a ValueError
        return False
    return True


P = typing.TypeVar("P", bound="Policy[typing.Any]")


@attr.s(frozen=True)
class Policy(typing.Generic[_ct.HttpRequest]):
    """Logic that determines the behaviour of a cookie jar.

    This determines if a cookie sent by a server is stored and if a cookie
    that's been stored is sent to a server during a request.
    """

    domain: DomainPolicy = attr.ib()

    @classmethod
    def default(cls: typing.Type[P]) -> P:
        """Return the default policy."""
        return cls(domain=DomainPolicy())

    def match(
        self, cookie: "_cookie.Cookie", request: _ct.HttpRequest
    ) -> bool:
        """Determine if a cookie matches the request based on policy."""
        return False
