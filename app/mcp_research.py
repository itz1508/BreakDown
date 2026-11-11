"""Minimal stub for MCP research integration."""
from dataclasses import dataclass

@dataclass
class ResearchMCPOutput:
    artifact_id: str = ""
    summary: str = ""
    sources: list = None

def mcp_transport_config() -> dict:
    return {"transport": "stub"}

def research_artifact_id(*args, **kwargs) -> str:
    return ""
