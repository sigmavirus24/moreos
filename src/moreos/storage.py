"""Storage mechanism for a cookie jar."""
import typing

import attr


S = typing.TypeVar("S", bound="Storage")


@attr.s
class Storage:
    """Abstraction for a backend for moreos cookie jar storage."""

    backend = attr.ib()  # TODO

    def purge_expired_cookies(self: S):
        """Remove expired cookies from storage backend."""
        pass
