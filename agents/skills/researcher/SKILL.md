# Researcher â€” sourced evidence investigation

**Mini-pipeline:** `research.yaml` declares the `review`, `retrieve` and `main`
segments. Every step stays `status: unbound` because execution is Host-dispatched,
never self-started.

**Entry points.**

- `research.py` / `__main__.py`: fail-closed CLI that reports the registered
  dispatch route and exits 2.
- `researching.run(context, envelope, arguments)`: the Host-dispatched operation.
  If a `ResearchExecutionService` is injected it delegates to it; otherwise it runs
  the bounded search below.
- `researching.search(...)`: bounded model/tool loop over the tools that exist here.

**Tools available today, both read-only.**

- `search_repository(terms, scope, max_results)` â†’ `agent.skills.spec_search`
  (literal matching, ranked, digest-bound snippets).
- `read_source(path, start_line, max_lines)` â†’ `agent.skills.auditor.tools.core.safe_read_bytes`
  (repository-root and symlink checked, byte-bounded).

**Not available from this package:** web search, web fetch, browser automation,
sandboxed code execution and any MCP server. None of them is simulated. A question
that needs them produces an explicit limitation, not a fabricated result, and
repository lookup is never described as web research.

**Result states.** `completed`, `truncated` (`finish_reason=length`), `pending`
(step limit with tools still requested), `exhausted` (tool-call limit), `failed`
(provider unavailable or unusable answer). An empty search is a tool status, never
a success.

**Artifacts (existing models, existing store).** `research-audit:*` and
`research-code:*` are `research_record` artifacts; `research-fixture:*` is a
`fixture_specification` and is produced only when evidence exists. Each returned
reference carries the digest of the stored bytes, and identical evidence yields an
identical artifact identity.

**Boundary.** No stage transitions, approvals, trusted receipts, source writes or
web claims. A model statement without a digest observed by a tool call is recorded
as an unknown, never as evidence. Rules of conduct come from `AGENTS.md` and are
not restated here.

