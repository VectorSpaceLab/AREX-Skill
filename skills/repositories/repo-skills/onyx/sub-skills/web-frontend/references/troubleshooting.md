# Web Frontend Troubleshooting

Use this reference when a web task is blocked by tooling, proxying, auth, stale generated artifacts, flaky waits, browser setup, Opal/shared packaging, or UI-standard violations.

## Fast triage

1. Confirm the task is frontend-owned. Rendered UI, component state, frontend services, SWR, App Router, Jest, and Playwright belong here. Backend endpoint logic, indexing, chat orchestration, LLM/tool execution, sandboxes, mobile, and CLI/deployment do not.
2. Check whether Bun and `web/node_modules` exist before running web scripts.
3. For API behavior, hit the frontend origin first: `http://localhost:3000/api/...`.
4. For test flake, inspect whether the assertion uses Playwright auto-retrying matchers or a one-shot DOM snapshot.
5. For UI review failures, look for raw controls, raw color classes, `dark:` modifiers, legacy components, relative imports, and missing Opal `Text`.

## Tooling and dependency failures

| Symptom | Likely cause | What to do |
| --- | --- | --- |
| `bun: command not found` | Bun is not installed in the environment | Install or request Bun before running web package scripts. If execution is optional, record that checks were not run due to missing Bun. |
| `Cannot find module` or missing test runner | Dependencies are absent | Run `cd web && bun install` when Bun is available. |
| Next or Jest cannot resolve Opal/shared package imports | Workspace packages or generated `dist/` output are missing | For app development, prefer `@opal/*` source aliases. For package-style imports, build shared then Opal when dependencies are available. |
| `typescript-7` or `next typegen` missing | Web dependencies are not installed | Install dependencies and rerun `cd web && bun run types:check`. |
| Lint/format commands missing | Web dependencies are absent or Bun unavailable | Install dependencies or record the blocker; do not substitute unpinned global tools. |

Avoid `npx` for Playwright test runs because it may fetch a different version. Use `bun run playwright ...` for tests after dependencies are installed.

## Frontend proxy and auth cookie issues

The frontend catch-all `/api/[...path]` proxy is development-only by default. It forwards to `INTERNAL_URL`, preserves cookies and streams, and may inject a debug auth cookie in local development.

| Symptom | Likely cause | What to check | Fix |
| --- | --- | --- | --- |
| `/api/...` returns 404 from Next | Proxy route is disabled outside development, or the wrong server is serving the page | Current Next mode, preview override flag, frontend server URL | Use the local dev server for frontend proxy testing, or configure the explicit preview override only for preview environments. |
| `/api/...` returns 500 `Proxy error` | Backend is unreachable or `INTERNAL_URL` is wrong | Frontend logs, backend availability, `INTERNAL_URL` value | Start/repair backend, or point `INTERNAL_URL` at the intended backend API base. |
| Browser is logged out against a remote backend | Missing/stale debug auth cookie, localhost cookies overriding remote auth, or cookie name mismatch | `.env.local` values, cookie storage for localhost, auth cookie name | Refresh the remote auth cookie, update local env, restart the dev server, and clear localhost cookies when necessary. |
| Playwright setup cannot register/login | Frontend or backend is not ready, auth route failing, first user is not admin in a reused DB | Readiness check and global setup logs | Ensure `http://localhost:3000/api/auth/type` returns 200. Reset/promote users only if needed for the test environment. |
| Curl works on backend `:8080` but UI fails | Bypassing the frontend proxy hid cookie/origin behavior | Calls made directly to backend | Reproduce through `http://localhost:3000/api/...` or relative `/api/...`. |

When debugging frontend code, do not treat direct backend calls as proof that browser behavior works. The app depends on frontend-origin cookies, redirects, and stream handling.

## Stale generated clients and route types

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Typed route errors after adding/moving pages | Next route types are stale | Run `cd web && bun run types:check`, which runs Next type generation before TypeScript. |
| Import from `src/lib/generated` fails | Generated artifacts are absent in the checkout | Regenerate the relevant artifact through the owning workflow; do not hand-edit generated output. |
| OpenAPI shape changed but frontend types are old | Backend schema/client generation was not refreshed | Route backend OpenAPI generation to the backend/CLI owners, then update frontend code against regenerated artifacts. |
| Package import from `@onyx-ai/shared` or `@onyx-ai/opal` lacks `dist` types | Workspace package build output is missing | Run package builds when dependencies are available. Build shared before Opal if both changed. |

Keep generated artifacts out of hand-written patches unless the repository explicitly expects them to be checked in.

## Flaky Playwright waits and assertions

Common anti-patterns and replacements:

