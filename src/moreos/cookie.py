"""The cookie module contains the parsing logic and cookie class."""
import datetime
import enum
import typing

import attr
import dateutil.parser

from moreos import parsing


SSP = typing.TypeVar("SSP", bound="SameSitePolicy")


@enum.unique
class SameSitePolicy(enum.Enum):
    """A way of enumerating the values of the SameSite portion of a cookie."""

    lax = "Lax"
    strict = "Strict"
    none = "None"

    def __str__(self: SSP) -> str:
        """Return the value of the enum instead of a repr."""
        return str(self.value)

    @classmethod
    def from_value(
        cls: typing.Type[SSP],
        policy: typing.Union[typing.Optional[str], "SameSitePolicy"],
    ) -> typing.Optional[SSP]:
        """Convert value to a SameSitePolicy value."""
        if isinstance(policy, cls):
            return policy
        policy = typing.cast(typing.Optional[str], policy)
        return cls.from_string(policy)

    @classmethod
    def from_string(
        cls: typing.Type[SSP], policy: typing.Optional[str]
    ) -> typing.Optional[SSP]:
        """Convert a string from a cookie to the SameSitePolicy value."""
        # NOTE(sigmavirus24): With a default of None, attrs will pass that to
        # the converter
        if policy is None:
            return policy
        policy = typing.cast(str, policy)
        return getattr(cls, policy.lower(), None)


@enum.unique
class CookieType(enum.Enum):
    """Enumeration of kinds of cookie headers."""

    server = "Set-Cookie"
    client = "Cookie"

    def __str__(self: "CookieType") -> str:
        """Return the value of the enum instead of a repr."""
        return str(self.value)

    @classmethod
    def from_value(
        cls: typing.Type["CookieType"],
        cookie_header_type: typing.Union[typing.Optional[str], "CookieType"],
    ) -> typing.Optional["CookieType"]:
        """Convert the cookie header name to its CookieType."""
        if isinstance(cookie_header_type, cls):
            return cookie_header_type
        cookie_header_type = typing.cast(
            typing.Optional[str], cookie_header_type
        )
        return cls.from_string(cookie_header_type)

    @classmethod
    def from_string(
        cls: typing.Type["CookieType"],
        cookie_header_value: typing.Optional[str],
    ) -> typing.Optional["CookieType"]:
        """Convert the cookie header name to its CookieType."""
        if cookie_header_value is not None:
            cookie_header_value = typing.cast(str, cookie_header_value)
            lowered = cookie_header_value.lower()
            if lowered == "set-cookie":
                return cls.server
            if lowered == "cookie":
                return cls.client
        return None


# MyPy's attrs plugin doesn't support classmethods as converters below, so
# let's define a private function to satisfy the type linter... for now
# Issue: https://github.com/python/mypy/issues/6172
def _ssp_from_value(
    value: typing.Union[typing.Optional[str], SameSitePolicy]
) -> typing.Optional[SameSitePolicy]:
    return SameSitePolicy.from_value(value)


def _ct_from_value(
    value: typing.Union[typing.Optional[str], CookieType]
) -> typing.Optional[CookieType]:
    return CookieType.from_value(value)


def _max_age_converter(
    value: typing.Union[None, str, int]
) -> typing.Optional[datetime.timedelta]:
    if value is None:
        return None
    if isinstance(value, str):
        value = int(value, 10)
    return datetime.timedelta(seconds=value)


def _expires_converter(
    value: typing.Union[None, str, datetime.datetime],
) -> typing.Optional[datetime.datetime]:
    if value is None or isinstance(value, datetime.datetime):
        return value
    return dateutil.parser.parse(value)


def _now() -> datetime.datetime:
    return datetime.datetime.now(tz=datetime.timezone.utc)


C = typing.TypeVar("C", bound="Cookie")


