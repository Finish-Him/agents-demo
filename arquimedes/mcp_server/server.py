"""MCP server that re-exposes Arquimedes' LangChain tools over the
Model Context Protocol.

The same ``@tool``-decorated Python functions power two surfaces:

- LangGraph agent (``arquimedes.agent.graph`` -> ``ToolNode(all_tools)``)
- MCP server (this module)

Since both surfaces introspect the Pydantic ``args_schema`` attached by
``langchain_core.tools.tool``, the JSON schemas exposed to MCP clients
are guaranteed to stay in lock-step with what the agent itself sees.

Transports:
- stdio (default): ``python -m arquimedes.mcp_server``
- SSE:    ``python -m arquimedes.mcp_server --sse --port 8765``
"""

from __future__ import annotations

import asyncio
import json
import logging
import sys
from typing import Any

import mcp.types as types
from mcp.server import Server

from arquimedes.tools import all_tools


logger = logging.getLogger("arquimedes.mcp")


# ── Tool introspection ────────────────────────────────────────────────
def _tool_input_schema(lc_tool) -> dict[str, Any]:
    """Return a JSON schema for the LangChain tool's input arguments."""
    schema_cls = getattr(lc_tool, "args_schema", None)
    if schema_cls is None:
        return {"type": "object", "properties": {}}
    try:
        # Pydantic v2
        return schema_cls.model_json_schema()
    except AttributeError:  # pragma: no cover
        # Pydantic v1 fallback
        return schema_cls.schema()


def _as_mcp_tool(lc_tool) -> types.Tool:
    return types.Tool(
        name=lc_tool.name,
        description=(lc_tool.description or "").strip(),
        inputSchema=_tool_input_schema(lc_tool),
    )


# ── Server factory ────────────────────────────────────────────────────
def build_server() -> Server:
    server: Server = Server(
        name="arquimedes",
        version="1.0.0",
        instructions=(
            "Math-for-ML tutoring tools: level assessment, exercise generation, "
            "concept explanation, textbook RAG lookup, symbolic math (SymPy), "
            "function plotting, step-by-step derivation, fine-tuned math solver."
        ),
    )

    tools_by_name = {t.name: t for t in all_tools}

    @server.list_tools()
    async def list_tools() -> list[types.Tool]:
        return [_as_mcp_tool(t) for t in all_tools]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict[str, Any]) -> list[types.ContentBlock]:
        lc_tool = tools_by_name.get(name)
        if lc_tool is None:
            raise ValueError(f"unknown tool: {name!r}")

        # LangChain tools are sync — run them in a thread so we don't block
        # the MCP event loop.
        result = await asyncio.to_thread(lc_tool.invoke, arguments or {})

        # Always return a single TextContent; MCP clients render it as
        # Markdown. Base64-image data URIs embedded in the text survive
        # because clients do their own Markdown rendering.
        if not isinstance(result, str):
            result = json.dumps(result, ensure_ascii=False)
        return [types.TextContent(type="text", text=result)]

    return server


# ── Entrypoints ───────────────────────────────────────────────────────
async def run_stdio() -> None:
    from mcp.server.stdio import stdio_server

    server = build_server()
    async with stdio_server() as (read, write):
        await server.run(read, write, server.create_initialization_options())


async def run_sse(host: str, port: int) -> None:  # pragma: no cover
    """SSE transport — lets the MCP server run over HTTP for multi-client demos."""
    from mcp.server.sse import SseServerTransport
    import uvicorn
    from starlette.applications import Starlette
    from starlette.routing import Mount, Route

    server = build_server()
    sse = SseServerTransport("/messages/")

    async def handle_sse(request):  # type: ignore[no-untyped-def]
        async with sse.connect_sse(request.scope, request.receive, request._send) as (r, w):
            await server.run(r, w, server.create_initialization_options())

    app = Starlette(
        routes=[
            Route("/sse", endpoint=handle_sse),
            Mount("/messages/", app=sse.handle_post_message),
        ]
    )
    config = uvicorn.Config(app, host=host, port=port, log_level="info")
    await uvicorn.Server(config).serve()


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(prog="arquimedes-mcp")
    parser.add_argument("--sse", action="store_true", help="Serve over HTTP/SSE instead of stdio.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()

    # Log to stderr only — MCP clients parse stdout as JSON-RPC frames.
    logging.basicConfig(level=logging.INFO, stream=sys.stderr)

    if args.sse:
        asyncio.run(run_sse(args.host, args.port))
    else:
        asyncio.run(run_stdio())


if __name__ == "__main__":  # pragma: no cover
    main()
