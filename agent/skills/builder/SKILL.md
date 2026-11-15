# Builder Skill

## Purpose
Execute build processes and verify effect compliance for repository changes.

## Entry Point
```bash
uv run --no-sync python -m agent.skills.builder.run <repository-root>
```

## Tools
- `build_execution` - Execute build builds and track revisions
- `effect_verification` - Verify effect compliance and validity

## Output
- Build execution results with stage revisions
- Effect verification status (valid/not_valid)
- Build validation issue reports
# Builder Skill

## Ownership
Execute admitted Build actions, report effects and execution evidence.

## Responsibilities
- Execute Build actions admitted by the Runtime host
- Report effect observations with pre/post image digests
- Never issue trusted receipts or authorize its own operations
- Never bypass Build admission

## Tools
| Tool | Inputs | Outputs |
|------|--------|---------|
| `build_execution` | admitted BuildAction, admission receipt | `BuildActionExecution` with effect observations |
| `effect_verification` | pre/post digests, artifact refs | Verification status and reconciled effects |

## Runtime Integration
- Reports output through `HostDispatchResult` with `build_record` contract
- Never issues trusted receipts
- Never authorizes operations
- Host validates admission and executes effects through EffectExecutor

## Constraints
- Cannot issue trusted receipts
- Cannot authorize Build operations
- Cannot advance workflow stages
- Cannot execute actions without a valid admission receipt