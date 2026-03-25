---
description: "Run the project release gate checklist for TypeScript, frontend, backend, and Tauri build readiness."
name: "Release Gate Checklist"
argument-hint: "Describe the release scope or branch"
agent: "agent"
tools: [read, search, execute]
---
Validate this release candidate end-to-end for VIO83 AI Orchestra.

Input scope: ${input:Describe scope, branch, or release objective}

Execute the checks in this order and stop on first failure:
1. npm run typecheck
2. npm run lint
3. npm run test:frontend
4. npm run test:backend
5. npm run build
6. npm run tauri:build

Output format:
1. Release summary in max 120 words.
2. Checklist with pass or fail for each command.
3. If any failure exists, include:
- root cause
- impacted files
- smallest safe fix
- rerun result
4. Risk table with severity and mitigation.
5. Final recommendation: GO or NO-GO.

Constraints:
- Do not invent command output.
- Report exact failing command and key lines from output.
- Keep changes minimal and scoped to failures.
