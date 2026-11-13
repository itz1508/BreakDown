"""List tools from a Databricks AI Gateway MCP service (streamable HTTP).

Local adaptation of the Databricks notebook snippet. Verified against the
installed dependency set in the project `.venv`:

- mcp==2.3.0  -> `mcp.client.streamable_http.streamable_http_client` yields a
  2-tuple ``(read, write)`` (see mcp/client/_transport.py: TransportStreams).
- httpx2==2.16.0 -> mcp 2.3.0 is built on the httpx2/httpcore2 generation, so
  the custom ``http_client`` passed here must be an ``httpx2.AsyncClient``.

Prerequisites:
1. Databricks CLI installed (this machine: d:\\breakdown\\.tools\\databricks-cli,
   also added to the user PATH).
2. Log in once (opens a browser; run in a normal terminal):
       databricks auth login --host "https://dbc-0749ad06-5bc8.cloud.databricks.com" -p DEFAULT

Run with the project venv:
    d:\\breakdown\\.venv\\Scripts\\python.exe examples\\databricks_mcp_list_tools.py
"""

import asyncio
import json
import os
import shutil
import subprocess

import httpx2
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

DATABRICKS_HOST = "https://dbc-0749ad06-5bc8.cloud.databricks.com"
MCP_URL = f"{DATABRICKS_HOST}/ai-gateway/mcp-services/system.ai.github"
CLI_PROFILE = "DEFAULT"
# Local install location used when `databricks` is not on PATH yet.
CLI_FALLBACK = r"D:\breakdown\.tools\databricks-cli\databricks.exe"


def _databricks_exe() -> str:
    """Resolve the Databricks CLI executable."""
    found = shutil.which("databricks")
    return found if found else CLI_FALLBACK


def databricks_token() -> str:
    """Mint a short-lived OAuth token from the CLI profile."""
    try:
        out = subprocess.check_output(
            [
                _databricks_exe(),
                "auth",
                "token",
                "--host",
                DATABRICKS_HOST,
                "-p",
                CLI_PROFILE,
                "--output",
                "json",
            ],
            text=True,
            stderr=subprocess.PIPE,
        )
    except subprocess.CalledProcessError as exc:
        raise SystemExit(
            "Databricks CLI could not mint a token. Log in first (opens a browser, "
            "run in a normal terminal):\n"
            f"  databricks auth login --host {DATABRICKS_HOST} -p {CLI_PROFILE}\n"
            f"CLI error: {(exc.stderr or '').strip()}"
        ) from exc
    return json.loads(out)["access_token"]


async def main() -> None:
    token = os.environ.get("DATABRICKS_TOKEN") or databricks_token()
    http_client = httpx2.AsyncClient(headers={"Authorization": f"Bearer {token}"})
    async with http_client, streamable_http_client(
        MCP_URL, http_client=http_client
    ) as (read, write), ClientSession(read, write) as session:
        await session.initialize()
        result = await session.list_tools()
        for tool in result.tools:
            print(f"{tool.name}: {tool.description}")


if __name__ == "__main__":
    asyncio.run(main())
