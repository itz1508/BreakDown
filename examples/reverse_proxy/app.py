"""Async HTTP/1.1 reverse-proxy example with grouped backends and host-scoped tenants.

Educational reference service; not a production edge proxy or authorization system.
All configured origins are operator-controlled; incoming requests cannot select an origin.
"""

from __future__ import annotations

import asyncio
import os
import re
from collections.abc import Iterable
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated, Self

import httpx
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import PlainTextResponse, Response
from starlette.routing import Route

# Hop-by-hop fields cannot cross proxy connections. Connection-nominated fields
# must also be discarded (RFC 9110, Section 7.6.1).
HOP_HEADERS = frozenset(
    {
        "connection",
        "keep-alive",
        "proxy-connection",
        "proxy-authenticate",
        "proxy-authorization",
        "te",
        "trailer",
        "transfer-encoding",
        "upgrade",
    }
)
SPOOFABLE_HEADERS = frozenset({"forwarded", "x-forwarded-for", "x-forwarded-host", "x-forwarded-proto", "x-tenant-id"})
HOST_LABEL = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$")
MAX_REQUEST_BYTES = 1_048_576
MAX_RESPONSE_BYTES = 4_194_304


def normalize_host(raw: str) -> str:
    """Accept DNS hostnames and optional port, but no user-info, schemes or paths."""
    value = raw.lower().strip()
    if ":" in value:
        name, separator, port = value.rpartition(":")
        if separator and port.isdecimal() and 1 <= int(port) <= 65535:
            value = name
        else:
            raise ValueError("invalid Host header")
    if not 1 <= len(value) <= 253 or any(not HOST_LABEL.fullmatch(label) for label in value.split(".")):
        raise ValueError("invalid Host header")
    return value


