# Reverse proxy and hierarchical async load balancer

One **reference implementation** supporting four cumulative requirements without maintaining four competing runtime versions:

1. Reverse proxy with round-robin backend selection.
2. Hierarchical backends (`Tenant` → `BackendGroup` → `Endpoint`), with group-level round-robin and endpoint-level round-robin.
3. Nonblocking request forwarding via `httpx.AsyncClient`, async ASGI handling, and nonblocking configuration file load.
4. Per-tenant hostname routing, disjoint backend pools and disjoint routing counters.

**Not a production-ready public edge proxy.** Do not put it on an untrusted network without authentication, TLS termination, rate limiting, operational health checks, observability, and rigorous HTTP protocol/security review. Hostname routing does **not** authenticate a tenant; a client can select a configured hostname by supplying its `Host` header. For genuine tenant authorization, enforce identity at a trusted authenticated gateway (or introduce a verified authentication mechanism) before this application.

## Architecture and ownership

```text
ASGI Request
  → validate unique Host and request size
  → Router (sole owner of tenant/group/endpoint selection)
      → Tenant (one host namespace)
          → BackendGroup (equal-weight group rotation)
              → Endpoint (round-robin within group)
  → one outbound HTTPX async forwarding path
  → bounded upstream response / stripped hop-by-hop headers
  → ASGI Response
```

`ProxyConfig` owns configuration invariants and prevents overlapping tenant hostnames. `Router` owns selection and tenant-specific counters. `create_app` owns request validation and network effects. `ConfiguredProxy` owns one-time asynchronous configuration loading. None of these layers duplicates Host orchestration, OneShot Build Admission, the existing Sandbox, or a second provider registry.

Connection-establishment failure can fall through to another configured backend. Once a request may have reached an upstream, failures are reported as `502`; no automatic replay of ambiguous operations. Upstream HTTP status codes, including 4xx/5xx, are forwarded as responses and do not trigger automatic failover.

## Run locally

From the **repository root** with the existing `mvp` and dev dependency groups installed:

```sh
uv sync --locked --extra mvp
PROXY_CONFIG=examples/reverse_proxy/config.example.json \
  uv run --no-sync uvicorn examples.reverse_proxy.app:app --host 127.0.0.1 --port 8080
```

The supplied configuration points to demonstration backends on `127.0.0.1:9101`, `9102`, `9103`, and `9201`. Start your own HTTP services on those ports first, or edit a private copy of the configuration. To test routing, send `Host: alpha.localhost` or `Host: beta.localhost`. No backend address is accepted from a request header or query string.

The example is a source-checkout-only module (`examples/` is not included in OneShot's wheel), and it does not install or start any backend services.

## Verify

```sh
uv run --no-sync pytest -q tests/proxy
uv run --no-sync python -m compileall -q examples/reverse_proxy tests/proxy
```

The focused suite includes a loopback ASGI-to-HTTP-socket integration test and does **not** require `pytest-asyncio`. The connected test uses a local ephemeral server only. No Modal, hosted inference, remote repository mutation, or production networking is performed by the tests.

## Deliberate limitations

- HTTP/1.1 via ASGI/HTTPX; no WebSocket, CONNECT, HTTP/2 or gRPC proxying.
- In-memory, bounded requests (1 MiB) and responses (4 MiB). This example is not a streaming, unbounded-content proxy.
- Equal-weight round-robin per group and endpoint; no passive/active health scoring, sticky sessions or distributed counters. Multiple worker processes each hold separate counters.
- Simple hostname lookup; no tenant login/authorization. Forwarded headers are rewritten to avoid trusting the caller's claims.
- Only operator-configured HTTP(S) backend origins; no dynamic upstream registration, service discovery or forwarding to client-selected URLs.
- No TLS termination, rate-limiting, abuse controls, audit telemetry, retries after ambiguous effects, or automatic deployment.
- No claim that root repository CI or hosted E2E passed. See [DESIGN_REVIEW.md](DESIGN_REVIEW.md) for the recorded evaluation and verification evidence.
