"""Behavioral checks for all four cumulative proxy requirements."""

from __future__ import annotations

import asyncio
import gzip
from functools import wraps
from pathlib import Path

import httpx
import pytest
import uvicorn
from pydantic import ValidationError

from examples.reverse_proxy.app import Endpoint, ProxyConfig, create_app, load_config


def run_async(fn):
    """Execute coroutine tests without requiring a separate pytest plugin."""

    @wraps(fn)
    def wrapped(*args, **kwargs):
        return asyncio.run(fn(*args, **kwargs))

    return wrapped


@pytest.fixture
def config() -> ProxyConfig:
    return ProxyConfig.model_validate(
        {
            "tenants": [
                {
                    "name": "alpha",
                    "hosts": ["alpha.example"],
                    "groups": [
                        {
                            "name": "east",
                            "backends": [
                                {"name": "a1", "origin": "http://a1:8000"},
                                {"name": "a2", "origin": "http://a2:8000"},
                            ],
                        },
                        {"name": "west", "backends": [{"name": "a3", "origin": "http://a3:8000"}]},
                    ],
                },
                {
                    "name": "beta",
                    "hosts": ["beta.example"],
                    "groups": [
                        {
                            "name": "only",
                            "backends": [{"name": "b1", "origin": "http://b1:8000"}],
                        },
                    ],
                },
            ]
        }
    )


@run_async
async def test_round_robin_hierarchical_and_tenant_isolation(config: ProxyConfig) -> None:
    observed: list[str] = []

    async def upstream(request: httpx.Request) -> httpx.Response:
        observed.append(request.url.host)
        return httpx.Response(200, text=request.url.host)

    backend = httpx.AsyncClient(transport=httpx.MockTransport(upstream))
    app = create_app(config, backend)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://alpha.example") as user:
        results = [(await user.get("/path?x=2")).text for _ in range(5)]
        beta = (await user.get("/", headers={"host": "beta.example"})).text
        next_alpha = (await user.get("/")).text
    assert results == ["a1", "a3", "a2", "a3", "a1"]
    assert beta == "b1"
    assert next_alpha == "a3"
    assert observed == [*results, beta, next_alpha]
    await backend.aclose()


@run_async
async def test_unknown_tenant_and_spoofed_identity_denied(config: ProxyConfig) -> None:
    seen = []

    async def upstream(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        assert "x-tenant-id" not in request.headers
        assert request.headers["x-forwarded-host"] == "alpha.example"
        assert request.headers["x-forwarded-proto"] == "http"
        assert request.headers["host"] == "a1:8000"
        return httpx.Response(200, text="alpha")

    backend = httpx.AsyncClient(transport=httpx.MockTransport(upstream))
    app = create_app(config, backend)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://unknown.example") as user:
        assert (await user.get("/")).status_code == 421
        result = await user.get(
            "/", headers={"host": "alpha.example", "x-tenant-id": "beta", "x-forwarded-host": "beta.example"}
        )
        assert result.status_code == 200
    assert len(seen) == 1
    await backend.aclose()


@run_async
async def test_connect_failover_and_no_retry_after_http_response(config: ProxyConfig) -> None:
    attempts: list[str] = []

    async def upstream(request: httpx.Request) -> httpx.Response:
        attempts.append(request.url.host)
        if request.url.host == "a1":
            raise httpx.ConnectError("offline", request=request)
        return httpx.Response(503, text="upstream unavailable")

    backend = httpx.AsyncClient(transport=httpx.MockTransport(upstream))
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=create_app(config, backend)),
        base_url="http://alpha.example",
    ) as user:
        response = await user.get("/")
    assert response.status_code == 503
    assert attempts == ["a1", "a2"]
    await backend.aclose()


@run_async
async def test_async_concurrency(config: ProxyConfig) -> None:
    active = peak = 0

    async def upstream(request: httpx.Request) -> httpx.Response:
        nonlocal active, peak
        active += 1
        peak = max(active, peak)
        await asyncio.sleep(0.02)
        active -= 1
        return httpx.Response(200, text="ok")

    backend = httpx.AsyncClient(transport=httpx.MockTransport(upstream))
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=create_app(config, backend)),
        base_url="http://alpha.example",
    ) as user:
        results = await asyncio.gather(*(user.get("/") for _ in range(8)))
    assert all(r.status_code == 200 for r in results)
    assert peak >= 2
    await backend.aclose()


