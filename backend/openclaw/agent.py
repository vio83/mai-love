# VIO 83 AI ORCHESTRA — OpenClaw Agent Runtime
# Copyright (c) 2026 Viorica Porcu. AGPL-3.0 / Proprietaria
"""
OpenClaw Agent: agentic tool-calling loop.

Flow:
  1. User sends a task/message
  2. AI analyzes and decides which tools to call
  3. Tools execute via plugin registry
  4. Results feed back to AI
  5. Repeat until AI provides a final answer (max N iterations)

Uses Ollama locally or cloud providers for reasoning.
"""
from __future__ import annotations

import asyncio
import json
import time
import re
from dataclasses import dataclass, field
from typing import Any, Optional

from backend.plugins.registry import PluginRegistry, get_registry


@dataclass
class ToolCall:
    plugin_id: str
    tool_name: str
    params: dict[str, Any]


@dataclass
class AgentStep:
    step: int
    action: str  # "think", "tool_call", "tool_result", "answer"
    content: str
    tool_call: Optional[ToolCall] = None
    tool_result: Optional[dict] = None
    latency_ms: int = 0


@dataclass
class AgentResult:
    task: str
    answer: str
    steps: list[AgentStep] = field(default_factory=list)
    total_steps: int = 0
    total_latency_ms: int = 0
    tools_used: list[str] = field(default_factory=list)
    status: str = "completed"  # completed, max_iterations, error


MAX_AGENT_ITERATIONS = 24
TOOL_CALL_PATTERN = re.compile(
    r"<tool_call>\s*\{.*?\}\s*</tool_call>",
    re.DOTALL,
)


def _build_tools_description(registry: PluginRegistry) -> str:
    """Build a concise tool catalog for the AI system prompt."""
    lines: list[str] = []
    for plugin_dict in registry.list_plugins():
        pid = plugin_dict["id"]
        for tool in plugin_dict.get("tools", []):
            tname = tool["name"]
            desc = tool["description"]
            params = tool.get("parameters", {})
            param_str = ", ".join(
                f'{k}: {v.get("type", "string")}'
                for k, v in params.get("properties", {}).items()
            )
            lines.append(f"- {pid}/{tname}({param_str}) — {desc}")
    return "\n".join(lines)


def _build_agent_system_prompt(tools_desc: str) -> str:
    return f"""You are OpenClaw, the agent runtime of VIO 83 AI Orchestra.
You solve tasks step by step using available tools.

AVAILABLE TOOLS:
{tools_desc}

INSTRUCTIONS:
- Analyze the task, then decide if you need a tool.
- To call a tool, output EXACTLY:
<tool_call>{{"plugin":"PLUGIN_ID","tool":"TOOL_NAME","params":{{...}}}}</tool_call>
- After receiving tool results, analyze them and decide next step.
- When you have the final answer, respond normally WITHOUT any <tool_call> tags.
- Be concise. Max {MAX_AGENT_ITERATIONS} tool calls per task.
- If no tool is needed, answer directly.
"""


def _build_native_tools(registry: PluginRegistry) -> list[dict]:
    """
    Converte i tool del registry nel formato OpenAI/Claude function calling nativo.
    Usato per provider che supportano tools=[...] nella API.
    """
    native_tools = []
    for plugin_dict in registry.list_plugins():
        pid = plugin_dict["id"]
        for tool in plugin_dict.get("tools", []):
            native_tools.append({
                "type": "function",
                "function": {
                    "name": f"{pid}__{tool['name']}",
                    "description": tool["description"],
                    "parameters": tool.get("parameters", {"type": "object", "properties": {}}),
                },
            })
    return native_tools


def _build_claude_native_tools(registry: PluginRegistry) -> list[dict]:
    """
    Converte i tool nel formato Anthropic tool_use nativo.
    """
    native_tools = []
    for plugin_dict in registry.list_plugins():
        pid = plugin_dict["id"]
        for tool in plugin_dict.get("tools", []):
            native_tools.append({
                "name": f"{pid}__{tool['name']}",
                "description": tool["description"],
                "input_schema": tool.get("parameters", {"type": "object", "properties": {}}),
            })
    return native_tools


# ─── Provider che supportano native function calling ───────────────
NATIVE_TOOL_PROVIDERS = {"gpt4", "claude", "groq", "deepseek", "mistral"}


