---
description: "Use when editing FastAPI backend modules, schemas, orchestrator logic, or Python services under backend. Enforces schema-first and safe API behavior."
name: "Backend FastAPI Guardrails"
applyTo: "backend/**/*.py, tests/backend/**/*.py"
---
# Backend FastAPI Guardrails

## Scope
Apply these rules to backend API, orchestrator, database, and backend tests.

## API Contract First
- Update Pydantic schemas before changing endpoint handler logic.
- Keep request and response contracts explicit, with defaults and bounds where appropriate.
- Preserve backward compatibility for existing endpoints unless a breaking change is requested.

## Error Handling And Reliability
- Return controlled HTTP errors with clear status codes and stable response shapes.
- Avoid silent exceptions; log actionable context without exposing secrets.
- Keep network calls resilient with timeout and fallback behavior.

## Architecture Boundaries
- API entry points remain in backend/api/server.py unless a deliberate refactor is requested.
- Keep provider and routing decisions in backend/config and backend/orchestrator.
- Do not move cross-cutting concerns into endpoint handlers when a core module exists.

## Security And Secrets
- Never hardcode tokens, keys, or credentials in source files.
- Keep all secrets in .env and avoid logging secret-like values.
- Validate user-provided values used in file paths, shell calls, or external requests.

## Quality Gate
Before closing a backend change, run:
- python3 -m py_compile backend
- npm run test:backend

If a command fails, report exact error lines and minimal remediation.
