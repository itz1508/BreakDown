"""Tests for the shared agents/tools package."""

from __future__ import annotations

import pytest

from agents.tools import (
    CodeExecutionServerTool,
    ThinkTool,
    Tool,
    WebSearchServerTool,
    manifest,
)


class TestToolBase:
    def test_to_dict_is_anthropic_format(self) -> None:
        tool = Tool(name="t", description="d", input_schema={"type": "object", "properties": {}})
        assert tool.to_dict() == {"name": "t", "description": "d", "input_schema": {"type": "object", "properties": {}}}

    def test_to_openai_dict_wraps_in_function(self) -> None:
        tool = Tool(name="t", description="d", input_schema={"type": "object"})
        wrapped = tool.to_openai_dict()
        assert wrapped["type"] == "function"
        assert wrapped["function"]["name"] == "t"
        assert wrapped["function"]["parameters"] == {"type": "object"}

    def test_base_execute_is_abstract(self) -> None:
        with pytest.raises(NotImplementedError):
            Tool(name="t", description="d", input_schema={}).execute()


class TestThinkTool:
    def test_returns_acknowledgment_without_effects(self) -> None:
        assert ThinkTool().execute(thought="plan the search") == "Thinking complete!"

    def test_manifest_includes_think_for_dispatched_stages(self) -> None:
        stage_tools = manifest(root=".")
        assert stage_tools["discovery"]
        assert any(t["function"]["name"] == "think" for t in stage_tools["planning"])
        assert "user_request" not in stage_tools
        assert "user_review_and_approval" not in stage_tools


class TestServerTools:
    def test_web_search_declaration(self) -> None:
        declared = WebSearchServerTool(max_uses=2, allowed_domains=["docs.python.org"]).to_dict()
        assert declared == {
            "type": "web_search_20250305",
            "name": "web_search",
            "max_uses": 2,
            "allowed_domains": ["docs.python.org"],
        }

    def test_code_execution_declaration(self) -> None:
        assert CodeExecutionServerTool().to_dict() == {"type": "code_execution_20250522", "name": "code_execution"}
