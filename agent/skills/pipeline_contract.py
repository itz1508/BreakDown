"""Read-only validation of Agent-side pipeline definitions.

This module compiles descriptions, not executable tasks. It does not register
tools, perform operations, change Host transitions, or grant effects.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Literal, Mapping

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator


class DefinitionError(ValueError):
    """The declarative Agent process graph is incomplete or invalid."""


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class PipelineStep(_Strict):
    id: str = Field(pattern=r"^[a-z][a-z0-9_]*$")
    depends_on: tuple[str, ...] = ()
    operation_id: str = Field(pattern=r"^[a-z][a-z0-9_]*\.[a-z][a-z0-9_]*$")
    status: Literal["unbound"] = "unbound"
    subpipeline_ref: str | None = None


class PipelineSegment(_Strict):
    id: str = Field(pattern=r"^[a-z][a-z0-9_]*$")
    steps: tuple[PipelineStep, ...] = Field(min_length=1)


class SkillPipeline(_Strict):
    kind: Literal["skill_mini_pipeline"]
    definition_version: Literal[1]
    pipeline_id: str = Field(pattern=r"^[a-z][a-z0-9_]*\.[a-z][a-z0-9_]*$")
    owner: str = Field(pattern=r"^[a-z][a-z0-9_]*$")
    artifact_contract_refs: tuple[str, ...] = Field(min_length=1)
    segments: tuple[PipelineSegment, ...] = Field(min_length=1)
    policy: dict[str, bool | str] = Field(default_factory=dict)
    limits: dict[str, int] = Field(default_factory=dict)
    public_api_intent: str | None = None
    implementation_intent: str | None = None
    process_only: bool = False

    @model_validator(mode="after")
    def validate_ids(self) -> "SkillPipeline":
        if not self.pipeline_id.startswith(f"{self.owner}."):
            raise ValueError("pipeline_id must be namespaced to owner")
        if len(set(self.artifact_contract_refs)) != len(self.artifact_contract_refs):
            raise ValueError("duplicate artifact contract reference")
        _unique_ids([segment.id for segment in self.segments], "segment")
        for segment in self.segments:
            _unique_ids([step.id for step in segment.steps], f"{self.pipeline_id}#{segment.id} step")
            _validate_dag({step.id: step.depends_on for step in segment.steps}, f"{self.pipeline_id}#{segment.id}")
        if any(isinstance(v, bool) or v <= 0 for v in self.limits.values()):
            raise ValueError("limits must be positive integers")
        return self


class RootStep(_Strict):
    id: str = Field(pattern=r"^[a-z][a-z0-9_]*$")
    depends_on: tuple[str, ...] = ()
    pipeline_ref: str


class AgentProcessGraph(_Strict):
    kind: Literal["agent_process_graph"]
    definition_version: Literal[1]
    graph_id: str = Field(pattern=r"^[a-z][a-z0-9_]*\.[a-z][a-z0-9_]*$")
    activation: Literal["inactive"]
    steps: tuple[RootStep, ...] = Field(min_length=1)
    external_boundaries: dict[str, str] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_dependencies(self) -> "AgentProcessGraph":
        _unique_ids([step.id for step in self.steps], f"{self.graph_id} step")
        _validate_dag({step.id: step.depends_on for step in self.steps}, self.graph_id)
        return self


def _unique_ids(ids: list[str], label: str) -> None:
    if len(set(ids)) != len(ids):
        raise ValueError(f"duplicate {label} ID")


def _validate_dag(dependencies: Mapping[str, tuple[str, ...]], label: str) -> None:
    ids = list(dependencies)
    _unique_ids(ids, f"{label} step")
    for step_id, deps in dependencies.items():
        if len(set(deps)) != len(deps):
            raise ValueError(f"{label}: repeated dependency of {step_id}")
        if any(dep not in dependencies for dep in deps):
            raise ValueError(f"{label}: unknown dependency of {step_id}")
    color: dict[str, int] = {}

    def visit(node: str) -> None:
        if color.get(node) == 1:
            raise ValueError(f"{label}: cycle involving {node}")
        if color.get(node) == 2:
            return
        color[node] = 1
        for dep in dependencies[node]:
            visit(dep)
        color[node] = 2

    for step_id in ids:
        visit(step_id)


class _NoDuplicateKeys(yaml.SafeLoader):
    """Reject YAML duplicate keys instead of silently overriding policy."""

    def construct_mapping(self, node: yaml.MappingNode, deep: bool = False) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=deep)
            if not isinstance(key, str):
                raise DefinitionError("YAML keys must be strings")
            if key in result:
                raise DefinitionError(f"duplicate YAML key: {key}")
            result[key] = self.construct_object(value_node, deep=deep)
        return result


def _load_yaml(path: Path) -> object:
    if path.stat().st_size > 256 * 1024:
        raise DefinitionError(f"YAML definition exceeds size limit: {path}")
    try:
        return yaml.load(path.read_text(encoding="utf-8"), Loader=_NoDuplicateKeys)
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        raise DefinitionError(f"cannot load YAML definition: {path}") from exc


def _resolve_relative(root: Path, relative: str) -> Path:
    if not isinstance(relative, str) or not relative or "\\" in relative:
        raise DefinitionError("reference must be a nonempty POSIX-relative path")
    posix = PurePosixPath(relative)
    if posix.is_absolute() or any(part in {".", ".."} for part in relative.split("/")):
        raise DefinitionError(f"disallowed reference: {relative}")
    candidate = root / relative
    current = root
    for part in posix.parts:
        current = current / part
        if current.is_symlink():
            raise DefinitionError(f"symlink reference not permitted: {relative}")
    if not candidate.is_file() or not candidate.resolve().is_relative_to(root.resolve()):
        raise DefinitionError(f"missing or escaping reference: {relative}")
    return candidate


def _split_ref(ref: str) -> tuple[str, str]:
    if not isinstance(ref, str) or ref.count("#") != 1:
        raise DefinitionError(f"expected path#segment reference: {ref!r}")
    path, fragment = ref.split("#")
    if not re.fullmatch(r"[a-z][a-z0-9_]*", fragment):
        raise DefinitionError(f"invalid segment ID: {fragment}")
    return path, fragment


@dataclass(frozen=True)
class CompiledDefinitions:
    """Validated references only; no execution authority or approved operations."""

    root: AgentProcessGraph
    role_pipelines: Mapping[str, SkillPipeline]
    referenced_operations: frozenset[str]
    registered_operations: frozenset[str]

    @property
    def activation_ready(self) -> bool:
        return False


def compile_definitions(
    repository_root: str | Path,
    *,
    trusted_operation_ids: frozenset[str] | None = None,
    require_registered: bool = False,
) -> CompiledDefinitions:
    """Validate inactive graph, role DAGs and contract paths without execution."""
    root = Path(repository_root).resolve(strict=True)
    graph = AgentProcessGraph.model_validate(_load_yaml(_resolve_relative(root, "agent/breakdown.yaml")))
    pipelines: dict[str, SkillPipeline] = {}
    operations: set[str] = set()
    seen_segments: set[tuple[str, str]] = set()

    def inspect(reference: str, stack: tuple[tuple[str, str], ...] = ()) -> None:
        path, segment_id = _split_ref(reference)
        if not path.startswith("agent/skills/") or not path.endswith(".yaml"):
            raise DefinitionError(f"pipeline must be an Agent skill YAML: {path}")
        identity = (path, segment_id)
        if identity in stack:
            raise DefinitionError(f"recursive subpipeline reference: {reference}")
        loaded = pipelines.get(path)
        if loaded is None:
            loaded = SkillPipeline.model_validate(_load_yaml(_resolve_relative(root, path)))
            if not path.startswith(f"agent/skills/{loaded.owner}/"):
                raise DefinitionError(f"pipeline owner/path mismatch: {path}")
            for artifact_path in loaded.artifact_contract_refs:
                if not artifact_path.startswith("contracts/workflow/") or not artifact_path.endswith(".py"):
                    raise DefinitionError(f"invalid artifact contract path: {artifact_path}")
                _resolve_relative(root, artifact_path)
            if loaded.implementation_intent is not None:
                if not loaded.implementation_intent.startswith("agent/skills/"):
                    raise DefinitionError("implementation intent must be under agent/skills")
                _resolve_relative(root, loaded.implementation_intent)
            pipelines[path] = loaded
        segment = next((part for part in loaded.segments if part.id == segment_id), None)
        if segment is None:
            raise DefinitionError(f"unknown pipeline segment: {reference}")
        if identity in seen_segments:
            return
        for step in segment.steps:
            operations.add(step.operation_id)
            if step.subpipeline_ref is not None:
                inspect(step.subpipeline_ref, (*stack, identity))
        seen_segments.add(identity)

    for step in graph.steps:
        inspect(step.pipeline_ref)
    registered = trusted_operation_ids if trusted_operation_ids is not None else frozenset()
    if require_registered:
        missing = operations - registered
        if missing:
            raise DefinitionError("unregistered pipeline operation IDs: " + ", ".join(sorted(missing)))
    return CompiledDefinitions(
        root=graph,
        role_pipelines=pipelines,
        referenced_operations=frozenset(operations),
        registered_operations=frozenset(registered & operations),
    )
