"""MCP mock handshake against aimock (verified sequence per ai-mock-testing skill).

Proves the agentic-surface mocking story: JSON-RPC initialize →
notifications/initialized → tools/list → tools/call, all offline.
"""

import json
from typing import Any

import httpx


def _parse_response(resp: httpx.Response) -> dict[str, Any]:
    text = resp.text
    if "application/json" in resp.headers.get("content-type", ""):
        return resp.json()
    for line in text.splitlines():
        if line.startswith("data:"):
            return json.loads(line[5:].strip())
    return {}


def _rpc(
    port: int, payload: dict[str, Any], extra_headers: dict[str, str] | None = None
) -> httpx.Response:
    headers = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}
    if extra_headers:
        headers.update(extra_headers)
    return httpx.post(f"http://127.0.0.1:{port}/mcp", json=payload, headers=headers, timeout=10.0)


def test_mcp_initialize_and_tools(aimock_port: int) -> None:
    resp = _rpc(
        aimock_port,
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-03-26",
                "capabilities": {},
                "clientInfo": {"name": "triage-test", "version": "0.1"},
            },
        },
    )
    assert resp.status_code == 200, resp.text
    session_id = resp.headers.get("Mcp-Session-Id")
    assert session_id, "server must issue an Mcp-Session-Id"

    resp = _rpc(
        aimock_port,
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
        extra_headers={"mcp-session-id": session_id},
    )
    assert resp.status_code in (200, 202), resp.text

    resp = _rpc(
        aimock_port,
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
        extra_headers={"mcp-session-id": session_id},
    )
    data = _parse_response(resp)
    tool_names = [t["name"] for t in data.get("result", {}).get("tools", [])]
    assert "get_runbook_notes" in tool_names

    resp = _rpc(
        aimock_port,
        {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {"name": "get_runbook_notes", "arguments": {"document_id": "rb-1"}},
        },
        extra_headers={"mcp-session-id": session_id},
    )
    data = _parse_response(resp)
    result = data.get("result", {})
    assert result.get("isError") in (None, False)
    assert "mocked" in json.dumps(result)