@run_async
async def test_request_body_and_hop_header_filter(config: ProxyConfig) -> None:
    seen = []

    async def upstream(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        assert request.content == b"hello"
        assert "x-unsafe" not in request.headers
        # HTTPX may synthesize its own connection header; the nominated
        # unsafe header must not cross the proxy boundary.
        return httpx.Response(201, headers=[("set-cookie", "a=1"), ("set-cookie", "b=2")], content=b"done")

    backend = httpx.AsyncClient(transport=httpx.MockTransport(upstream))
    app = create_app(config, backend)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://alpha.example") as user:
        response = await user.post("/new", content=b"hello", headers={"connection": "x-unsafe", "x-unsafe": "drop"})
    assert response.status_code == 201
    assert response.text == "done"
    assert response.headers.get_list("set-cookie") == ["a=1", "b=2"]
    assert len(seen) == 1
    await backend.aclose()


@run_async
async def test_body_limit(config: ProxyConfig) -> None:
    backend = httpx.AsyncClient(transport=httpx.MockTransport(lambda _: httpx.Response(200)))
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=create_app(config, backend)),
        base_url="http://alpha.example",
    ) as user:
        response = await user.post("/", content=b"x" * (1024 * 1024 + 1))
    assert response.status_code == 413
    await backend.aclose()


@run_async
async def test_backend_down_is_bad_gateway(config: ProxyConfig) -> None:
    def fail(req: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("down", request=req)

    backend = httpx.AsyncClient(transport=httpx.MockTransport(fail))
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=create_app(config, backend)),
        base_url="http://alpha.example",
    ) as user:
        response = await user.get("/")
    assert response.status_code == 502
    await backend.aclose()


@pytest.mark.parametrize(
    "bad",
    [
        "http://host.invalid/path",
        "file:///etc/passwd",
        "https://user:pass@example.com",
        "http://x/?y=z",
        "http://x/#frag",
    ],
)
def test_disallow_unsafe_upstream_urls(bad: str) -> None:
    with pytest.raises(ValidationError):
        Endpoint(name="bad", origin=bad)


def test_duplicate_tenant_host_denied(config: ProxyConfig) -> None:
    data = config.model_dump()
    data["tenants"][1]["hosts"] = ["alpha.example"]
    with pytest.raises(ValidationError, match="globally unique"):
        ProxyConfig.model_validate(data)


def test_config_example_parses() -> None:
    path = Path(__file__).parents[2] / "examples/reverse_proxy/config.example.json"
    loaded = asyncio.run(load_config(path))
    assert len(loaded.tenants) == 2
    assert loaded.tenants[0].groups[0].backends[1].name == "a2"


@run_async
async def test_duplicate_host_header_is_rejected(config: ProxyConfig) -> None:
    backend = httpx.AsyncClient(transport=httpx.MockTransport(lambda _: httpx.Response(200)))
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=create_app(config, backend))) as user:
        request = httpx.Request(
            "GET", "http://alpha.example/", headers=[("host", "alpha.example"), ("host", "beta.example")]
        )
        response = await user.send(request)
    assert response.status_code == 400
    await backend.aclose()


@run_async
async def test_untrusted_location_never_redirects_upstream(config: ProxyConfig) -> None:
    attempted: list[str] = []

    def upstream(request: httpx.Request) -> httpx.Response:
        attempted.append(request.url.host)
        return httpx.Response(302, headers={"location": "http://untrusted.example/"})

    backend = httpx.AsyncClient(transport=httpx.MockTransport(upstream), follow_redirects=True)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=create_app(config, backend)),
        base_url="http://alpha.example",
    ) as user:
        response = await user.get("/")
    assert response.status_code == 302
    assert attempted == ["a1"]
    await backend.aclose()


@run_async
async def test_no_retry_after_read_failure(config: ProxyConfig) -> None:
    attempted: list[str] = []

    def upstream(request: httpx.Request) -> httpx.Response:
        attempted.append(request.url.host)
        raise httpx.ReadTimeout("uncertain effect", request=request)

    backend = httpx.AsyncClient(transport=httpx.MockTransport(upstream))
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=create_app(config, backend)),
        base_url="http://alpha.example",
    ) as user:
        response = await user.post("/", content="mutating")
    assert response.status_code == 502
    assert attempted == ["a1"]
    await backend.aclose()


