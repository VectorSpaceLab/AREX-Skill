---
name: "frontend"
description: "Use frontend for Unstract's React/Vite/Bun browser app, route
  tree, runtime config, build, and browser-side troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: AGPL 3.0
---

# Frontend

Use this sub-skill when the task is about the Unstract browser app: routing, runtime config, Vite/Bun tooling, build / lint / preview commands, or browser-side startup problems.

## Owns

- `frontend/src/`, including the route tree, config helper, stores, and shell components.
- `frontend/vite.config.js` and `frontend/generate-runtime-config.sh`.
- Vite / Bun install, build, preview, and lint commands.
- Browser-side runtime config, proxy configuration, and route-loading behavior.

## Excludes

- Backend route families and hosted MCP behavior — use `backend-platform`.
- Full-stack startup / deployment — use `platform-deployment`.
- Worker queue routing — use `workers`.
- Shared SDK / tool registry workflows — use `sdk-and-tools`.
- Repo test-group manifests — use `testing-rig`.

## Start Here

Read `references/routes-and-runtime.md` when you need the frontend route tree, runtime-config precedence, or the Vite proxy / build settings.

Read `references/troubleshooting.md` when the UI is using the wrong backend URL, the runtime config is stale, or the dev server / build is failing.

For a safe install / build check:

```bash
cd frontend
bun install
bun run build
```

## Shared References

- `references/routes-and-runtime.md` — route tree, runtime config, and Vite behavior.
- `references/troubleshooting.md` — frontend startup, proxy, and runtime-config failures.
- `../../references/service-map.md` — repo-wide service map and dependencies.
- `../../references/installation-and-env.md` — install and env matrix for the frontend workflow.
- `../../scripts/check_unstract_packages.py` — shared package checker if you also need backend / tool validation.

## Common Task Routing

| User request | Read next |
| --- | --- |
| "Why does the UI route to the wrong page?" | `references/routes-and-runtime.md` |
| "How do I change the backend URL?" | `references/routes-and-runtime.md` |
| "Why is the runtime config stale?" | `references/troubleshooting.md` |
| "Why does Vite / Bun fail?" | `references/troubleshooting.md` |
| "What does this route belong to?" | `references/routes-and-runtime.md` |

## Safety Boundaries

- Do not assume the frontend has tests just because the app builds.
- Do not rely on `process.env.REACT_APP_*`; the app uses Vite runtime and `VITE_*` env vars.
- Do not debug route chunks before checking the optional-plugin and lazy-load behavior in Vite.
