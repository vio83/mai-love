---
description: "Use when editing GIU-L_IA engine and runtime setup in brace-v3. Enforces anti-manipulation and anti-dependency bunker policy with positive education objective."
name: "GIU-L_IA Bunker Relational Safety"
applyTo: "brace-v3/**/*.py"
---
# GIU-L_IA Bunker Relational Safety

## Objective
Keep GIU-L_IA strictly aligned to one objective: positive education for healthier human interactions.

## Non-Negotiable Bunker Policy
- Never generate or normalize manipulation tactics.
- Never generate dependency mechanics (emotional hooks, isolation pressure, obedience framing).
- Never reinforce guilt, fear, or coercive leverage.
- Always redirect to consent, autonomy, boundaries, and reciprocal responsibility.

## Runtime Behavior Rules
- If manipulation or dependency signals are detected, switch to de-escalation mode.
- Explain why the detected pattern is harmful in real life.
- Provide safe alternatives in plain language.
- If high risk persists, suggest external support resources.

## Output Contract
- Keep `pil_result` explicit on: risk level, detected signals, mode, and prevention guidance.
- Keep `system_prompt` explicit about anti-manipulation and anti-dependency constraints.
- Preserve backward compatibility of existing API response keys unless a breaking change is requested.

## Verification Gate
Before closing changes in `brace-v3/`:
- `python3 -m py_compile brace-v3`
