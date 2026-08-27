---
name: web-client-development
description: "Develop, test, build, and troubleshoot Galaxy's Vue/TypeScript
  client, pnpm workspace, Vitest tests, MSW/OpenAPI mocks, and generated
  API-client package."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Galaxy Web Client Development

Use this sub-skill when a task involves Galaxy client build commands, pnpm workspace packages, Vue/TypeScript changes, Vitest unit tests, Vue Test Utils, Pinia test setup, MSW/OpenAPI API mocks, Vite dev-server proxy settings, static client artifacts, or the generated `@galaxyproject/galaxy-api-client` package.

## Start Here

- For safe command selection, run `python scripts/client_command_planner.py --help`; it only prints recommended commands, prerequisites, and cautions.
- For build/dev-server/package workflow choices, read [Client Development](references/client-development.md).
- For Vitest, Vue Test Utils, Pinia, async assertions, and MSW/OpenAPI mocks, read [Client Testing](references/client-testing.md).
- For `node`/`pnpm` mismatch, missing artifacts, stale API schema, proxy/origin/port issues, and test flakiness, read [Troubleshooting](references/troubleshooting.md).

## Routing Boundaries

- Stay here for `client/` pnpm scripts, Vite builds, dev-server proxy, frontend lint/format/type-check, component unit tests, test mocks, and the API-client workspace package.
- Use `../api-automation/SKILL.md` for backend endpoint semantics, OpenAPI route design, API keys, API smoke automation, or Python API tests.
- Use `../configuration-and-admin/SKILL.md` for starting/configuring the Galaxy backend server that the dev server proxies to.
- Route Selenium, Playwright, server-backed browser tests, and full-stack UI behavior to root Galaxy test guidance rather than treating them as Vitest unit tests.

## Safe Defaults

- Do not run `pnpm install`, full builds, or all client tests without user confirmation; dependency install/build steps can be long-running.
- Prefer targeted Vitest commands for changed files, then broader `pnpm test`, `pnpm run type-check`, lint, or build when the user asks to validate comprehensively.
- Do not commit generated client artifacts; Galaxy does not keep built client bundles in source control.
- Prefer type-safe `GalaxyApi` and MSW/OpenAPI mocks over ad hoc Axios or untyped network stubs when the endpoint is in the schema.
