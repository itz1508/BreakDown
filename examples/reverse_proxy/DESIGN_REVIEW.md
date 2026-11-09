# Reverse proxy design and execution record

Execution chronology uses America/Los_Angeles time. Records are additive; corrections retain preceding observations.

## 2026-11-09T02:40:00-08:00 — Repository audit and design scope

- Audited `itz1508/BreakDown` (`main` at `e3e33f3aa7c229015bf2f0186d29cb9ec1856ae1`). A recursive tree inspection found **no existing reverse-proxy implementation** to reuse or replace.
- The `draft` and `refactor/executor-sandbox-relocation-20261108` branches share an *Executor Sandbox relocation*, not a proxy implementation. `breakdown` and `itz1508/breakdown` share a different, unrelated history with no common ancestor with `main`. `master` is absent. These branches must not be discarded as proxy drafts.
- Scoped the proxy to `examples/reverse_proxy` and focused tests in `tests/proxy`. No existing OneShot contracts, Host runtime, or Sandbox dispatch have been modified. No parallel proxy framework is introduced.

## 2026-11-09T02:40:00-08:00 — Four cumulative design revisions

| Revision | Requirement | Evidence/check | Status |
| --- | --- | --- | --- |
| 01 | HTTP reverse proxy and load balancing | Backend response, round-robin selection | Implemented/tested |
| 02 | Backends become hierarchical | Group-first and backend-within-group selection; connection failover | Implemented/tested |
| 03 | Proxy I/O becomes async | ASGI/HTTPX operations; async config loading; concurrent requests | Implemented/tested |
| 04 | Whole proxy becomes multi-tenant | Host-to-tenant routing, isolated backend pools/counters, spoofed forwarded-header stripping | Implemented/tested |

## 2026-11-09T02:40:00-08:00 — Alternatives evaluated

The alternatives below are **architecture proposals**, not separately implemented or benchmarked variants. No remote branch or CI result is fabricated for them.

| Candidate | Requirements supported | Trade-off | Overlap and risk | Decision |
| --- | --- | --- | --- | --- |
| A. Flat, synchronous proxy | 01 | Small initial surface | Hierarchical routing and async conversion require widespread rewrites; synchronous I/O blocks concurrency | Reject for final scope |
| B. Add a new wrapper/dispatcher for each requirement change | 01–04 in principle | Stage-local edits | Repeated load-selection rules, duplicate tenant parsing, competing owners of dispatch | Reject |
| C. Typed hierarchical config + one Router + one async ASGI forwarding path | 01–04 | Stable interface, centralized routing decisions | Buffered payload limits and trusted tenant authentication remain production work | **Selected** |

C preserves a single owner for routing and forwarding without conflating distinct concerns. It reuses the project's existing Python/Pydantic/ASGI/HTTPX stack rather than creating a second general-purpose networking framework. A backend group is a routing domain object, not an additional execution/authorization agent.

## 2026-11-09T02:40:00-08:00 — Validation findings and corrections

- Initial tests found that Starlette's `Headers` exposes `.raw`, not HTTPX's `.multi_items()`. Corrected the boundary adapter rather than creating a second header parser.
- Initial hierarchical round-robin logic incorrectly incremented counters in unselected groups. Corrected counters to advance only on selected-group routing, preserving endpoint fairness.
- Prebuffered HTTPX mock responses may already be decoded; a stale `Content-Encoding` caused double decompression. Corrected the mock-consumed response handling while using raw response streaming for real backends.
- Added tests for redirect suppression, encoded paths, no retry after uncertain operations, size limits, duplicate Host headers, HEAD semantics, compressed content, and tenant/forwarded-header isolation.

## 2026-11-09T02:40:00-08:00 — Independent verification boundaries

- **23 focused tests passed** using `python -m pytest -p no:asyncio tests/proxy -q`, including a connected loopback ASGI-to-backend HTTP integration test.
- `python -m compileall -q examples tests/proxy` completed successfully.
- Executed under local Python 3.13; repository CI declares Python 3.11 and 3.12. Those version-specific tests, full root suite, Ruff, mypy, remote deployment, and production load tests have **not** been run here.
- Two Uvicorn/WebSockets dependency deprecation warnings appeared during the loopback test; these are separate from test assertion failures.
- Alternatives A and B were never stored as competing implementations. Only C is intended for publication. Do not delete unrelated remote branches or treat test output as a Host-issued Build Admission receipt.
