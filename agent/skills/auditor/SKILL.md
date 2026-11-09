# Auditor Skill

## Purpose
Run read-only inspection tools against a repository to produce audit findings.

## Entry Point
```bash
uv run --no-sync python -m agent.skills.auditor.run <repository-root>
```

## Tools
- `scan_paths` - Scan for path-related patterns
- `scan_security` - Scan for security-related patterns  
- `scan_state` - Scan for state-related patterns

## Output
- Audit disposition: `not_e2e_verified`, `findings_open`, or `blocked`
- Executed capabilities list
- Finding tuples with capability, path, line, code, message, severity
# Auditor Skill

## Ownership
Read-only repository inspection, CodeIntent discovery, source-grounded diagnostic findings.

## Responsibilities
- Filesystem integrity: broken symlinks, repo containment (paths tool)
- Security-sensitive source pattern detection (security tool)
- Static host ownership and receipt-binding audits (state tool)

## Tools
| Tool | Inputs | Outputs |
|------|--------|---------|
| `paths` | repository root, scope | `Finding` tuples: PATH_OUTSIDE_REPOSITORY, BROKEN_SYMLINK |
| `security` | repository root, scope | `Finding` tuples: COMMAND_EXECUTION_REVIEW, SHELL_TRUE_REVIEW |
| `state` | repository root, scope | `Finding` tuples: RECEIPT_SUBJECT_UNBOUND |

## Runtime Integration
- Reports findings through `HostDispatchResult` with `audit_findings` contract
- Never issues trusted receipts
- Never authorizes operations
- Host validates and persists all output

## Constraints
- Read-only: no file writes, no subprocess execution, no network
- Cannot advance workflow stages
- Cannot modify artifacts or receipts