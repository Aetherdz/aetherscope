from __future__ import annotations

import ipaddress
import re
from dataclasses import dataclass
from typing import Iterable, List, Optional, Tuple

IN_SCOPE = "in-scope"
OUT_OF_SCOPE = "out-of-scope"
UNKNOWN = "unknown"
ERROR = "error"

_WILDCARD_PREFIX = "*."
_COMMENT_CHARS = ("#", ";")
_URL_SCHEME = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*://")


def _strip_comment(line: str) -> str:
    for marker in _COMMENT_CHARS:
        index = line.find(marker)
        if index != -1:
            line = line[:index]
    return line.strip()


def _split_host_port(text: str) -> Tuple[str, Optional[str]]:
    if text.startswith("["):
        closing = text.find("]")
        if closing != -1:
            host = text[1:closing]
            rest = text[closing + 1 :]
            if rest.startswith(":"):
                return host, rest[1:]
            return host, None
    if text.count(":") == 1:
        host, port = text.rsplit(":", 1)
        if port.isdigit():
            return host, port
    return text, None


def _is_ip(value: str) -> bool:
    try:
        ipaddress.ip_address(value)
        return True
    except ValueError:
        return False


def _is_cidr(value: str) -> bool:
    try:
        ipaddress.ip_network(value, strict=False)
        return True
    except ValueError:
        return False


@dataclass(frozen=True)
class Rule:
    raw: str
    kind: str  # host | wildcard | url | ip | cidr
    excluded: bool
    host: Optional[str] = None
    port: Optional[str] = None
    scheme: Optional[str] = None
    path: Optional[str] = None
    network: Optional[ipaddress._BaseNetwork] = None

    def matches_host(self, host: str) -> bool:
        if self.kind == "host":
            return self.host == host
        if self.kind == "wildcard":
            assert self.host is not None
            return host == self.host or host.endswith("." + self.host)
        return False

    def matches_url(self, scheme: str, host: str, port: Optional[str], path: str) -> bool:
        if self.kind in ("ip", "cidr"):
            return False
        if self.kind == "url":
            if self.scheme and self.scheme.lower() != scheme.lower():
                return False
            if not self.matches_host(host):
                return False
            if self.port and self.port != (port or ""):
                return False
            if self.path and not path.startswith(self.path):
                return False
            return True
        if self.kind in ("host", "wildcard"):
            if not self.matches_host(host):
                return False
            if self.port and self.port != (port or ""):
                return False
            if self.scheme and self.scheme.lower() != scheme.lower():
                return False
            if self.path and not path.startswith(self.path):
                return False
            return True
        return False

    def matches_ip(self, ip: ipaddress._BaseAddress) -> bool:
        if self.kind == "ip":
            assert self.network is not None
            return ip == self.network.network_address
        if self.kind == "cidr":
            assert self.network is not None
            return ip in self.network
        return False


def parse_rule(raw_line: str) -> Optional[Rule]:
    text = _strip_comment(raw_line)
    if not text:
        return None

    excluded = False
    body = text
    while body.startswith("!"):
        excluded = True
        body = body[1:].lstrip()

    scheme = None
    path = None
    if _URL_SCHEME.match(body):
        scheme, _, remainder = body.partition("://")
        slash = remainder.find("/")
        if slash != -1:
            authority, path = remainder[:slash], remainder[slash:]
        else:
            authority = remainder
        host_part, port = _split_host_port(authority)
        if host_part:
            if host_part.startswith(_WILDCARD_PREFIX):
                return Rule(
                    raw=raw_line.strip(),
                    kind="wildcard",
                    excluded=excluded,
                    host=host_part[2:],
                    port=port,
                    scheme=scheme,
                    path=path,
                )
            if _is_ip(host_part):
                return Rule(
                    raw=raw_line.strip(),
                    kind="ip",
                    excluded=excluded,
                    host=host_part,
                    port=port,
                    scheme=scheme,
                    path=path,
                    network=ipaddress.ip_address(host_part),
                )
            return Rule(
                raw=raw_line.strip(),
                kind="host",
                excluded=excluded,
                host=host_part,
                port=port,
                scheme=scheme,
                path=path,
            )

    if _is_cidr(body):
        network = ipaddress.ip_network(body, strict=False)
        return Rule(
            raw=raw_line.strip(),
            kind="cidr",
            excluded=excluded,
            network=network,
        )

    if _is_ip(body):
        return Rule(
            raw=raw_line.strip(),
            kind="ip",
            excluded=excluded,
            host=body,
            network=ipaddress.ip_address(body),
        )

    host_part, port = _split_host_port(body)
    if host_part:
        if host_part.startswith(_WILDCARD_PREFIX):
            return Rule(
                raw=raw_line.strip(),
                kind="wildcard",
                excluded=excluded,
                host=host_part[2:],
                port=port,
            )
        return Rule(
            raw=raw_line.strip(),
            kind="host",
            excluded=excluded,
            host=host_part,
            port=port,
        )

    return None


