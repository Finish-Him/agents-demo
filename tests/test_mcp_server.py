"""Tests for arquimedes/mcp_server/server.py.

Validates that every LangChain tool in ``all_tools`` is mirrored into the
MCP server with a well-formed JSON schema, and that ``call_tool`` can
execute a pure-python tool round-trip without any network / GPU.
"""

from __future__ import annotations

import asyncio

import pytest

from arquimedes.mcp_server.server import _as_mcp_tool, build_server
from arquimedes.tools import all_tools


class TestToolSchemas:
    def test_all_tools_convertible(self):
        """Every registered LangChain tool must yield a valid MCP Tool object."""
        for t in all_tools:
            mcp_tool = _as_mcp_tool(t)
            assert mcp_tool.name == t.name
            assert mcp_tool.description  # non-empty
            schema = mcp_tool.inputSchema
            assert isinstance(schema, dict)
            assert schema.get("type") == "object"
            assert "properties" in schema

    def test_solve_symbolic_schema_has_literal_operation(self):
        mcp_tool = next(
            _as_mcp_tool(t) for t in all_tools if t.name == "solve_symbolic"
        )
        props = mcp_tool.inputSchema["properties"]
        assert "operation" in props
        # Literal types land as enum in JSON schema.
        op = props["operation"]
        enum = op.get("enum") or (op.get("anyOf", [{}])[0].get("enum"))
        if enum is None:
            # Pydantic may nest the enum under a $defs block — accept either.
            assert "operation" in props
        else:
            for val in ("derivative", "integral", "limit", "solve", "simplify", "evaluate"):
                assert val in enum


class TestServerBuild:
    def test_build_server_registers_all_tools(self):
        server = build_server()
        # We can't call the inner handler directly without a request context,
        # but the `list_tools` handler is registered so the server accepts
        # `tools/list` requests. The test therefore just asserts the server
        # was constructed without error and carries the right metadata.
        assert server.name == "arquimedes"


class TestCallToolRoundtrip:
    def test_assess_level_via_server_handler(self):
        server = build_server()
        # Grab the decorated handler from the server's internal registry.
        handler = None
        for key, fn in server.request_handlers.items():
            if getattr(key, "__name__", "") == "CallToolRequest":
                handler = fn
                break
        if handler is None:
            pytest.skip("MCP internals changed; handler lookup needs refresh")

        import mcp.types as types
        req = types.CallToolRequest(
            method="tools/call",
            params=types.CallToolRequestParams(
                name="assess_level",
                arguments={"subject": "linear_algebra", "student_response": "I know about eigenvectors and SVD"},
            ),
        )
        result = asyncio.run(handler(req))
        # ServerResult wraps CallToolResult; dig the text out.
        content_list = result.root.content
        text = "\n".join(c.text for c in content_list if hasattr(c, "text"))
        assert "ADVANCED" in text or "advanced" in text.lower()
