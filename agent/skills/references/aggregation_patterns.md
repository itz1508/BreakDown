# Aggregation patterns for evidence workflows

**Purpose:** Adapt data-processing ideas from MongoDB aggregation examples
without installing MongoDB, introducing a second search engine, or granting
execution authority.

| Pattern | Agent use | Constraint |
| --- | --- | --- |
| Compound search | Combine required concepts and related terminology | Relevance is not evidence |
| Match/filter | Restrict sources to accepted scope and version | Not authorization |
| Facet | Examine independent source questions | Not agent scheduling |
| Lookup | Associate findings, contracts, tests and references | Preserve provenance |
| Graph traversal | Expand callers, dependencies and linked evidence | Bound depth and records |
| Group | Consolidate duplicate findings | Preserve contradictions |
| Project | Return minimal evidence-linked outputs | Keep source identity |
| Sort/limit | Deterministic priority and resource bounds | Don't claim full coverage |
| Synthetic fixtures | Independent GOOD/BAD draft examples | Never imply observed success |

Researcher handles retrieval, Auditor examines evidence, Planner evaluates
dependencies and candidate gaps, and Fixturer creates unverified drafts.
Builder's new YAML is preparation-only.

References:
- https://www.practical-mongodb-aggregations.com/examples/full-text-search/compound-text-search.html
- https://www.practical-mongodb-aggregations.com/appendices/cheatsheet.html
- https://www.practical-mongodb-aggregations.com/appendices/cheatsheet-source.html

Do not copy `$merge`, `$out`, `$fill`, or `$densify` as trusted
read-only evidence operations. Host authorization and independent acceptance
remain external to these Agent definitions.