class Scope:
    def __init__(self, rules: Optional[Iterable[Rule]] = None) -> None:
        self.rules: List[Rule] = list(rules or [])

    @classmethod
    def from_text(cls, text: str) -> "Scope":
        rules = [rule for rule in (parse_rule(line) for line in text.splitlines()) if rule]
        return cls(rules)

    @classmethod
    def from_file(cls, path: str) -> "Scope":
        with open(path, "r", encoding="utf-8", errors="replace") as handle:
            return cls.from_text(handle.read())

    def add_line(self, line: str) -> None:
        rule = parse_rule(line)
        if rule:
            self.rules.append(rule)

    def classify_host(self, host: str, port: Optional[str] = None) -> Tuple[str, Optional[Rule]]:
        for rule in self.rules:
            if rule.excluded and rule.matches_host(host):
                if rule.port and rule.port != (port or ""):
                    continue
                return OUT_OF_SCOPE, rule
        for rule in self.rules:
            if not rule.excluded and rule.matches_host(host):
                if rule.port and rule.port != (port or ""):
                    continue
                return IN_SCOPE, rule
        return UNKNOWN, None

    def classify_ip(self, ip: str) -> Tuple[str, Optional[Rule]]:
        try:
            address = ipaddress.ip_address(ip)
        except ValueError:
            return ERROR, None
        for rule in self.rules:
            if rule.excluded and rule.matches_ip(address):
                return OUT_OF_SCOPE, rule
        for rule in self.rules:
            if not rule.excluded and rule.matches_ip(address):
                return IN_SCOPE, rule
        return UNKNOWN, None

    def classify_url(self, url: str) -> Tuple[str, Optional[Rule]]:
        scheme, _, rest = url.partition("://")
        if not scheme or not rest:
            return ERROR, None
        slash = rest.find("/")
        if slash != -1:
            authority, path = rest[:slash], rest[slash:]
        else:
            authority, path = rest, "/"
        host, port = _split_host_port(authority)
        if not host:
            return ERROR, None
        if _is_ip(host):
            verdict, rule = self.classify_ip(host)
            if rule is not None and rule.kind in ("host", "wildcard", "url"):
                if rule.kind == "url" and rule.matches_url(scheme, host, port, path):
                    return OUT_OF_SCOPE if rule.excluded else IN_SCOPE, rule
                if rule.kind in ("host", "wildcard"):
                    if rule.scheme and rule.scheme.lower() != scheme.lower():
                        return verdict, rule
                    if rule.port and rule.port != (port or ""):
                        return verdict, rule
                    return OUT_OF_SCOPE if rule.excluded else IN_SCOPE, rule
            if rule is not None:
                return verdict, rule
            return verdict, rule

        for rule in self.rules:
            if rule.excluded and rule.matches_url(scheme, host, port, path):
                return OUT_OF_SCOPE, rule
        for rule in self.rules:
            if not rule.excluded and rule.matches_url(scheme, host, port, path):
                return IN_SCOPE, rule
        return UNKNOWN, None

    def classify(self, target: str) -> Tuple[str, Optional[Rule]]:
        if "://" in target:
            return self.classify_url(target)
        host, port = _split_host_port(target)
        if not host:
            return ERROR, None
        if _is_ip(host):
            return self.classify_ip(host)
        return self.classify_host(host, port)
