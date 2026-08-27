---
name: web-frontend
description: "Onyx web frontend guidance for Next.js 16, React 19, Opal UI, API
  proxying, chat/admin/Craft surfaces, Jest, and Playwright."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Web Frontend

Use this sub-skill when the task is mainly in the Onyx web app: Next.js app routes, React components, Opal design system usage, frontend data fetching, `/api` proxy behavior, chat/admin/Craft UI, Jest/RTL tests, or Playwright E2E.

Stay inside this scope. Route mobile React Native patterns to the mobile-client sibling skill, backend route/model/task implementation to backend-platform or agents-craft-and-tools, and CLI/deployment tooling to cli-deployment-devtools.

Read [references/frontend-architecture.md](references/frontend-architecture.md) when you need route layout, app/admin/chat/Craft surface ownership, frontend API proxy behavior, feature hooks/services, or generated type guidance.

Read [references/opal-and-ui-standards.md](references/opal-and-ui-standards.md) before selecting components, writing visible UI, changing layout/spacing/colors, adding icons, or organizing frontend hooks and types.

Read [references/testing.md](references/testing.md) when choosing or writing Jest/React Testing Library tests, Playwright E2E, visual regression, auth setup, or frontend verification commands.

Read [references/troubleshooting.md](references/troubleshooting.md) when Bun/dependencies, proxy/auth cookies, stale types, flaky Playwright waits, browser binaries, Opal/shared builds, or forbidden legacy UI patterns block progress.

Primary working surfaces are `web/src/app/**`, `web/src/lib/**`, `web/src/sections/**`, `web/src/layouts/**`, `web/lib/opal/**`, `web/lib/shared/**`, and `web/tests/**`. Future agents should use the bundled references first, then inspect only the current checkout files needed for the requested change.
