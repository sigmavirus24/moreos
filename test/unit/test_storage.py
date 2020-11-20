"""Verify our InMemory and Storage classes."""

from moreos import cookie
from moreos import storage


def test_empty_inmemory_backend():
    """Verify some initial behaviours."""
    im = storage.InMemory()
    assert im.list() == []
    im.remove(
        cookie.Cookie(
            "SID", "31d4d96e407aad42", type=cookie.CookieType.server
        )
    )
    assert im.list() == []
