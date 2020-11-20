"""Storage mechanism for a cookie jar."""
import abc
import collections
import datetime
import typing

import attr

if typing.TYPE_CHECKING:
    import moreos.cookie


S = typing.TypeVar("S", bound="Storage")
B = typing.TypeVar("B", bound="Backend", covariant=True)
IM = typing.TypeVar("IM", bound="InMemory")


class Backend(metaclass=abc.ABCMeta):
    """Definition of the interface expected for a storage backend."""

    @abc.abstractmethod
    def save(
        self: B, cookies: typing.Sequence["moreos.cookie.Cookie"]
    ) -> None:
        """Save the cookies to the backend."""
        pass

    @abc.abstractmethod
    def list(
        self: B, domain: typing.Optional[str] = None
    ) -> typing.Sequence["moreos.cookie.Cookie"]:
        """List all stored cookies.

        :param domain:
            Allows users to filter to a specific domain.
        """
        pass

    @abc.abstractmethod
    def remove(self: B, cookie: "moreos.cookie.Cookie") -> None:
        """Remove a cookie from the backend."""
        pass

    @abc.abstractmethod
    def drop_for(self: B, domain: str) -> None:
        """Remove all cookies for a domain."""
        pass


class InMemory(Backend):
    """In memory storage for cookies."""

    def __init__(self) -> None:
        self._cookies = collections.defaultdict(
            set
        )  # type: typing.MutableMapping[str, typing.Set[moreos.cookie.Cookie]]

    @staticmethod
    def _key_for(cookie: "moreos.cookie.Cookie") -> str:
        # TODO: Is this the best way to do this? Should we have nested
        # mappings? Include the path?
        return InMemory._key(cookie.domain or "", cookie.name)

    @staticmethod
    def _key(domain: str, name: str) -> str:
        return f"{domain}::{name}"

    def list(
        self: IM, domain: typing.Optional[str] = None
    ) -> typing.Sequence["moreos.cookie.Cookie"]:
        """List all stored cookies.

        :param domain:
            Allows users to filter to a specific domain.
        """
        if domain is not None:
            pattern = self._key(domain, "")
            return [
                v
                for k, vs in self._cookies.items()
                if k.startswith(pattern)
                for v in vs
            ]
        return [v for vs in self._cookies.values() for v in vs]

    def save(
        self: IM, cookies: typing.Sequence["moreos.cookie.Cookie"]
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


@attr.s
class Storage:
    """Abstraction for a backend for moreos cookie jar storage."""

    backend: Backend = attr.ib()

    def purge_expired_cookies(self: S) -> None:
        """Remove expired cookies from storage backend."""
        now = datetime.datetime.now(tz=datetime.timezone.utc)
        for cookie in self.backend.list():
            if cookie.expired(now):
                self.backend.remove(cookie)
