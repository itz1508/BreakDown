"""Tests for the shared agents/tools package."""

from __future__ import annotations

import pytest

from agents.tools import (
    ServerTool,
    ThinkTool,
    Tool,
    manifest,
)


class TestToolBase:
    def test_declaration_is_provider_neutral(self) -> None:
        tool = Tool(name="t", description="d", input_schema={"type": "object", "properties": {}})
        assert tool.declaration() == {
            "name": "t",
            "description": "d",
            "input_schema": {"type": "object", "properties": {}},
        }

    def test_declaration_carries_no_provider_wire_keys(self) -> None:
        wrapped = Tool(name="t", description="d", input_schema={}).declaration()
        assert "type" not in wrapped
        assert "function" not in wrapped

    def test_base_execute_is_abstract(self) -> None:
        with pytest.raises(NotImplementedError):
            Tool(name="t", description="d", input_schema={}).execute()


class TestThinkTool:
    def test_returns_the_thought_without_effects(self) -> None:
        assert ThinkTool().execute(thought="plan the search") == "plan the search"

    def test_manifest_includes_think_for_dispatched_stages(self) -> None:
        stage_tools = manifest(root=".")
        assert stage_tools["discovery"]
        assert any(t["name"] == "think" for t in stage_tools["planning"])
        assert "user_request" not in stage_tools
        assert "user_review_and_approval" not in stage_tools


class TestServerTool:
    def test_declaration_is_capability_plus_options(self) -> None:
        declared = ServerTool(capability="web_search", options={"max_uses": 2}).declaration()
        assert declared == {"server_tool": "web_search", "max_uses": 2}

    def test_declaration_hardcodes_no_provider_type_strings(self) -> None:
        declared = ServerTool(capability="code_execution").declaration()
        assert "2025" not in str(declared)
        assert "type" not in declared
