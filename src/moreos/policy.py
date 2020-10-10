"""Policies for managing cookie jars."""
import enum
import ipaddress
import typing

import attr


class DomainMatching(enum.IntFlag):
    """Define the algorithms used for domain matching within a domain policy.

    * ``strict_equality``, as its name ideally implies, will check only for
      equality of the domains (after they've been noramlized to all lower case)
    """

    #: Strict equality matching will ensure that
    strict_equality = 1
    reject_ipaddress = 2


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


P = typing.TypeVar("P", bound="Policy")


@attr.s(frozen=True)
class Policy:
    """Logic that determines the behaviour of a cookie jar.

    This determines if a cookie sent by a server is stored and if a cookie
    that's been stored is sent to a server during a request.
    """

    # TODO make this real
    domain: DomainPolicy = attr.ib()

    @classmethod
    def default(cls: typing.Type[P]) -> P:
        """Return the default policy."""
        return cls(domain=DomainPolicy())
