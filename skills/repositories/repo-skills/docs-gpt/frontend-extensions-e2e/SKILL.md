---
name: frontend-extensions-e2e
description: "Use for DocsGPT React/Vite frontend and docs work, Chatwoot and
  React widget extensions, and Playwright end-to-end verification."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Frontend, extensions, and E2E skill

Use this subskill for React/Vite UI work, docs-site work, widget or Chatwoot integration, and Playwright/E2E verification.

## Primary surfaces

- Frontend app: `frontend/`.
- Docs site: `docs/`.
- Extensions: `extensions/chatwoot/` and `extensions/react-widget/`.
- E2E harness: `tests/e2e/` plus `scripts/e2e/*`.

## Frontend commands

```bash
cd frontend
npm install --include=dev
npm run dev
npm run lint
npm run build
npm run test
```

Guidance:

- Prefer `lucide-react` for standard icons.
- Use SVG React imports for brand or domain illustrations that need theming.
- Avoid introducing new `<img src={...}>` icon patterns.
- Keep changes small and reuse existing components/hooks when possible.
- Use Redux if shared global state is necessary.

## Docs site commands

```bash
cd docs
npm install
npm run dev
npm run build
```

If prose changed and Vale is available, run `vale .` as well.

## E2E harness commands

```bash
cd tests/e2e
npm run e2e:install
npm run e2e:up
npm run e2e
npm run e2e:down
```

Useful helpers also live under `scripts/e2e/` for mock LLM and OIDC services, database reset, and stack lifecycle.

## Extension-specific notes

- `extensions/chatwoot/` is a Python bridge service; inspect its sample env before changing docs or startup guidance.
- `extensions/react-widget/` is a reusable widget package. Keep docs and build instructions aligned with the widget README.

## When to use screenshots or video

For any user-visible UI change, ask for a screenshot or short video in the PR summary or review handoff. This repo explicitly calls that out as part of PR readiness.

## What to check in source/docs

- `frontend/package.json`
- `docs/package.json`
- `tests/e2e/package.json`
- `docs/content/Extensions/chat-widget.mdx`
- `docs/content/Extensions/Chatwoot-extension.mdx`
- `docs/content/Guides/Benchmarking-Agents.mdx`
- `tests/e2e/README.md`

## Safe checks

```bash
python skills/disco/docs-gpt/scripts/inspect_api_routes.py --repo . --contains /api/events
cd frontend && npm run lint && npm run build
cd docs && npm run build
```

If a UI change affects chat or streaming behavior, verify it against the ASGI app and the E2E harness instead of relying on isolated component tests alone.
