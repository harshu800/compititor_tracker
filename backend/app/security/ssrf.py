"""
SSRF protection for the crawler.

Every user-submitted URL must pass through `validate_and_resolve_url` before
any network request is made. This is defense-in-depth: we validate scheme,
hostname shape, AND the resolved IP address (to stop DNS-rebinding attacks
where a hostname resolves to a private IP at request time even if it looked
public at validation time).
"""
import ipaddress
import socket
from dataclasses import dataclass
from urllib.parse import urlparse

ALLOWED_SCHEMES = {"http", "https"}

# RFC1918 / loopback / link-local / metadata / reserved ranges.
BLOCKED_NETWORKS = [
    ipaddress.ip_network("127.0.0.0/8"),      # loopback
    ipaddress.ip_network("10.0.0.0/8"),        # private
    ipaddress.ip_network("172.16.0.0/12"),     # private
    ipaddress.ip_network("192.168.0.0/16"),    # private
    ipaddress.ip_network("169.254.0.0/16"),    # link-local (incl. cloud metadata 169.254.169.254)
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("100.64.0.0/10"),     # carrier-grade NAT
    ipaddress.ip_network("192.0.0.0/24"),
    ipaddress.ip_network("198.18.0.0/15"),
    ipaddress.ip_network("::1/128"),           # IPv6 loopback
    ipaddress.ip_network("fc00::/7"),          # IPv6 unique local
    ipaddress.ip_network("fe80::/10"),         # IPv6 link-local
]

BLOCKED_HOSTNAMES = {
    "localhost", "metadata.google.internal", "metadata.internal",
}


class SSRFValidationError(ValueError):
    pass


@dataclass
class ResolvedURL:
    original_url: str
    hostname: str
    scheme: str
    resolved_ip: str


def _is_blocked_ip(ip_str: str) -> bool:
    ip = ipaddress.ip_address(ip_str)
    if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast or ip.is_reserved or ip.is_unspecified:
        return True
    for net in BLOCKED_NETWORKS:
        if ip in net:
            return True
    return False


def validate_and_resolve_url(raw_url: str) -> ResolvedURL:
    """Raises SSRFValidationError if the URL is unsafe to fetch.
    Returns the resolved IP so the caller can pin the connection to it
    (preventing TOCTOU DNS-rebinding between validation and fetch)."""
    if not raw_url or len(raw_url) > 2048:
        raise SSRFValidationError("URL missing or too long")

    parsed = urlparse(raw_url)

    if parsed.scheme not in ALLOWED_SCHEMES:
        raise SSRFValidationError(f"Scheme '{parsed.scheme}' not allowed; only http/https")

    hostname = parsed.hostname
    if not hostname:
        raise SSRFValidationError("URL has no hostname")

    hostname_lower = hostname.lower()
    if hostname_lower in BLOCKED_HOSTNAMES:
        raise SSRFValidationError(f"Hostname '{hostname}' is blocked")

    if parsed.username or parsed.password:
        raise SSRFValidationError("URLs with embedded credentials are not allowed")

    # If hostname is already a literal IP, validate directly.
    try:
        literal_ip = ipaddress.ip_address(hostname_lower)
        if _is_blocked_ip(str(literal_ip)):
            raise SSRFValidationError(f"IP address {literal_ip} is not publicly routable")
        return ResolvedURL(raw_url, hostname, parsed.scheme, str(literal_ip))
    except ValueError:
        pass  # not a literal IP, fall through to DNS resolution

    # Resolve DNS and check every returned address (A and AAAA).
    try:
        addr_infos = socket.getaddrinfo(hostname, None)
    except socket.gaierror as e:
        raise SSRFValidationError(f"DNS resolution failed for '{hostname}': {e}")

    if not addr_infos:
        raise SSRFValidationError(f"No addresses resolved for '{hostname}'")

    resolved_ips = []
    for family, _, _, _, sockaddr in addr_infos:
        ip_str = sockaddr[0]
        if _is_blocked_ip(ip_str):
            raise SSRFValidationError(
                f"Hostname '{hostname}' resolves to a non-public address ({ip_str}); blocked"
            )
        resolved_ips.append(ip_str)

    return ResolvedURL(raw_url, hostname, parsed.scheme, resolved_ips[0])


def is_safe_url(raw_url: str) -> bool:
    try:
        validate_and_resolve_url(raw_url)
        return True
    except SSRFValidationError:
        return False


def is_safe_url_verbose(raw_url: str) -> tuple[bool, str | None]:
    """Same check as is_safe_url, but also returns the specific reason on
    failure — for server-side logging only. API responses should keep
    using the generic is_safe_url() + a generic client-facing message;
    revealing exactly why a URL was rejected (e.g. 'resolves to 10.x.x.x')
    is itself information a real attacker probing internal infrastructure
    could use, so that detail belongs in your own logs, not the response."""
    try:
        validate_and_resolve_url(raw_url)
        return True, None
    except SSRFValidationError as e:
        return False, str(e)
