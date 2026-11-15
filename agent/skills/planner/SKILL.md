# Planner Skill

## Purpose
Plan and scan repository structures to produce gap analyses, completeness checks, and wiring verification.

## Entry Point
```bash
uv run --no-sync python -m agent.skills.planner.run <repository-root>
```

## Tools
- `scan_candidate` - Initial capability scanning
- `analyze_gap` - Gap analysis between planned and actual state
- `scan_completeness` - Check specification completeness
- `scan_contracts` - Contract compliance scanning
- `scan_dependencies` - Dependency mapping
- `scan_frontend` - Frontend API route pattern inspection
- `scan_integration` - Integration path verification
- `scan_recovery` - Recovery procedure scanning
- `scan_verification` - Verification and validation
- `scan_wiring` - Component wiring analysis

## Output
- Scan results with disposition status
- Gap analysis summaries
- Wiring and integration reports
# Planner Skill

## Ownership
Code review, design, refactoring plans, Scanner capability execution,
gap resolution, and fixture definitions.

## Responsibilities
- Code review and design of BuildSpecification candidates
- Scanner execution (Scanner is a Planner capability)
- Gap resolution and fixture definitions
- Produce PlanningRecord artifacts for host review

## Tools
| Tool | Inputs | Outputs |
|------|--------|---------|
| `scanner_engine` | candidate artifact, specification | `ScannerResult` with findings |
| `completeness` | repository root, scope | `Finding` tuples |
| `contract_scanner` | repository root, scope | `Finding` tuples |
| `dependencies` | repository root, scope | `Finding` tuples |
| `frontend_api` | repository root, scope | `Finding` tuples |
| `integration` | repository root, scope | `Finding` tuples |
| `recovery` | repository root, scope | `Finding` tuples |
| `verification` | repository root, scope | `Finding` tuples |
| `wiring` | repository root, scope | `Finding` tuples |
| `gap_analysis` | structural gap request | `StructuralGapResult` |

## Runtime Integration
- Reports output through `HostDispatchResult` with `planning_record` or `build_specification` contract
- Never issues trusted receipts
- Never authorizes Build operations
- Host freezes specifications and issues Build admission

## Constraints
- Cannot issue trusted receipts
- Cannot authorize Build operations
- Cannot advance workflow stages
- Scanner output is reported to host, not self-verified