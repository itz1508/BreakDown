# Researcher Skill

## Purpose
Research and catalog frontend API patterns, component specifications, and integration references.

## Entry Point
```bash
uv run --no-sync python -m agent.skills.researcher.run <repository-root>
```

## Tools
- `research_catalog` - Catalog researched findings and evidence

## Output
- Catalog entries with evidence references and reliability status
- Research gap analysis summaries
# Researcher Skill

## Ownership
Research execution, sourced claims, evidence requests.

## Responsibilities
- Execute research tasks against configured MCP transports
- Produce sourced ResearchRecord artifacts with RFC 8785 digests
- Match research intents against synthetic catalog samples
- Never advance workflow stages or issue receipts

## Tools
| Tool | Inputs | Outputs |
|------|--------|---------|
| `research_catalog` | research intent, keywords | `CatalogMatch` with match status and conditions |

## Runtime Integration
- Reports results through `HostDispatchResult` with `research_record` contract
- Never issues trusted receipts
- Never authorizes operations
- Host validates artifacts and advances workflow stages

## Constraints
- Cannot advance workflow stages
- Cannot issue trusted receipts
- Cannot modify artifacts or receipts owned by the host