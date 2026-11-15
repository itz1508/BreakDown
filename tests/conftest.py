"""Pytest configuration — ensures the repo-root packages (agents, system) stay importable."""

import sys
from pathlib import Path

# Add project root to path (relocated from the ledger-retired root conftest.py).
root = Path(__file__).parent.parent
if str(root) not in sys.path:
    sys.path.insert(0, str(root))