| Anti-pattern | Why it flakes | Replace with |
| --- | --- | --- |
| `waitForTimeout()` | Sleeps do not prove state is ready | Locator assertions, `waitForResponse`, or `expect.poll()`. |
| `await locator.getAttribute()` then `expect(value)` | One-shot DOM snapshot before React state settles | `await expect(locator).toHaveAttribute(...)`. |
| `await locator.textContent()` then `expect(text)` | Reads stale text | `await expect(locator).toContainText(...)` or `toHaveText(...)`. |
| `await locator.count()` then `expect(count)` | Reads before async render completes | `await expect(locator).toHaveCount(n)`. |
| Inline locators in specs | Locator churn and inconsistent wait behavior | Move locators/actions into Page Objects. |
| Shared admin state in parallel tests | Tests mutate the same user/sidebar/history | Use worker users or admin2 and clean up by ID. |
| Random names in screenshots | Non-deterministic visual diffs | Prefer deterministic names plus cleanup; mask unavoidable dynamic content. |

Use `expect.poll()` only when no locator matcher exists, such as computed height or scroll metrics. For browser-only operations in a Page Object, keep `page.evaluate()` as an action/helper, not the final assertion on async UI state.

## Missing browser binary

If Playwright errors that Chromium or another browser executable is missing:

```bash
cd web && bun install
cd web && bunx playwright install chromium
```

Run the install only after dependencies exist so the local Playwright package is used. Then run specs with `bun run playwright ...`.

## Opal and shared package issues

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| App source imports work but package imports fail | App uses source aliases, package consumers need `dist` | Build the workspace package when dependencies are available. |
| Shared token/theme changes do not appear | Generated token CSS/types were not rebuilt | Build shared package outputs. If comparing token migration parity, run the token verification command when its baseline is available. |
| Shared package build starts pulling UI/runtime deps | A change violated the zero-runtime-dependency rule | Remove DOM/Node/React/Next/React Native usage from shared and keep contracts generic. |
| Opal component CSS missing in a package build | CSS bundle was not generated | Build Opal so its CSS bundling step runs. |
| Circular import/TDZ failures in Jest around Opal barrels | Opal barrel self-imports need the configured Jest lazy transform | Use the repository Jest config; do not replace it with ad-hoc global Jest. |

For web app code, prefer `@opal/components`, `@opal/layouts`, `@opal/icons`, and `@opal/utils`. For code inside Opal source, use `@opal/*` internals and keep component directories consistent with Opal conventions.

## Forbidden legacy or raw UI patterns

If review flags UI style issues, search for these patterns in the changed files:

- Raw `<button>`, `<input>`, or `<textarea>` where Opal/refresh components exist.
- Naked visible text nodes instead of `Text` or an Opal component that renders text.
- New imports from legacy `web/src/components/**` where Opal or sections fit.
- External icon imports from generic icon libraries.
- Tailwind raw palettes: `gray`, `slate`, `white`, `black`, `green`, `blue`, etc.
- New `dark:` modifiers outside logo/brand asset handling.
- Relative app imports like `../../../lib/foo` instead of `@/lib/foo`.
- String-built className values instead of `cn()`.
- Margins or wrapper-only divs where padding props are available.

The usual fix is to replace raw controls with Opal components, move repeated composites into `sections`, switch colors to Onyx semantic classes, and add accessible labels that tests can query.

## SWR and fetch failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Endless retries on auth/tier errors | Hook bypassed global retry suppression or uses custom config incorrectly | Use `skipRetryOnAuthError` for auth/tier-gated SWR reads. |
| Component shows stale data after mutation | Relevant SWR key was not mutated | Mutate the specific `SWR_KEYS` entry or use a key predicate for paginated variants. |
| Tests fail because fetch calls are out of order | Sequential mocks are undocumented or incomplete | Add endpoint comments for every mock and verify each expected URL/method. |
| User-facing error is generic | Response `detail` was not parsed | Use `parseErrorDetail` or an existing feature error helper at the fetch boundary. |
| Client calls backend `:8080` | Fetch helper bypassed frontend origin | Change to relative `/api/...` URL. |

## Craft frontend symptoms

| Symptom | Likely frontend cause | Route elsewhere when |
| --- | --- | --- |
| Tool cards or output panel render wrong packet state | Parser, stream item helper, store selector, or component renderer mismatch | Backend emitted an invalid/changed packet schema. |
| Sandbox status notice is stale | Pre-provision polling, wake-on-intent, or status reconciler did not refresh state | Sandbox provisioning, Docker/Kubernetes, or opencode runtime failed. |
| Scheduled task UI shows wrong state | Frontend task API helper or table state mismatch | Backend scheduler/task execution is wrong. |
| Preview tab path/URL is unsafe or broken | Frontend path sanitizer or URL bar rendering issue | Artifact storage or sandbox webapp server failed. |

Use Jest first for Craft parser/store/component issues. Use Playwright only when you need browser-level routing, preview, or service integration.

## Source script inventory and exclusions

No executable helper scripts are bundled with this sub-skill. The useful web commands are package scripts that depend on Bun, web dependencies, Playwright browser binaries, and running services, so they are recorded as concrete commands in the testing reference rather than copied or wrapped.

The existing Playwright authoring guidance was distilled into this skill instead of copied verbatim. Existing web tests were not copied; future agents should adapt their patterns and run the relevant current checkout tests when the environment permits.