@run_async
async def test_encoded_path_and_query_cannot_override_origin(config: ProxyConfig) -> None:
    seen = []

    def upstream(request: httpx.Request) -> httpx.Response:
        seen.append(request.url)
        return httpx.Response(200, text="ok")

    backend = httpx.AsyncClient(transport=httpx.MockTransport(upstream))
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=create_app(config, backend)),
        base_url="http://alpha.example",
    ) as user:
        response = await user.get("/%2f%2funtrusted.example/x?target=%23value")
    assert response.status_code == 200
    assert seen[0].host == "a1"
    assert seen[0].raw_path == b"/%2f%2funtrusted.example/x?target=%23value"
    await backend.aclose()


@run_async
async def test_large_upstream_response_blocked(config: ProxyConfig) -> None:
    backend = httpx.AsyncClient(
        transport=httpx.MockTransport(lambda _: httpx.Response(200, content=b"x" * (4_194_304 + 1)))
    )
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=create_app(config, backend)),
        base_url="http://alpha.example",
    ) as user:
        response = await user.get("/")
    assert response.status_code == 502
    await backend.aclose()


@run_async
async def test_configured_asgi_import_works(config: ProxyConfig, tmp_path: Path) -> None:
    from examples.reverse_proxy.app import ConfiguredProxy

    file = tmp_path / "proxy.json"
    await asyncio.to_thread(file.write_text, config.model_dump_json(), encoding="utf-8")
    app = ConfiguredProxy(file)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://unknown.example") as user:
        response = await user.get("/")
    assert response.status_code == 421


@run_async
async def test_connected_http_server_to_backend() -> None:
    backend_seen: list[bytes] = []

    async def backend_handler(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        request = await reader.readuntil(b"\r\n\r\n")
        backend_seen.append(request)
        body = b"backend-http-e2e"
        writer.write(
            b"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: "
            + str(len(body)).encode("ascii")
            + b"\r\nConnection: close\r\n\r\n"
            + body
        )
        await writer.drain()
        writer.close()
        await writer.wait_closed()

    backend = await asyncio.start_server(backend_handler, "127.0.0.1", 0)
    port = backend.sockets[0].getsockname()[1]
    config = ProxyConfig.model_validate(
        {
            "tenants": [
                {
                    "name": "alpha",
                    "hosts": ["alpha.example"],
                    "groups": [
                        {"name": "primary", "backends": [{"name": "origin-1", "origin": f"http://127.0.0.1:{port}"}]}
                    ],
                }
            ]
        }
    )
    server = uvicorn.Server(uvicorn.Config(create_app(config), host="127.0.0.1", port=0, log_level="critical"))
    run = asyncio.create_task(server.serve())
    try:
        for _ in range(100):
            if server.started and server.servers:
                break
            await asyncio.sleep(0.01)
        assert server.started, "ASGI server did not start"
        proxy_port = server.servers[0].sockets[0].getsockname()[1]
        async with httpx.AsyncClient(timeout=3, trust_env=False) as client:
            response = await client.get(
                f"http://127.0.0.1:{proxy_port}/api?hello=world", headers={"Host": "alpha.example"}
            )
        assert response.status_code == 200
        assert response.content == b"backend-http-e2e"
        assert b"GET /api?hello=world HTTP/1.1" in backend_seen[0]
        assert b"x-forwarded-host: alpha.example" in backend_seen[0].lower()
    finally:
        server.should_exit = True
        await asyncio.wait_for(run, 5)
        backend.close()
        await backend.wait_closed()


@run_async
async def test_compressed_response_preserves_wire_encoding(config: ProxyConfig) -> None:
    compressed = gzip.compress(b"compressed upstream representation")

    def upstream(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=compressed, headers={"content-encoding": "gzip"})

    backend = httpx.AsyncClient(transport=httpx.MockTransport(upstream))
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=create_app(config, backend)),
        base_url="http://alpha.example",
    ) as client:
        response = await client.get("/")
    assert response.status_code == 200
    assert response.content == b"compressed upstream representation"  # client decoded once
    assert "content-encoding" not in response.headers  # injected transport predecoded upstream
    await backend.aclose()


@run_async
async def test_head_has_no_body_and_retains_representation_length(config: ProxyConfig) -> None:
    def upstream(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=b"", headers={"content-length": "123"})

    backend = httpx.AsyncClient(transport=httpx.MockTransport(upstream))
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=create_app(config, backend)),
        base_url="http://alpha.example",
    ) as client:
        response = await client.head("/")
    assert response.status_code == 200
    assert response.content == b""
    assert response.headers["content-length"] == "123"
    await backend.aclose()
