# Builder — preparation without new runtime authority

**Mini-pipeline:** `build.yaml#prepare` receives a candidate reference and
describes preparation of a handoff for external review. All its operation IDs
remain unbound and it cannot perform effects or grant approval.

**Python:** Existing `building.run(context, envelope, arguments)` remains the
Host-authorized executable path, unchanged by this Agent-side contract.

**Boundary:** No unapproved execution, independent verification, Host
receipt issuance, or expansion of approved scope.
