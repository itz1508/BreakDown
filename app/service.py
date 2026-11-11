"""Minimal stub for MVP service integration."""
from dataclasses import dataclass, field
from typing import Any

class MVPError(Exception):
    """MVP service error."""
    pass

@dataclass
class MVPService:
    """MVP service facade — stub for module loading."""
    host: Any = None
    config: Any = None

    def __post_init__(self):
        pass
