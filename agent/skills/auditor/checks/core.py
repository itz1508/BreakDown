"""Read-only, evidence-grounded audit capability runner; not a workflow controller."""

from __future__ import annotations

import hashlib
from collections.abc import Callable, Iterable
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class Finding:
    capability: str
    code: str
    status: str
    severity: str
    path: str
    line: int
    message: str
    evidence_digest: str


@dataclass(frozen=True)
class AuditResult:
    root: str
    scope: str
    requested_capabilities: tuple[str, ...]
    executed_capabilities: tuple[str, ...]
    findings: tuple[Finding, ...]
    limitations: tuple[str, ...]
    disposition: str
    request: str = ""

    def to_dict(self) -> dict[str, object]:
        data = asdict(self)
        findings = data["findings"]
        assert isinstance(findings, tuple)
        for finding in findings:
            identity = "|".join((finding["capability"], finding["path"], str(finding["line"]), finding["code"]))
            finding["finding_id"] = "AUD-" + hashlib.sha256(identity.encode()).hexdigest()[:16]
        return data


def safe_read_bytes(root: Path, path: Path) -> bytes:
    """Reject out-of-root or symlinked audit sources before opening them."""
    root = root.resolve(strict=True)
    if not path.is_relative_to(root):
        raise ValueError("audit source escapes repository root")
    part_path = root
    for part in path.relative_to(root).parts:
        part_path = part_path / part
        if part_path.is_symlink():
            raise ValueError("audit source uses a symlink")
    resolved = path.resolve(strict=True)
    if not resolved.is_relative_to(root) or not resolved.is_file():
        raise ValueError("audit source is not a regular in-root file")
    return path.read_bytes()


def safe_read_text(root: Path, path: Path) -> str:
    return safe_read_bytes(root, path).decode("utf-8")


def evidence(
    root: Path,
    path: Path,
    line: int,
    code: str,
    capability: str,
    severity: str,
    message: str,
    status: str = "candidate",
) -> Finding:
    """Capture file digest so a later host can reconcile stale findings."""
    data = safe_read_bytes(root, path)
    return Finding(
        capability,
        code,
        status,
        severity,
        path.relative_to(root).as_posix(),
        line,
        message,
        hashlib.sha256(data).hexdigest(),
    )


def python_files(root: Path, scope: Path) -> Iterable[Path]:
    """Walk only ordinary files; never recurse through directory symlinks."""
    for path in sorted(scope.rglob("*.py")):
        if any(
            part in {".git", ".venv", "venv", "node_modules", "__pycache__", ".transfer-quarantine"}
            or part.startswith(".pytest-")
            for part in path.relative_to(root).parts
        ):
            continue
        if path.is_symlink():
            continue
        if path.is_file():
            if not path.resolve(strict=True).is_relative_to(root):
                raise ValueError("audit Python source escapes repository root")
            yield path


# Stable per-capability order; a requested subset cannot bypass this ordering.
# The Host retains ownership of cross-stage Audit Discovery checkpoints.
CAPABILITY_ORDER: tuple[str, ...] = (
    "paths",
    "contracts",
    "dependencies",
    "security",
    "completeness",
    "wiring",
    "frontend",
    "integration",
    "state",
    "recovery",
    "verification",
)


Scanner = Callable[[Path, Path], list[Finding]]


def scan(root: Path, scope: str = ".", capabilities: tuple[str, ...] = (), request: str = "") -> AuditResult:
    from agent.skills.auditor.checks.completeness import scan_completeness
    from agent.skills.auditor.checks.contracts import scan_contracts
    from agent.skills.auditor.checks.dependencies import scan_dependencies
    from agent.skills.auditor.checks.frontend import scan_frontend
    from agent.skills.auditor.checks.integration import scan_integration
    from agent.skills.auditor.checks.paths import scan_paths
    from agent.skills.auditor.checks.recovery import scan_recovery
    from agent.skills.auditor.checks.security import scan_security
    from agent.skills.auditor.checks.state import scan_state
    from agent.skills.auditor.checks.verification import scan_verification
    from agent.skills.auditor.checks.wiring import scan_wiring

    scanners: dict[str, Scanner] = {
        "paths": scan_paths,
        "contracts": scan_contracts,
        "dependencies": scan_dependencies,
        "security": scan_security,
        "completeness": scan_completeness,
        "wiring": scan_wiring,
        "frontend": scan_frontend,
        "integration": scan_integration,
        "state": scan_state,
        "recovery": scan_recovery,
        "verification": scan_verification,
    }
    if tuple(scanners) != CAPABILITY_ORDER:
        raise RuntimeError("audit capability registry/order mismatch")
    requested = tuple(dict.fromkeys(capabilities)) if capabilities else CAPABILITY_ORDER
    unknown = sorted(set(requested) - set(scanners))
    if unknown:
        raise ValueError(f"unknown audit capabilities: {', '.join(unknown)}")
    root = root.resolve(strict=True)
    if not root.is_dir():
        raise ValueError("repository root must be a directory")
    if Path(scope).is_absolute():
        raise ValueError("audit scope must be relative to repository root")
    target = (root / scope).resolve(strict=True)
    if not target.is_relative_to(root):
        raise ValueError("audit scope escapes repository root")
    if not target.is_dir():
        raise ValueError("audit scope must be a directory")
    findings: list[Finding] = []
    limitations = [
        "Static observations are not runtime or E2E verification.",
        "Only Python and literal frontend API route patterns are inspected; dynamic wiring requires runtime evidence.",
        "Symlink checks are not atomic source checkpoints; Host must verify source stability.",
    ]
    executed: list[str] = []
    for name in CAPABILITY_ORDER:
        if name not in requested:
            continue
        try:
            findings.extend(scanners[name](root, target))
            executed.append(name)
        except (OSError, UnicodeError, SyntaxError, ValueError) as exc:
            limitations.append(f"{name} not completed: {type(exc).__name__}")
    findings.sort(key=lambda f: (f.capability, f.path, f.line, f.code))
    if len(executed) != len(requested):
        disposition = "blocked"
    elif findings:
        disposition = "findings_open"
    else:
        disposition = "not_e2e_verified"
    return AuditResult(
        str(root),
        target.relative_to(root).as_posix(),
        requested,
        tuple(executed),
        tuple(findings),
        tuple(limitations),
        disposition,
        request,
    )
