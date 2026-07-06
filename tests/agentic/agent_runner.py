import json
from dataclasses import dataclass, field
from typing import Any

import anthropic
from mcp.server.fastmcp import FastMCP

DEFAULT_MODEL = "claude-haiku-4-5-20251001"

_SYSTEM_PROMPT = (
    "You are a shopping assistant with tools to search a catalog, manage a cart, and "
    "check out. Use the tools to fully satisfy the user's request, including completing "
    "checkout -- don't stop after just adding items to the cart. "
    'Use payment_token "tok_ok" and make up a unique idempotency_key. '
    'Ship to this address: {"line1": "1 Infinite Loop", "city": "Cupertino", '
    '"postal_code": "95014"}.'
)


@dataclass
class ToolCall:
    name: str
    input: dict[str, Any]
    output: Any


@dataclass
class AgentRunResult:
    instruction: str
    transcript: list[ToolCall] = field(default_factory=list)
    final_text: str = ""
    last_cart: dict[str, Any] | None = None
    last_order: dict[str, Any] | None = None


async def _mcp_tools_as_anthropic_tools(mcp_server: FastMCP) -> list[dict[str, Any]]:
    tools = await mcp_server.list_tools()
    return [
        {"name": t.name, "description": t.description or "", "input_schema": t.inputSchema}
        for t in tools
    ]


async def _call_mcp_tool(mcp_server: FastMCP, name: str, arguments: dict[str, Any]) -> Any:
    result = await mcp_server.call_tool(name, arguments)
    if isinstance(result, list) and result:
        text = getattr(result[0], "text", None)
        if text is not None:
            try:
                return json.loads(text)
            except ValueError:
                return text
    return result


async def run_agent(
    instruction: str,
    mcp_server: FastMCP,
    *,
    model: str = DEFAULT_MODEL,
    max_turns: int = 8,
) -> AgentRunResult:
    client = anthropic.AsyncAnthropic()
    tools = await _mcp_tools_as_anthropic_tools(mcp_server)
    messages: list[dict[str, Any]] = [{"role": "user", "content": instruction}]
    result = AgentRunResult(instruction=instruction)

    for _ in range(max_turns):
        response = await client.messages.create(
            model=model,
            max_tokens=1024,
            system=_SYSTEM_PROMPT,
            messages=messages,
            tools=tools,
        )
        messages.append({"role": "assistant", "content": response.content})

        tool_uses = [block for block in response.content if block.type == "tool_use"]
        if not tool_uses:
            result.final_text = "\n".join(
                block.text for block in response.content if block.type == "text"
            )
            break

        tool_results = []
        for block in tool_uses:
            output = await _call_mcp_tool(mcp_server, block.name, block.input)
            result.transcript.append(ToolCall(name=block.name, input=block.input, output=output))
            if block.name in ("create_cart", "add_item", "view_cart"):
                result.last_cart = output
            if block.name in ("checkout", "get_order_status"):
                result.last_order = output
            tool_results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(output),
                }
            )
        messages.append({"role": "user", "content": tool_results})

    return result
