"""Thin FortyGuard MCP client (Streamable HTTP). The key comes from the FORTYGUARD_API_KEY env var
and is never logged or written to output files."""
from __future__ import annotations

import asyncio
import json
import os

import httpx2
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client
from mcp.shared._httpx_utils import create_mcp_http_client

MCP_URL = os.environ.get("FORTYGUARD_MCP_URL", "https://tos-mcp.app.fortyguard.com/mcp")
ROUTE_PRICE = 3500  # stated in the temperature_routing tool description


def api_key() -> str:
    k = os.environ.get("FORTYGUARD_API_KEY", "").strip()
    if not k:
        raise SystemExit("Set FORTYGUARD_API_KEY (see .env.example).")
    return k


class FortyGuard:
    def __init__(self, session: ClientSession):
        self.s = session

    async def call(self, tool: str, args: dict) -> dict:
        res = await self.s.call_tool(tool, args)
        sc = res.structured_content
        if sc is None:  # fall back to the JSON text block
            sc = json.loads(res.content[0].text)  # type: ignore[union-attr]
        if res.is_error or (isinstance(sc, dict) and sc.get("ok") is False):
            raise RuntimeError(f"{tool} failed: {json.dumps(sc)[:500]}")
        return sc

    async def balance(self) -> int:
        sc = await self.call("credit_balance", {})
        return int(sc.get("available_credits", sc.get("result", {}).get("value", {}).get("available_credits", -1)))

    async def submit_route(self, origin, dest, departure: str) -> str:
        sc = await self.call("temperature_routing", {
            "origin": {"lat": origin[0], "lon": origin[1]},
            "destination": {"lat": dest[0], "lon": dest[1]},
            "departure_time": departure})
        return sc["result"]["activity_id"]

    async def read_route(self, activity_id: str, timeout_s: int = 300) -> dict:
        waited = 0
        while True:
            sc = await self.call("temperature_routing_read", {"activity_id": activity_id})
            value = sc["result"]["value"]
            if value.get("status") == "completed":
                return value
            if value.get("status") == "failed" or waited >= timeout_s:
                raise RuntimeError(f"route {activity_id} status={value.get('status')}")
            await asyncio.sleep(10)
            waited += 10


def connect():
    """Async context manager yielding a FortyGuard client."""
    headers = {"Authorization": f"Bearer {api_key()}"}
    http = create_mcp_http_client(headers=headers, timeout=httpx2.Timeout(60, read=300))

    class _Ctx:
        async def __aenter__(self):
            await http.__aenter__()
            self._t = streamable_http_client(MCP_URL, http_client=http)
            r, w = await self._t.__aenter__()
            self._s = ClientSession(r, w)
            await self._s.__aenter__()
            await self._s.initialize()
            return FortyGuard(self._s)

        async def __aexit__(self, *exc):
            await self._s.__aexit__(*exc)
            await self._t.__aexit__(*exc)
            await http.__aexit__(*exc)

    return _Ctx()
