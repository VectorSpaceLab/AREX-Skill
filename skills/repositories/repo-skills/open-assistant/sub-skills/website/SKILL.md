---
name: website
description: "Work with Open-Assistant's Next.js website, contribution task UI,
  chat UI, frontend API client, local dev, tests, Prisma, feature flags, and
  localization."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Website sub-skill

Use this sub-skill when the task is about the Open-Assistant Next.js website: local frontend development, contribution task pages, chat UI integration, the browser-facing API client, Jest/Cypress/Storybook checks, Prisma-backed website auth/task cache data, feature flags, or localization.

## Read first

- For setup, service profiles, package scripts, Prisma, feature flags, and localization maintenance, read `references/workflows.md`.
- For contribution task route mapping, task component behavior, review/submit state, frontend API client methods, and chat/SSE flow, read `references/ui-task-reference.md`.
- For selecting and running unit, component, e2e, contract, Storybook, and locale checks, read `references/testing.md`.
- For failure diagnosis, read `references/troubleshooting.md`.
- Use bundled helpers under `scripts/` rather than relying on repository helper scripts:
  - `scripts/run_frontend_checks.sh`
  - `scripts/find_missing_locales.py`

## Best-fit tasks

Use this sub-skill for requests such as:

- Add or debug a contribution task page, task component, validation rule, review/submit flow, or stable `data-cy` selector.
- Debug or extend the website's OASST API client calls, frontend task fetching/ack/interact sequence, or frontend-side error rendering.
- Work on the chat pages, chat form keyboard behavior, streamed response display, queue/plugin intermediate UI, or browser parsing of server-sent event chunks.
- Prepare local frontend development, run package checks, fix Jest/jsdom failures, author Cypress component/e2e/contract tests, or build Storybook.
- Add translations, audit locale JSON completeness, run inlang checks, or clean up feature-flagged UI.
- Touch Prisma only for website auth/session/task-cache tables and local development database synchronization.

## Route elsewhere or exclude

- Backend endpoint semantics, task scheduler rules, database internals, worker behavior, and protocol ownership belong to the `backend` sub-skill. This website sub-skill only covers how the website calls those APIs and handles responses.
- Inference server, worker, model configuration internals, websocket protocol, model downloads, and generation failures belong to the `inference` sub-skill. This sub-skill only covers website chat UI, API routes, and SSE handling at the browser/Next layer.
- Model training, evaluation pipelines, production deployment, Ansible, infrastructure, and Docusaurus docs-site maintainer work are out of scope for this sub-skill.

## Operating pattern

1. Identify whether the request targets setup, contribution task UI, chat UI, API client behavior, tests, Prisma, feature flags, or localization.
2. Read the matching bundled reference before editing. Keep implementation details grounded in the route/component/API names summarized there.
3. Prefer local, deterministic checks first: lint, typecheck, one-shot Jest, targeted Cypress component or contract checks, and the bundled locale audit. Use full e2e only when the local service stack is available.
4. Do not depend on original repository docs, examples, tests, or helper scripts as instructions for future work. If a workflow needs a reusable command, use or extend the bundled helper scripts in this sub-skill.
5. When a failure crosses into backend task semantics or inference internals, stop at the boundary and route to the owning sub-skill with the observed website-side symptom.
