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


MAX_AGENT_ITERATIONS = 8
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
        "version": "1.0.0",
        "status": "active",
        "max_iterations": MAX_AGENT_ITERATIONS,
        "plugins_loaded": len(plugins),
        "total_tools": total_tools,
        "supported_providers": ["ollama", "claude", "gpt4", "groq", "deepseek", "mistral"],
        "capabilities": [
            "multi-step tool calling",
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