class Endpoint(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str = Field(min_length=1)
    origin: str

    @field_validator("origin")
    @classmethod
    def valid_origin(cls, value: str) -> str:
        try:
            url = httpx.URL(value)
        except (ValueError, httpx.InvalidURL) as exc:
            raise ValueError("invalid origin URL") from exc
        if (
            url.scheme not in {"http", "https"}
            or not url.host
            or url.username
            or url.password
            or url.path not in {"", "/"}
            or url.query
            or url.fragment
        ):
            raise ValueError("origin must be an absolute http(s) authority without credentials, path or query")
        return str(url).rstrip("/")


class BackendGroup(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str = Field(min_length=1)
    backends: tuple[Endpoint, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_backends(self) -> Self:
        ids = [endpoint.name for endpoint in self.backends]
        if len(set(ids)) != len(ids):
            raise ValueError("duplicate backend name within group")
        return self


class Tenant(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str = Field(min_length=1)
    hosts: tuple[str, ...] = Field(min_length=1)
    groups: tuple[BackendGroup, ...] = Field(min_length=1)

    @field_validator("hosts")
    @classmethod
    def valid_hosts(cls, hosts: tuple[str, ...]) -> tuple[str, ...]:
        canonical = tuple(normalize_host(h) for h in hosts)
        if len(set(canonical)) != len(canonical):
            raise ValueError("duplicate tenant hostname")
        return canonical

    @model_validator(mode="after")
    def unique_groups(self) -> Self:
        if len({group.name for group in self.groups}) != len(self.groups):
            raise ValueError("duplicate backend group name within tenant")
        return self


class ProxyConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    tenants: tuple[Tenant, ...] = Field(min_length=1)
    connect_timeout_seconds: Annotated[float, Field(gt=0, le=30)] = 3.0
    request_timeout_seconds: Annotated[float, Field(gt=0, le=120)] = 10.0

    @model_validator(mode="after")
    def unique_tenants_and_hosts(self) -> Self:
        names = [t.name for t in self.tenants]
        hosts = [host for tenant in self.tenants for host in tenant.hosts]
        if len(set(names)) != len(names) or len(set(hosts)) != len(hosts):
            raise ValueError("tenant names and hostnames must be globally unique")
        return self


class Router:
    """One canonical selection owner: group RR, then endpoint RR per tenant/group."""

    def __init__(self, config: ProxyConfig) -> None:
        self.by_host = {host: t for t in config.tenants for host in t.hosts}
        self._group_next: dict[str, int] = {}
        self._endpoint_next: dict[tuple[str, str], int] = {}
        self._lock = asyncio.Lock()

    async def candidates(self, tenant: Tenant) -> tuple[Endpoint, ...]:
        """Rotate candidates without mixing counters or backends between tenants."""
        async with self._lock:
            group_pos = self._group_next.get(tenant.name, 0)
            self._group_next[tenant.name] = group_pos + 1
            groups = tenant.groups[group_pos % len(tenant.groups) :] + tenant.groups[: group_pos % len(tenant.groups)]
            result: list[Endpoint] = []
            for group_index, group in enumerate(groups):
                key = (tenant.name, group.name)
                endpoint_pos = self._endpoint_next.get(key, 0)
                if group_index == 0:
                    self._endpoint_next[key] = endpoint_pos + 1
                endpoints = group.backends
                offset = endpoint_pos % len(endpoints)
                result.extend(endpoints[offset:] + endpoints[:offset])
            return tuple(result)


def _filtered_headers(headers: Iterable[tuple[str, str]], *, request: bool) -> list[tuple[str, str]]:
    pairs = list(headers)
    nominated = {
        part.strip().lower() for name, value in pairs if name.lower() == "connection" for part in value.split(",")
    }
    banned = HOP_HEADERS | nominated | {"content-length"}
    if request:
        banned = banned | SPOOFABLE_HEADERS | {"host"}
    return [(name, value) for name, value in pairs if name.lower() not in banned]


async def _read_request(request: Request) -> bytes:
    body = bytearray()
    async for chunk in request.stream():
        if len(body) + len(chunk) > MAX_REQUEST_BYTES:
            raise ValueError("request body exceeds size limit")
        body.extend(chunk)
    return bytes(body)


async def _read_response(response: httpx.Response) -> bytes:
    # Mock transports may provide a fully buffered response before stream entry.
    if response.is_stream_consumed:
        if len(response.content) > MAX_RESPONSE_BYTES:
            raise ValueError("upstream response exceeds size limit")
        return response.content
    body = bytearray()
    async for chunk in response.aiter_raw():
        if len(body) + len(chunk) > MAX_RESPONSE_BYTES:
            raise ValueError("upstream response exceeds size limit")
        body.extend(chunk)
    return bytes(body)


def create_app(config: ProxyConfig, client: httpx.AsyncClient | None = None) -> Starlette:
    """Factory for an ASGI proxy. Inject a fake client to test without network effects."""
    router = Router(config)
    own_client = client is None
    if client is None:
        client = httpx.AsyncClient(
            follow_redirects=False,
            timeout=httpx.Timeout(config.request_timeout_seconds, connect=config.connect_timeout_seconds),
            trust_env=False,  # never inherit HTTP(S)_PROXY for configured upstream connections
        )

    @asynccontextmanager
    async def lifespan(_app: Starlette):
        try:
            yield
        finally:
            if own_client:
                await client.aclose()

    async def handle(request: Request) -> Response:
        host_fields = [v.decode("latin-1") for k, v in request.scope["headers"] if k.lower() == b"host"]
        if len(host_fields) != 1:
            return PlainTextResponse("exactly one Host header is required", status_code=400)
        try:
            host = normalize_host(host_fields[0])
        except ValueError:
            return PlainTextResponse("invalid Host header", status_code=400)
        tenant = router.by_host.get(host)
        if tenant is None:
            return PlainTextResponse("unknown tenant", status_code=421)
        if "transfer-encoding" in request.headers and "content-length" in request.headers:
            return PlainTextResponse("ambiguous request framing", status_code=400)
        lengths = request.headers.getlist("content-length")
        if len(lengths) > 1 or (lengths and (not lengths[0].isdecimal() or int(lengths[0]) > MAX_REQUEST_BYTES)):
            return PlainTextResponse("invalid or excessive Content-Length", status_code=413)
        try:
            body = await _read_request(request)
        except ValueError:
            return PlainTextResponse("request body too large", status_code=413)

        raw_path = request.scope.get("raw_path", b"/").decode("ascii", errors="strict")
        if not raw_path.startswith("/"):
            return PlainTextResponse("invalid path", status_code=400)
        query = request.scope.get("query_string", b"")
        suffix = request.scope.get("raw_path", b"/") + (b"?" + query if query else b"")
        headers = _filtered_headers(
            ((key.decode("latin-1"), value.decode("latin-1")) for key, value in request.headers.raw),
            request=True,
        )
        headers.extend((("x-forwarded-host", host), ("x-forwarded-proto", request.url.scheme)))

        candidates = await router.candidates(tenant)
        for endpoint in candidates:
            url = httpx.URL(endpoint.origin).copy_with(raw_path=suffix)
            try:
                # A returned HTTP 4xx/5xx is the backend's response, not a connection failure.
                # Never retry ambiguous effects after request bytes may have been transmitted.
                async with client.stream(
                    request.method, url, headers=headers, content=body, follow_redirects=False
                ) as upstream:
                    predecoded = upstream.is_stream_consumed
                    try:
                        raw = await _read_response(upstream)
                    except ValueError:
                        return PlainTextResponse("upstream response too large", status_code=502)
                    filtered = _filtered_headers(upstream.headers.multi_items(), request=False)
                    if predecoded:
                        # A prebuffered injected transport may have decoded the payload.
                        # Never forward a stale Content-Encoding for decoded bytes.
                        filtered = [(k, v) for k, v in filtered if k.lower() != "content-encoding"]
                    # HEAD and bodyless statuses must not send the representation body.
                    if request.method == "HEAD" or upstream.status_code in {204, 304}:
                        raw = b""
                    reply = Response(content=raw, status_code=upstream.status_code)
                    # Preserve duplicate Set-Cookie and content-encoding metadata.
                    allowed = [(name.encode("latin-1"), value.encode("latin-1")) for name, value in filtered]
                    if request.method == "HEAD" and upstream.status_code not in {204, 304}:
                        # A HEAD response may advertise the GET representation size.
                        length = upstream.headers.get("content-length", str(len(raw)))
                        allowed.append((b"content-length", length.encode("ascii")))
                    elif upstream.status_code not in {204, 304}:
                        allowed.append((b"content-length", str(len(raw)).encode("ascii")))
                    reply.raw_headers = allowed
                    return reply
            except (httpx.ConnectError, httpx.ConnectTimeout):
                continue  # A connection was not established; no request was sent.
            except (httpx.TimeoutException, httpx.HTTPError):
                return PlainTextResponse("upstream unavailable", status_code=502)
        return PlainTextResponse("no backend available", status_code=502)

    return Starlette(
        routes=[Route("/{path:path}", handle, methods=["GET", "HEAD", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])],
        lifespan=lifespan,
    )


async def load_config(path: str | Path) -> ProxyConfig:
    """Load the explicitly selected configuration without blocking the event loop."""
    content = await asyncio.to_thread(Path(path).read_text, encoding="utf-8")
    return ProxyConfig.model_validate_json(content)


class ConfiguredProxy:
    """Load on first ASGI event; no synchronous configuration I/O at import."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self._instance: Starlette | None = None
        self._initialize_lock = asyncio.Lock()

    async def __call__(self, scope, receive, send) -> None:
        if self._instance is None:
            async with self._initialize_lock:
                if self._instance is None:
                    config = await load_config(self.path)
                    self._instance = create_app(config)
        await self._instance(scope, receive, send)


# Convenience ASGI import for: PROXY_CONFIG=... uvicorn examples.reverse_proxy.app:app
CONFIG_PATH = Path(os.getenv("PROXY_CONFIG", Path(__file__).with_name("config.example.json")))
app = ConfiguredProxy(CONFIG_PATH)
