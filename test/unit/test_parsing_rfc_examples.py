"""Verify we can parse the RFC examples."""
import pytest

import moreos.cookie

EXAMPLES = [
    # From https://tools.ietf.org/html/rfc6265#section-3.1
    (
        ("Set-Cookie", "SID=31d4d96e407aad42"),
        [
            moreos.cookie.Cookie(
                "SID",
                "31d4d96e407aad42",
                type=moreos.cookie.CookieType.server,
            )
        ],
    ),
    (
        ("Set-Cookie", "SID=31d4d96e407aad42; Path=/; Domain=example.com"),
        [
            moreos.cookie.Cookie(
                "SID",
                "31d4d96e407aad42",
                path="/",
                domain="example.com",
                type=moreos.cookie.CookieType.server,
            )
        ],
    ),
    (
        ("Set-Cookie", "SID=31d4d96e407aad42; Path=/; Secure; HttpOnly"),
        [
            moreos.cookie.Cookie(
                "SID",
                "31d4d96e407aad42",
                path="/",
                secure=True,
                httponly=True,
                type=moreos.cookie.CookieType.server,
            )
        ],
    ),
    (
        ("Set-Cookie", "lang=en-US; Path=/; Domain=example.com"),
        [
            moreos.cookie.Cookie(
                "lang",
                "en-US",
                path="/",
                domain="example.com",
                type=moreos.cookie.CookieType.server,
            )
        ],
    ),
    (
        ("Cookie", "SID=31d4d96e407aad42; lang=en-US"),
        [
            moreos.cookie.Cookie(
                "SID",
                "31d4d96e407aad42",
                type=moreos.cookie.CookieType.client,
            ),
            moreos.cookie.Cookie(
                "lang", "en-US", type=moreos.cookie.CookieType.client
            ),
        ],
    ),
    (
        ("Set-Cookie", "lang=en-US; Expires=Wed, 09 Jun 2021 10:18:14 GMT"),
        [
            moreos.cookie.Cookie(
                "lang",
                "en-US",
                expires="Wed, 09 Jun 2021 10:18:14 GMT",
                type=moreos.cookie.CookieType.server,
            )
        ],
    ),
    (
        ("Set-Cookie", "lang=; Expires=Sun, 06 Nov 1994 08:49:37 GMT"),
        [
            moreos.cookie.Cookie(
                "lang",
                "",
                expires="Sun, 06 Nov 1994 08:49:37 GMT",
                type=moreos.cookie.CookieType.server,
            )
        ],
    ),
]


@pytest.mark.parametrize("parse_args, expected_cookies", EXAMPLES)
def test_parses_rfc_examples(parse_args, expected_cookies):
    """Ensure there are no errors parsing the examples in RFC 6265."""
    parsed_cookies = moreos.cookie.parse(*parse_args)
    assert len(parsed_cookies) == len(expected_cookies)
    for i, cookie in enumerate(parsed_cookies):
        assert isinstance(cookie, moreos.cookie.Cookie)
        assert expected_cookies[i] == cookie
