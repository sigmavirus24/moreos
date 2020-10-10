"""Parsing utilities for Cookie strings."""
import re

import attr


@attr.s(frozen=True)
class ABNF:
    """Container of regular expressions both raw and compiled for parsing."""

    # From https://tools.ietf.org/html/rfc2616#section-2.2
    ctl = control_characters = "\x7f\x00-\x1f"
    digit = "0-9"
    separators = r"\[\]\(\)<>@,;:\\\"/?={}\s"
    token = f"[^{ctl}{separators}]+"
    # RFC1123 date components
    wkday = "(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun)"
    month = "(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)"
    time = f"[{digit}]{{2}}:[{digit}]{{2}}:[{digit}]{{2}}"
    date1 = f"[{digit}]{{1,2}} {month} [{digit}]{{4}}"
    # NOTE(sigmavirus24) This allows some nonsense but it's a decent
    # high-level check
    rfc1123_date = f"{wkday}, {date1} {time} GMT"

    # From https://tools.ietf.org/html/rfc1034#section-3.5, enhanced by
    # https://tools.ietf.org/html/rfc1123#section-2.1
    letter = "A-Za-z"
    let_dig = f"{letter}{digit}"
    let_dig_hyp = f"{let_dig}-"
    ldh_str = f"[{let_dig_hyp}]+"
    # This is where the update from rfc1123#section2.1 is relevant
    label = f"[{let_dig}](?:(?:{ldh_str})?[{let_dig}])?"
    subdomain = f"\\.?(?:{label}\\.)*(?:{label})"

    # From https://tools.ietf.org/html/rfc6265#section-3.1
    # NOTE: \x5b = [, \x5d = ] so let's escape those directly
    cookie_octet = "[\x21\x23-\x2b\\\x2d-\x3a\x3c-\\[\\]-\x7e]"
    cookie_value = f'(?:{cookie_octet}*|"{cookie_octet}*")'
    cookie_name = token
    cookie_pair = f"(?P<name>{cookie_name})=(?P<value>{cookie_value})"

    _any_char_except_ctls_or_semicolon = f"[^;{ctl}]+"
    extension_av = _any_char_except_ctls_or_semicolon
    httponly_av = "(?P<httponly>HttpOnly)"
    secure_av = "(?P<secure>Secure)"
    path_value = _any_char_except_ctls_or_semicolon
    path_av = f"Path=(?P<path>{path_value})"
    domain_value = subdomain
    domain_av = f"Domain=(?P<domain>{domain_value})"
    non_zero_digit = "1-9"
    max_age_av = f"Max-Age=(?P<max_age>[{non_zero_digit}][{digit}]*)"
    sane_cookie_date = rfc1123_date
    expires_av = f"Expires=(?P<expires>{sane_cookie_date})"
    samesite_value = "(?:Strict|Lax|None)"
    samesite_av = f"SameSite=(?P<samesite>{samesite_value})"
    cookie_av = (
        f"(?:{expires_av}|{max_age_av}|{domain_av}|{path_av}|"
        f"{secure_av}|{httponly_av}|{samesite_av}|{extension_av})"
    )
    set_cookie_string = f"{cookie_pair}(?:; {cookie_av})*"

    # Not specified in either RFC
    client_cookie_string = f"(?:({cookie_name})=({cookie_value}))(?:; )?"

    # Pre-compiled version of the above abnf
    separators_re = re.compile(f"[{separators}]+")
    control_characters_re = re.compile(f"[{ctl}]+")
    cookie_name_re = token_re = re.compile(token)
    cookie_value_re = re.compile(cookie_value)
    set_cookie_string_re = re.compile(set_cookie_string)
    client_cookie_string_re = re.compile(client_cookie_string)