def _parse_tool_call(text: str) -> Optional[ToolCall]:
    """Extract a tool call from AI response text."""
    match = TOOL_CALL_PATTERN.search(text)
    if not match:
        return None
    raw = match.group(0)
    # Extract JSON between tags
    json_str = raw.replace("<tool_call>", "").replace("</tool_call>", "").strip()
    try:
        data = json.loads(json_str)
    except json.JSONDecodeError:
        return None

    plugin_id = data.get("plugin", "")
    tool_name = data.get("tool", "")
    params = data.get("params", {})

    if not plugin_id or not tool_name:
        return None

    return ToolCall(plugin_id=plugin_id, tool_name=tool_name, params=params)


async def run_agent(
    task: str,
    model: str = "qwen2.5-coder:3b",
    provider: str = "ollama",
    registry: Optional[PluginRegistry] = None,
    max_iterations: int = MAX_AGENT_ITERATIONS,
) -> AgentResult:
    """
    Execute the agentic tool-calling loop.

    Returns AgentResult with the final answer and all intermediate steps.
    """
    if registry is None:
        registry = get_registry()

    tools_desc = _build_tools_description(registry)
    system_prompt = _build_agent_system_prompt(tools_desc)

    # Import the orchestrator's call functions
    from backend.orchestrator.direct_router import call_ollama, call_cloud

    messages: list[dict[str, str]] = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": task},
    ]

    result = AgentResult(task=task, answer="", steps=[])
    start_total = time.time()

    for iteration in range(max_iterations):
        step_start = time.time()

        # Call AI
        try:
            if provider == "ollama":
                ai_response = await call_ollama(
                    messages=messages,
                    model=model,
                    temperature=0.1,
                    max_tokens=1024,
                )
            else:
                ai_response = await call_cloud(
                    messages=messages,
                    provider=provider,
                    model=model if model != "auto" else None,
                    temperature=0.1,
                    max_tokens=1024,
                )
        except Exception as e:
            result.steps.append(AgentStep(
                step=iteration + 1,
                action="error",
                content=f"AI call failed: {e}",
                latency_ms=int((time.time() - step_start) * 1000),
            ))
            result.status = "error"
            result.answer = f"Agent error: {e}"
            break

        response_text = ai_response.get("content", "")
        step_ms = int((time.time() - step_start) * 1000)

        # Check for tool call
        tool_call = _parse_tool_call(response_text)

        if tool_call is None:
            # No tool call → this is the final answer
            result.steps.append(AgentStep(
                step=iteration + 1,
                action="answer",
                content=response_text,
                latency_ms=step_ms,
            ))
            result.answer = response_text
            break

        # Record thinking step
        thinking_text = TOOL_CALL_PATTERN.sub("", response_text).strip()
        if thinking_text:
            result.steps.append(AgentStep(
                step=iteration + 1,
                action="think",
                content=thinking_text,
                latency_ms=step_ms,
            ))

        # Execute tool
        tool_start = time.time()
        tool_result = registry.execute(
            tool_call.plugin_id,
            tool_call.tool_name,
            tool_call.params,
        )
        tool_ms = int((time.time() - tool_start) * 1000)

        result.steps.append(AgentStep(
            step=iteration + 1,
            action="tool_call",
            content=f"{tool_call.plugin_id}/{tool_call.tool_name}",
            tool_call=tool_call,
            latency_ms=step_ms,
        ))
        result.steps.append(AgentStep(
            step=iteration + 1,
            action="tool_result",
            content=json.dumps(tool_result, ensure_ascii=False, default=str)[:2000],
            tool_result=tool_result,
            latency_ms=tool_ms,
        ))

        tool_id = f"{tool_call.plugin_id}/{tool_call.tool_name}"
        if tool_id not in result.tools_used:
            result.tools_used.append(tool_id)

        # Feed result back to AI
        messages.append({"role": "assistant", "content": response_text})
        messages.append({
            "role": "user",
            "content": f"Tool result for {tool_call.plugin_id}/{tool_call.tool_name}:\n{json.dumps(tool_result, ensure_ascii=False, default=str)[:2000]}",
        })
    else:
        # Max iterations reached
        result.status = "max_iterations"
        if not result.answer:
            result.answer = "Agent reached maximum iterations. Partial results available in steps."

    result.total_steps = len(result.steps)
    result.total_latency_ms = int((time.time() - start_total) * 1000)
    return result


