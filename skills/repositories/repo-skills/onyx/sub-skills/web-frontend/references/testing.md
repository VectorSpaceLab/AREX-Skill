# Frontend Testing

Use this reference to select, write, and run Onyx web checks. Commands require the web toolchain; if Bun, node_modules, browsers, or services are unavailable, record that explicitly instead of claiming a pass.

## Command quick reference

Run commands from the repository root unless a command starts with `cd web`.

```bash
# Install web dependencies when Bun is available.
cd web && bun install

# Jest / React Testing Library.
cd web && bun run test
cd web && bun run test -- MinimalMarkdown.test
cd web && bun run test -- --testPathPattern="auth"
cd web && bun run test:ci

# Type, lint, and formatting checks.
cd web && bun run types:check
cd web && bun run lint
cd web && bun run format:check

# Playwright. Prefer the package script for test runs so the repo-pinned version is used.
cd web && bun run playwright tests/e2e/chat/welcome_page.spec.ts --project admin
cd web && bun run playwright tests/e2e/chat/welcome_page.spec.ts -g "chat input is visible" --project admin
cd web && bun run playwright --ui
cd web && bun run playwright --headed

# Install a missing Chromium browser binary after dependencies exist.
cd web && bunx playwright install chromium
```

Bun may not be installed in some construction or CI-like environments. Native JavaScript execution is optional for skill use; future agents should run the targeted checks only when Bun and dependencies are present.

## Test type selection

- Use Jest/React Testing Library for component behavior, forms, hooks, parsers, frontend utility functions, SWR state handling, and UI error/loading states.
- Use Playwright for multi-service behavior, auth/role flows, browser-only interactions, route/chrome behavior, visual regression, and frontend/backend integration through `/api`.
- Use pure Jest unit tests for deterministic utilities such as packet parsing, markdown URL sanitation, path sanitization, and small data transforms.
- Avoid full Playwright suites unless the task truly needs broad regression coverage; targeted specs are preferred.

Useful native candidates when Bun is available include chat packet processing, Craft `parsePacket`, MinimalMarkdown sanitation, Craft store/queue behavior, and admin table/modal flows. Do not copy existing tests into skills; adapt their patterns to the new change.

## Jest and React Testing Library rules

Jest tests are co-located with source files and use the projects in `web/jest.config.js`:

- `*.test.ts` pure unit tests run in Node where possible.
- `*.test.tsx` React integration tests run in jsdom.
- E2E tests under `web/tests/e2e/**` are ignored by Jest.

Use the shared test utilities:

```tsx
import { render, screen, setupUser, waitFor } from "@tests/setup/test-utils";
```

Required patterns:

- Always use `setupUser()` instead of `userEvent.setup()`. It wraps interactions in React `act()`.
- Use the custom `render()` from `@tests/setup/test-utils`; it provides isolated SWR cache and tooltip context.
- Prefer user-visible queries in this order: role, label, placeholder, text. Avoid `getByTestId` unless no accessible query fits. Do not assert on CSS classes for behavior.
- After triggering async state, use `findBy*`, `waitFor`, or `waitForElementToBeRemoved` before asserting.
- Test user-visible behavior and integration points, not component internals or hook implementation details.
- Mock only external boundaries: `fetch`, Next navigation, and problematic third-party packages. Do not mock the app code being tested.
- Restore spies in `afterEach` or at the end of the test.

### Fetch mocking convention

Sequential fetch mocks must document their endpoint with comments. This avoids confusing mock order when a component reads, writes, then refreshes.

```tsx
const user = setupUser();
const fetchSpy = jest.spyOn(global, "fetch");

// Mock GET /api/admin/widgets
fetchSpy.mockResolvedValueOnce({
  ok: true,
  json: async () => ({ widgets: [] }),
} as Response);

// Mock POST /api/admin/widgets
fetchSpy.mockResolvedValueOnce({
  ok: true,
  json: async () => ({ id: 1, name: "New widget" }),
} as Response);

render(<WidgetForm />);
await user.click(screen.getByRole("button", { name: /create/i }));

await waitFor(() => {
  expect(fetchSpy).toHaveBeenCalledWith(
    "/api/admin/widgets",
    expect.objectContaining({ method: "POST" })
  );
});
```

If testing SWR hooks, supply `swrConfig.fallback` to the custom render or mock `fetch` before rendering. Keep endpoint URLs relative to `/api/...`.

## Playwright prerequisites

Playwright E2E expects the app stack to be running. In local development, run the frontend on `http://localhost:3000` and the backend behind it. The browser and tests should use the frontend origin for both UI and API calls.

Readiness check:

```bash
curl -s -o /dev/null -w '%{http_code}\n' http://localhost:3000/api/auth/type
```

A healthy local stack should return `200`. If it does not, debug frontend dev server, backend server, and proxy settings before investigating the spec.

Playwright global setup:

- Polls the configured base URL for readiness.
- Registers known users idempotently. The first registered user becomes admin in a fresh database.
- Logs in through API and writes storage states in the `web/` working directory.
- Creates admin, admin2, and worker user states.
- Ensures a public LLM provider exists when possible.

Known credentials used by setup:

- Admin: `admin_user@example.com` / `TestPassword123!`
- Admin2: `admin2_user@example.com` / `TestPassword123!`
- Worker pool: `worker0@example.com` through `worker7@example.com` / `WorkerPassword123!`

Most specs start pre-authenticated as admin through `admin_auth.json`. Use API login helpers for user switches; do not drive the login UI unless the login flow itself is under test.

## Playwright hard rules

### Page Object Model

All locators and surface interactions belong in a Page Object class, not inline in a spec. Existing feature POMs may live near their specs; new shared page objects should live under `tests/e2e/pages/`.

Specs should read like user behavior:

```ts
const chatPage = new ChatPage(page);
await chatPage.goto();
await chatPage.inputBar.fill("hello");
await chatPage.inputBar.send();
await chatPage.expectHumanMessage("hello");
```

Locator priority inside page objects:

1. `data-testid` or `aria-label` with `getByTestId` / `getByLabel`.
2. Role-based locators with `getByRole`.
3. Visible text or label locators.
4. CSS selectors only as a last resort.

### Auto-retrying assertions

Use Playwright's auto-retrying matchers because locator assertions retry until stable:

- `await expect(locator).toHaveAttribute(name, value)`
- `await expect(locator).toHaveClass(/selected/)`
- `await expect(locator).toContainText("...")`
- `await expect(locator).toHaveCount(n)`
- `await expect(locator).toBeVisible()` / `toBeHidden()`
- `await expect(locator).toHaveValue(value)`

Do not base async assertions on one-shot snapshots such as `getAttribute()`, `textContent()`, `count()`, `inputValue()`, `isVisible()`, or `page.evaluate()`. Use `expect.poll()` only when no locator matcher exists, such as computed height or scroll metrics.

### Waiting and flake control

- No `waitForTimeout()` in specs.
- Use `waitForResponse`, locator `.waitFor()`, `page.waitForLoadState("networkidle")` after navigation, or `expect.poll()` for non-DOM state.
- Keep tests parallel-safe. No shared mutable state between workers.
- Tests that create visible app state should use `loginAsWorkerUser(page, testInfo.workerIndex)` and clean up resources in `afterAll`.
- Use `admin2` for admin-capable state mutations that should not contaminate the primary admin session.
- Prefer API setup/teardown through `OnyxApiClient`; reserve UI interactions for behavior under test.
- Use deterministic names and clean up by ID. Fall back to timestamps only when deterministic cleanup cannot prevent collisions.
- Add useful error context when a helper fails.
- Tag serial/slow tests with `@exclusive`.

## Visual regression

Visual helpers capture screenshots by default and assert only when `VISUAL_REGRESSION=true`.

- Use `expectScreenshot(page, { name, mask, hide, fullPage })` for page screenshots.
- Use `expectElementScreenshot(locator, { name, mask, hide })` for component or region screenshots.
- The helpers wait for visible images and CSS animations to settle.
- Use masks/hide selectors for dynamic text, timestamps, avatars, toasts, and ephemeral overlays.
- To test both themes, loop over `THEMES` and call `setThemeBeforeNavigation(page, theme)` before `page.goto()`.
- Playwright output is under `web/output/playwright/`; capture-only screenshots are under `web/output/screenshots/`.

If the optional Onyx devtools CLI is installed, screenshot comparison can be run with `ods screenshot-diff compare --project admin`; route CLI installation or deployment issues to cli-deployment-devtools.

## Auth and environment notes

- The Playwright config reads `.vscode/.env` if present and skips it silently for most tests.
- Some OAuth-specific specs require provider-specific environment variables and may fail at import time if run as part of a broad suite without those values. Scope runs to the relevant file or directory when secrets are absent.
- Playwright tests can reset or mutate application state. Do not run them against data you want to preserve.
- Browser binary errors are fixed by installing the required browser after dependencies are installed.
- Always call API setup through `http://localhost:3000/api/...` or relative `/api/...`, not backend `:8080`.

## Minimal verification matrix

For a typical frontend change, prefer one of these:

- Pure utility/parser change: targeted Jest unit test plus `bun run test -- <file>`.
- Component/form change: targeted RTL test using role/label queries plus `bun run test -- <file>`.
- Admin page with API mutations: RTL for form state and a targeted Playwright spec only if auth/browser integration is the risk.
- Chat/Craft streaming UI: Jest for packet/store/rendering logic; Playwright only for end-to-end browser streaming or screenshots with services.
- Route/proxy/auth behavior: targeted Playwright or manual curl through the frontend origin, plus logs if a backend service is involved.
