# Spec Search — bounded, read-only evidence retrieval

**What it is.** A query-driven retrieval capability for Research and Planning. Given a
repository root, a relative scope, literal terms and a budget, it returns ranked
snippets with line numbers and content digests. It reaches declared symbols
(`class`/`def`), configuration keys and prose references through one deterministic
lexical strategy.

**Boundary.** Read-only. It does not call a model, choose a design, write source,
dispatch a stage, or issue receipts. It has no `Stage` and no `SkillDispatch`
route; `agent/breakdown.yaml` records it under `unrouted_capabilities`. Rules of
conduct come from `AGENTS.md`; they are not restated here.

**Why it exists.** Research and Planning need source-grounded citations, not a
whole-repository dump. The module returns the smallest window that carries the
match plus a digest the host can reconcile later.

**Ranking (deterministic, no clock and no randomness).** Whole-word match (3) >
exact substring (2) > case-insensitive substring (1), plus 1 when the match line
declares the term. Ties break on the number of distinct terms in the file, then
path, then line.

**Budgets are explicit.** `max_files` and `max_results` set `truncated` and
`truncated_reason` (`file_budget`, `result_budget`). Files over
`max_file_bytes` and files that are not valid UTF-8 are reported in `skipped`
with `size` or `decode_error`; nothing is dropped silently.

**Entry points.**

```
python -m agent.skills.spec_search --root . --term TokenBucket --scope agent
python -m agent.skills.spec_search --root . --term "rate limit" --suffix .md
```

Programmatic callers use `agent.skills.spec_search.search(root, SpecQuery(...))`.

**Limitations.** Matching is lexical: synonyms, stemming and semantic similarity
are out of scope, and the benchmark measures exactly that rather than claiming
more. The capability reports what it found; it does not decide whether the
evidence is sufficient.