def get_agent_capabilities(registry: Optional[PluginRegistry] = None) -> dict:
    """Return a summary of OpenClaw agent capabilities."""
    if registry is None:
        registry = get_registry()

    plugins = registry.list_plugins()
    total_tools = sum(len(p.get("tools", [])) for p in plugins)

    return {
        "name": "OpenClaw Agent Runtime",
        "version": "2.0.0",
        "status": "active",
        "always_active": True,
        "auto_start": True,
        "max_iterations": MAX_AGENT_ITERATIONS,
        "plugins_loaded": len(plugins),
        "total_tools": total_tools,
        "supported_providers": ["ollama", "claude", "gpt4", "groq", "deepseek", "mistral"],
        "native_tool_calling": list(NATIVE_TOOL_PROVIDERS),
        "capabilities": [
            "multi-step tool calling",
            "native function calling (OpenAI/Claude)",
            "automatic tool selection",
            "file system operations",
            "web search",
            "code execution",
            "data processing",
            "system info",
            "git operations",
            "translation",
            "persistent memory",
        ],
    }


async def run_agent_native(
    task: str,
    provider: str = "gpt4",
    model: str = "",
    registry: Optional[PluginRegistry] = None,
    max_iterations: int = MAX_AGENT_ITERATIONS,
) -> AgentResult:
    """
    Agentic loop con NATIVE function calling (OpenAI/Claude API).

    Invece di parsare XML <tool_call>, usa il meccanismo tools=[...] nativo
    delle API OpenAI e Anthropic. Più affidabile e preciso.

    Fallback automatico a run_agent() per provider senza native tools.
    """
    if provider not in NATIVE_TOOL_PROVIDERS:
        return await run_agent(task, model=model or "qwen2.5-coder:3b",
                               provider=provider, registry=registry,
                               max_iterations=max_iterations)

    if registry is None:
        registry = get_registry()

    from backend.orchestrator.direct_router import (
        _resolve_cloud_model, _resolve_cloud_api_key,
        _cloud_base_url, _build_cloud_headers,
        _http_post_json, _normalize_messages_for_claude,
    )

    resolved_model = _resolve_cloud_model(provider, model or None)
    api_key = _resolve_cloud_api_key(provider)
    base_url = _cloud_base_url(provider)
    headers = _build_cloud_headers(provider, api_key)

    is_claude = provider == "claude"

    # Build native tools
    tools = _build_claude_native_tools(registry) if is_claude else _build_native_tools(registry)

    messages: list[dict] = [
        {"role": "system", "content": (
            "You are OpenClaw, the agent runtime of VIO 83 AI Orchestra. "
            "Solve tasks step by step using the available tools. "
            "When you have the final answer, respond without tool calls."
        )},
        {"role": "user", "content": task},
    ]

    result = AgentResult(task=task, answer="", steps=[])
    start_total = time.time()

    for iteration in range(max_iterations):
        step_start = time.time()

        try:
            if is_claude:
                system_text, anthropic_msgs = _normalize_messages_for_claude(messages)
                payload = {
                    "model": resolved_model,
                    "system": system_text,
                    "messages": anthropic_msgs,
                    "tools": tools,
                    "max_tokens": 2048,
                    "temperature": 0.1,
                }
                data = await _http_post_json(
                    f"{base_url}/messages", headers=headers,
                    payload=payload, timeout_s=120.0,
                )
                # Parse Claude response
                content_blocks = data.get("content", [])
                text_parts = []
                tool_uses = []
                for block in content_blocks:
                    if block.get("type") == "text":
                        text_parts.append(block.get("text", ""))
                    elif block.get("type") == "tool_use":
                        tool_uses.append(block)

                response_text = "".join(text_parts).strip()
                data.get("stop_reason", "")

            else:
                # OpenAI-compatible format — G2: enable parallel tool calls
                payload = {
                    "model": resolved_model,
                    "messages": messages,
                    "tools": tools,
                    "parallel_tool_calls": True,
                    "max_tokens": 2048,
                    "temperature": 0.1,
                }
                data = await _http_post_json(
                    f"{base_url}/chat/completions", headers=headers,
                    payload=payload, timeout_s=120.0,
                )
                choice = data.get("choices", [{}])[0]
                msg = choice.get("message", {})
                response_text = msg.get("content", "") or ""
                tool_calls_raw = msg.get("tool_calls", [])
                tool_uses = []
                for tc in tool_calls_raw:
                    fn = tc.get("function", {})
                    name = fn.get("name", "")
                    try:
                        args = json.loads(fn.get("arguments", "{}"))
                    except json.JSONDecodeError:
                        args = {}
                    tool_uses.append({
                        "id": tc.get("id", ""),
                        "name": name,
                        "input": args,
                    })
                choice.get("finish_reason", "")

        except Exception as e:
            result.steps.append(AgentStep(
                step=iteration + 1, action="error",
                content=f"Native tool call failed: {e}",
                latency_ms=int((time.time() - step_start) * 1000),
            ))
            result.status = "error"
            result.answer = f"Agent error: {e}"
            break

        step_ms = int((time.time() - step_start) * 1000)

        if not tool_uses:
            # Final answer
            result.steps.append(AgentStep(
                step=iteration + 1, action="answer",
                content=response_text, latency_ms=step_ms,
            ))
            result.answer = response_text
            break

        # Execute tool calls — G2: parallel execution when multiple tools
        async def _exec_one_tool(tu_item):
            """Execute a single tool call, returns (tu_item, plugin_id, tool_name, params, tool_result)."""
            tn_full = tu_item.get("name", "")
            parts = tn_full.split("__", 1)
            if len(parts) == 2:
                pid, tname = parts
            else:
                pid, tname = "", tn_full
            prms = tu_item.get("input", {})
            tres = await asyncio.to_thread(registry.execute, pid, tname, prms)
            return tu_item, pid, tname, prms, tres

        # Run all tool calls concurrently
        tool_exec_results = await asyncio.gather(
            *[_exec_one_tool(tu) for tu in tool_uses],
            return_exceptions=True,
        )

        # Collect results for feeding back to the model
        assistant_tool_calls_openai = []
        tool_messages_openai = []
        claude_tool_result_blocks = []

        for idx, exec_res in enumerate(tool_exec_results):
            if isinstance(exec_res, Exception):
                tu = tool_uses[idx]
                tool_name_full = tu.get("name", "")
                tool_result = {"error": str(exec_res)}
                plugin_id, tool_name, params = "", tool_name_full, tu.get("input", {})
            else:
                tu, plugin_id, tool_name, params, tool_result = exec_res
                tool_name_full = tu.get("name", "")

            result.steps.append(AgentStep(
                step=iteration + 1, action="tool_call",
                content=f"{plugin_id}/{tool_name}",
                tool_call=ToolCall(plugin_id, tool_name, params),
                latency_ms=step_ms,
            ))
            result.steps.append(AgentStep(
                step=iteration + 1, action="tool_result",
                content=json.dumps(tool_result, ensure_ascii=False, default=str)[:2000],
                tool_result=tool_result,
            ))

            tool_id = f"{plugin_id}/{tool_name}"
            if tool_id not in result.tools_used:
                result.tools_used.append(tool_id)

            result_json = json.dumps(tool_result, ensure_ascii=False, default=str)[:2000]

            if is_claude:
                claude_tool_result_blocks.append({
                    "type": "tool_result",
                    "tool_use_id": tu.get("id", ""),
                    "content": result_json,
                })
            else:
                assistant_tool_calls_openai.append({
                    "id": tu.get("id", ""),
                    "type": "function",
                    "function": {
                        "name": tool_name_full,
                        "arguments": json.dumps(params),
                    },
                })
                tool_messages_openai.append({
                    "role": "tool",
                    "tool_call_id": tu.get("id", ""),
                    "content": result_json,
                })

        # Feed all results back to the model in one turn
        if is_claude:
            messages.append({"role": "assistant", "content": data.get("content", [])})
            messages.append({"role": "user", "content": claude_tool_result_blocks})
        else:
            messages.append({
                "role": "assistant",
                "content": response_text,
                "tool_calls": assistant_tool_calls_openai,
            })
            for tm in tool_messages_openai:
                messages.append(tm)
    else:
        result.status = "max_iterations"
        if not result.answer:
            result.answer = "Agent reached maximum iterations."

    result.total_steps = len(result.steps)
    result.total_latency_ms = int((time.time() - start_total) * 1000)
    return result
