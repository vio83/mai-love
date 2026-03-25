---
description: "Use when editing React, TypeScript, Vite frontend files in src or frontend tests. Enforces strict typing, state consistency, and UI safety checks."
name: "Frontend TypeScript Strict"
applyTo: "src/**/*.ts, src/**/*.tsx, tests/frontend/**/*.ts"
---
# Frontend TypeScript Strict Guidelines

## Scope
Apply these rules to frontend code in src and frontend tests.

## Type Safety
- Keep TypeScript strict-compliant and avoid any unless there is no practical typed alternative.
- Prefer explicit domain types for API payloads, store slices, and component props.
- Avoid non-null assertions; prefer guards and safe fallbacks.

## State And Data Flow
- Reuse existing Zustand store contracts before adding new global state.
- Keep derived values in memoized selectors or useMemo when they are computed from state.
- Do not mutate store objects in-place; keep updates immutable and predictable.

## React And UI
- Preserve existing visual tokens and CSS variable usage.
- Keep side effects in useEffect and avoid mixing fetch logic directly into render paths.
- Ensure loading, empty, and error states are explicitly handled for async flows.

## Runtime And API Integration
- Treat backend responses as untrusted input and validate shape before deep access.
- Keep localhost runtime endpoints centralized and consistent with existing patterns.
- For polling and intervals, always clean up timers and abort in-flight requests on unmount.

## Quality Gate
Before closing a frontend change, run:
- npm run typecheck
- npm run lint
- npm run test:frontend

If a command fails, report the exact failure and the smallest fix applied.