@attr.s(frozen=True)
class Cookie:
    """A cookie string parsed into its components."""

    #: The name of the cookie itself. For example, in ``Set-Cookie:
    #: sessionId=1234``, the name would be ``sessionId``.
    name: str = attr.ib()
    #: The value of the cookie. For example, in ``Set-Cookie:
    #: sessionId=abcdef12345``, the value would be ``abcdef12345``
    value: str = attr.ib()
    #: Whether the cookie was indicated to be forbidden from being accessed by
    #: JavaScript. This is intended to mitigate cross-site scripting.
    httponly: bool = attr.ib(default=False)
    #: Whether the cookie
    secure: bool = attr.ib(default=False)
    domain: typing.Optional[str] = attr.ib(default=None)
    samesite: typing.Optional[SameSitePolicy] = attr.ib(
        default=None, converter=_ssp_from_value
    )
    path: typing.Optional[str] = attr.ib(default=None)
    expires: typing.Optional[datetime.datetime] = attr.ib(
        default=None, converter=_expires_converter
    )
    max_age: typing.Optional[datetime.timedelta] = attr.ib(
        default=None, converter=_max_age_converter
    )
    extensions: typing.Dict[str, str] = attr.ib(factory=dict)
    # NOTE(sigmavirus24): We don't want this to play apart in being compared.
    # Someone _can_ create a Cookie instance from the keywords and we'd want
    # that to be equal to one parsed by us where we store the raw string
    raw: str = attr.ib(
        kw_only=True, default="", repr=False, eq=False, order=False
    )
    _type: CookieType = attr.ib(
        kw_only=True, repr=False, converter=_ct_from_value, default=None
    )
    # Max-Age is a timedelta so we need to know (roughly) when we received the
    # cookie
    _received_at: datetime.datetime = attr.ib(
        init=False, eq=False, order=False, repr=False, factory=_now
    )

    @property
    def domain_provided(self: C) -> bool:
        """Identify whether we should behave as if a domain was provided.

        In the event that the cookie has, for example, ``Domain=example.com.``
        then we must ignore the attribute.

        See also https://tools.ietf.org/html/rfc6265#section-4.1.2.3
        """
        return self.domain is not None and not self.domain.endswith(".")

    def expired(self: C, now: datetime.datetime = None) -> bool:
        """Check if the cookie has expired or not.

        :param now:
            A timezone-aware datetime object representing the time to check
            against. If none is provided, one will be created and used.
        :type now:
            :class:`~datetime.datetime`
        """
        if now is None:
            now = _now()
        if self.max_age is not None:
            # As explained in
            # https://tools.ietf.org/html/rfc6265#section-4.1.2.2
            # Max-Age takes precedence if a cookie has it and expires
            return (self._received_at + self.max_age) < now
        if self.expires is not None:
            return self.expires < now
        return False


_expected_cookie_attributes = frozenset(
    [
        "name",
        "value",
        "httponly",
        "secure",
        "domain",
        "samesite",
        "path",
        "expires",
        "max_age",
    ]
)


def parse(
    cookie_header_type: str, cookie_string: str
) -> typing.Sequence[Cookie]:
    """Parse a string into one or more cookies based on the header type.

    .. doctest::

        >>> from moreos.cookie import parse
        >>> parse("Cookie", "SID=abcd1234; lang=en_US")
        [Cookie(name="SID", value="abcd1234", httponly=False, secure=False,
            domain="", samesite=None, path="", expires=None, max_age=None),
         Cookie(name=lang", value="en_US", httponly=False, secure=False,
            domain="", samesite=None, path="", expires=None, max_age=None)]
        >>> parse(
        ...     "Set-Cookie", "SID=31d4d96e407aad42; Path=/; Secure; HttpOnly"
        ... )
        [Cookie(name="SID", value="31d4d96e407aad42", httponly=True,
            secure=True, domain="", samesite=None, path="/", expires=None,
            max_age=None)]
    """
    cookie_type = CookieType.from_string(cookie_header_type)
    if cookie_type is CookieType.server:
        m = parsing.ABNF.set_cookie_string_re.match(cookie_string)
        if m is None:
            return []
        c = m.groupdict()
        extensions = {
            k: v for k, v in c.items() if k not in _expected_cookie_attributes
        }
        return [
            Cookie(
                c["name"],
                c["value"],
                httponly=(c["httponly"] == "HttpOnly"),
                secure=(c["secure"] == "Secure"),
                domain=c["domain"],
                samesite=c["samesite"],
                path=c["path"],
                expires=c["expires"],
                max_age=c["max_age"],
                extensions=extensions,
                raw=cookie_string,
                type=cookie_type,
            )
        ]
    if cookie_type is CookieType.client:
        cookies = []
        for m in parsing.ABNF.client_cookie_string_re.finditer(cookie_string):
            cookie_name, cookie_value = m.groups()
            raw = m.group().rstrip("; ")
            cookies.append(
                Cookie(
                    cookie_name,
                    cookie_value,
                    raw=raw,
                    type=cookie_type,
                )
            )
        return cookies
    return []
