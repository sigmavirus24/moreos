"""Storage mechanism for a cookie jar."""
import collections
import datetime
import typing

import attr
import zope.interface

if typing.TYPE_CHECKING:
    import moreos.cookie


S = typing.TypeVar("S", bound="Storage")
IM = typing.TypeVar("IM", bound="InMemory")


class IBackend(zope.interface.Interface):
    """Definition of the interface expected for a storage backend."""

    def save(
        cookies: typing.Sequence["moreos.cookie.Cookie"],  # noqa: N805
    ) -> None:
        """Save the cookies to the backend."""

    def list(
        domain: typing.Optional[str] = None,  # noqa: N805
        name: typing.Optional[str] = None,
        path: typing.Optional[str] = None,
    ) -> typing.Sequence["moreos.cookie.Cookie"]:
        """List all stored cookies.

        :param str domain:
            Allows users to filter to a specific domain.
        :param str name:
            The name of the cookie to filter for.
        :param str path:
            The path associated with the cookie that's been stored.
        """

    def remove(cookie: "moreos.cookie.Cookie") -> None:  # noqa: N805
        """Remove a cookie from the backend."""

    def drop_for(domain: str) -> None:  # noqa: N805
        """Remove all cookies for a domain."""


@zope.interface.implementer(IBackend)
@attr.s
class InMemory:
    """In memory storage for cookies."""

    _cookies: typing.MutableMapping[
        str, typing.Set["moreos.cookie.Cookie"]
    ] = attr.ib(factory=lambda: collections.defaultdict(set))

    @staticmethod
    def _key_for(cookie: "moreos.cookie.Cookie") -> str:
        # TODO: Is this the best way to do this? Should we have nested
        # mappings? Include the path?
        return InMemory._key(cookie.domain or "", cookie.name)

    @staticmethod
    def _key(domain: str, name: str) -> str:
        return f"{domain}::{name}"

    def list(
        self: IM,
        domain: typing.Optional[str] = None,
        name: typing.Optional[str] = None,
        path: typing.Optional[str] = None,
    ) -> typing.Sequence["moreos.cookie.Cookie"]:
        """List all stored cookies.

        :param str domain:
            Allows users to filter to a specific domain.
        :param str name:
            The name of the cookie to filter for.
        :param str path:
            The path associated with the cookie that's been stored.
        """
        if name is None:
            name = ""
        if domain is not None:
            pattern = self._key(domain, name)
            return [
                v
                for k, vs in self._cookies.items()
                if k.startswith(pattern)
                for v in vs
                if v.path == path
            ]
        return [v for vs in self._cookies.values() for v in vs]

    def save(
        self: IM, cookies: typing.Iterable["moreos.cookie.Cookie"]
    ) -> None:
        """Persist cookies to the in memory backend."""
        for cookie in cookies:
            key = self._key_for(cookie)
            self._cookies[key].add(cookie)

    def remove(self: IM, cookie: "moreos.cookie.Cookie") -> None:
        """Remove a cookie from the in memory backend."""
        key = self._key_for(cookie)
        self._cookies[key].discard(cookie)

    def drop_for(self: IM, domain: str) -> None:
        """Remove all cookies for a domain."""
        pattern = self._key(domain, "")
        for k in list(self._cookies.keys()):
            if k.startswith(pattern):
                del self._cookies[k]
                break


@attr.s(frozen=True)
class Storage:
    """Abstraction for a backend for moreos cookie jar storage."""

    backend: IBackend = attr.ib(validator=attr.validators.provides(IBackend))

    def purge_expired_cookies(self: S) -> None:
        """Remove expired cookies from storage backend."""
        now = datetime.datetime.now(tz=datetime.timezone.utc)
        for cookie in self.backend.list():
            if cookie.expired(now):
                self.backend.remove(cookie)

    def find(
        self: S,
        domain: str,
        name: typing.Optional[str] = None,
        path: typing.Optional[str] = None,
    ) -> typing.Iterable["moreos.cookie.Cookie"]:
        """List cookies stored for a given domain.

        :param str domain:
            Allows users to filter to a specific domain.
        :param str name:
            The name of the cookie to filter for.
        :param str path:
            The path associated with the cookie that's been stored.
        :returns:
            An iterable that contains Cookie instances.
        """
        return self.backend.list(domain=domain, name=name, path=path)
