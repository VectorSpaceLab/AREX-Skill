# Frontend Verification

Use this reference to choose the smallest reliable verification for Transformer Lab frontend changes. Prefer direct visual inspection with the browser automation workflow for UI changes; use Playwright only when the user asks for E2E work or when you intentionally modify the E2E suite.

## Environment and Commands

Use Node v22 for frontend work.

| Purpose | Command |
| --- | --- |
| Install frontend dependencies | `npm install` |
| Start frontend dev server | `npm start` |
| Start frontend + API together | `npm run dev` |
| Check ports before combined dev | `npm run check-ports` |
| Format changed frontend files | `npm run format` |
| Dry-run formatter | `npm run format:check` |
| Optional React diagnostics | `npm run doctor` |
| Start test container/app for browser checks | `npm run docker-test:up` |
| Stop test container/app | `npm run docker-test:down` |

Notes:

- `npm start` serves the web UI on port `1212`; the API is expected on port `8338`.
- `npm run dev` checks ports, then runs frontend and API together.
- Always run `npm run format` after changing frontend source files before commit or handoff. Use `format:check` when a dry-run is required.
- There is no configured frontend unit-test framework in this version; frontend behavior is covered with browser/E2E workflows.

## Default Visual Verification: Agent Browser

For UI layout and interaction changes, do not write new Playwright specs or run the whole Playwright suite unless the user explicitly asks. Use the agent-browser workflow instead.

Suggested visual check:

1. Start the app, usually with `npm run docker-test:up` for a self-contained environment or `npm run dev` for local iteration.
2. Navigate in a browser to the app root. The API-served app is normally available on port `8338`; the dev server is on port `1212`.
3. Log in with the seeded development credentials when needed: `admin@example.com` / `admin123`.
4. Visit every page directly affected by the change and one adjacent page that shares layout or context.
5. Capture a screenshot or snapshot and inspect for broken layout, missing controls, console-visible errors, and auth/team state problems.
6. If the page includes task/job output terminals, visually inspect them for layout only; validate terminal text through API polling if an assertion is needed.

Use lower-level browser/devtools access only when you specifically need console evaluation, network inspection, or performance tracing.

## Optional Playwright/E2E Guidance

Use this section only when the user asks for Playwright tests, when you edit the E2E suite, or when a specific frontend change cannot be verified confidently by visual inspection and API checks.

Evidence-backed E2E conventions:

- The base URL is the API-served app at `http://localhost:8338`.
- The smoke project covers app title/homepage, auth endpoints, and main screen navigation before full E2E cases.
- Reuse shared login and experiment-selection helpers rather than duplicating login flows.
- Prefer selectors by role, exact text, and placeholder. Use `.first()` when duplicate historical data may exist.
- Make tests idempotent: assume prior runs left tasks, jobs, datasets, or dialogs behind.
- Use unique suffixes for created task/job names and match the specific row by that suffix.
- Queued local jobs can take minutes; use generous test timeouts and status waits.
- Fail early if a job row shows `FAILED` or `COMPLETE - 0%` when a successful run is expected.
- For xterm.js terminal content, poll the related API endpoint instead of asserting DOM text.

## Verification Recipes

### Pure component/layout change

1. Run `npm run format`.
2. Start the app.
3. Use agent-browser to log in, navigate to the changed screen, and capture/inspect the UI.
4. Check at least one adjacent screen that shares the changed shell, provider, route, or modal pattern.

### Route or navigation change

1. Run `npm run format`.
2. Verify the route path works as a hash route (`/#/...`) and preserves app-relative navigation.
3. For experiment-scoped routes, select an experiment and confirm the context-dependent controls render with the selected experiment.
4. Navigate away and back using app controls, not only direct URL entry.

### Authenticated data-fetching change

1. Confirm reads use `useSWRWithAuth`, `useAPI`, or the shared `fetcher` and return `null` keys until required IDs/team state exist.
2. Confirm mutations use `fetchWithAuth` or `authenticatedFetch`, handle non-OK responses, and call `mutate` for affected data.
3. With the app running, log in and exercise the read/mutation path.
4. If debugging via direct HTTP calls, remember protected endpoints require auth and team context; frontend code should not manually duplicate that when `fetchWithAuth` can provide it.

### Task queue modal change

1. Run `npm run format`.
2. Verify the modal opens from a task row after refreshing the latest task snapshot.
3. Check provider selection, parameter controls, resource-clear behavior, and provider-specific sections relevant to the change.
4. Queue only if the environment has an appropriate provider and the user/request permits running a job.
5. After queueing, verify the jobs list placeholder/status appears and data is revalidated.

### Job status/log UI change

1. Run `npm run format`.
2. Verify status chips/progress bars with representative statuses or existing jobs.
3. For log rendering, open the output modal and inspect tab layout.
4. For text assertions, poll the `provider_logs`, task-output, or request-log endpoint instead of reading xterm.js DOM content.

## Proposed Hard Usability Cases

These cases are useful for final repo-skill verification planning and go beyond simple smoke navigation.

1. **Authenticated endpoint-backed modal:** Add or modify a modal that fetches data only while open, requires an experiment ID and team context, submits via `fetchWithAuth`, shows success/failure notifications, and revalidates the parent SWR list without a full page reload.
2. **Terminal log assertion:** Queue or reuse a local job that writes a known string, open the output modal, switch to Machine Logs, and verify the string by polling the provider-log API with `live=false` rather than reading xterm.js DOM text.

## Handoff Checklist

Report these in a frontend handoff:

- Changed files and screens.
- Whether `npm run format` or `npm run format:check` ran.
- App startup method used, if any.
- Browser pages inspected and screenshots/snapshots taken, if any.
- Any Playwright specs run or intentionally not run.
- Known gaps such as no provider available, auth setup unavailable, or job execution intentionally skipped.
