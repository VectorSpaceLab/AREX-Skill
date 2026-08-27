---
name: frontend-web-app
description: "Operate on the Transformer Lab React TypeScript web UI,
  authenticated data access, task and job screens, and browser verification."
disable-model-invocation: true
metadata:
  disco-role: operating
license: AGPL 3.0
---

# Frontend Web App

Use this sub-skill when modifying, debugging, or verifying the Transformer Lab browser UI under `src/renderer/`: React components, HashRouter routes, Joy UI screens, authenticated SWR/fetch data access, task queueing modals, job status/log views, and visual checks.

For implementation depth, read:

- [Frontend reference](references/frontend-reference.md) for architecture, routing, UI conventions, data access, and task/job screen patterns.
- [Verification](references/verification.md) for formatting, app readiness, browser verification, and E2E caveats.
- [Troubleshooting](references/troubleshooting.md) for common frontend failure modes.

## Operating Rules

1. Treat the app as a React 18 + TypeScript web app. Do not add Electron, IPC, or main-process patterns.
2. Use MUI Joy (`@mui/joy`) components and `lucide-react` icons. Do not introduce `@mui/material`, MUI icons, or Material component APIs.
3. Route all authenticated API reads through `useSWRWithAuth`, `useAPI`, or the shared `fetcher`; route mutations through `fetchWithAuth` or `authenticatedFetch` and revalidate affected SWR keys.
4. Prefer `Endpoints` helpers from the API client for URL construction. Add typed, URL-encoded endpoint helpers when adding new frontend API access.
5. Keep `HashRouter` route semantics intact; route paths should be app-relative (`/experiment/:experimentName/...`) and work behind a path prefix.
6. After changing frontend files, run the formatter command described in [Verification](references/verification.md). Use browser visual verification with the agent-browser workflow unless the user explicitly requests Playwright tests.

## Boundaries

- Backend router, schema, database, and service implementation belongs in [backend-api-services](../backend-api-services/SKILL.md).
- Job/provider lifecycle semantics, provider launch behavior, local/remote execution, and compute troubleshooting belong in [task-execution-compute](../task-execution-compute/SKILL.md).
- CLI and SDK workflows belong in [cli-sdk-workflows](../cli-sdk-workflows/SKILL.md).
