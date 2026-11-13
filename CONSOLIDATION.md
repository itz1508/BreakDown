# BreakDown consolidation baseline

Source checkpoint: BreakDown staging `ff800aff580e55b9159238f767215295fb177aa8`.
Reviewed skill draft: PR #2 `f9178e9d2d354051e834367582169b058a378ecc`.
MVP source: OneShot-Continuing `dbecd79e58b5b43592009d3cc914fcdc2722413b`.

The baseline preserves the existing Host and Storage contracts, replaces obsolete role
paths with reviewed role implementations, and restores the Continuing HTTP/MCP
package with imports pointed at the single BreakDown Host. The source package
contains `agent`, `contracts`, `system`, `api_fundamentals`, and `mvp`.

No standalone `executor` role or `oneshot_sandbox` package is imported. The
legacy Host effect module remains temporarily because the approved Builder
still requires its authorization, checkpoint and receipt controls. Removal
requires an end-to-end equivalent rather than deleting those guards.

A commit is a consolidation candidate, not evidence that all tests passed.
The Consolidated package gate checks Python 3.11 and 3.12, dependency lock,
imports, E2E tests, static checks and actual wheel resources.
