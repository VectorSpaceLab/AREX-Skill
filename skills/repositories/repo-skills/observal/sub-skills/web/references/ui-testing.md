# UI Testing and Verification

This reference gives the safe verification path for web changes: static contract checks, type/lint/build, route and API smoke checks, then Playwright/E2E and screenshots when the UI changed.

## 1) Run the bundled static contract helper first

Use the bundled helper before expensive work or when you want a quick structural sanity check.

```bash
python skills/disco/observal/sub-skills/web/scripts/check_web_contract.py --repo-root .
```

Expected signal:

- `PASS` lines for package scripts, route file presence, `use-api` barrel, harness hook, and OKLCH token file
- exit code `0` on success
- a concise `FAIL` line and non-zero exit code if a required frontend contract is missing

What it checks:

- `web/package.json` scripts and package identity
- route file presence and TanStack Router markers
- `web/src/hooks/use-api.ts` barrel presence and exported domain hook modules
- `web/src/lib/api.ts` / `web/src/hooks/use-harnesses.ts` harness-data contract markers
- `web/src/app.css` presence of semantic OKLCH token definitions

## 2) Fast local checks

Run these from the repo root unless you deliberately want to work inside `web/`.

| Command | Use when | Expected signal |
|---|---|---|
| `pnpm e2e:list` | You want to confirm the installed Playwright test inventory | Lists tests without launching the browser stack |
| `pnpm --filter web typecheck` | Type-only validation after API/type changes | Exit `0` and no TypeScript diagnostics |
| `pnpm --filter web lint` | You touched hooks, route modules, or components | Exit `0`; address new errors before handoff |
| `pnpm --filter web build` | You want the full frontend compile/bundle proof | `tsc --noEmit` succeeds, then Vite build succeeds |
| `pnpm --filter web dev` | You need local browser debugging | Vite serves on `http://localhost:3000` |
| `pnpm --filter web e2e` | You changed UI behavior that needs browser coverage | Playwright runs against the local dev server or CI stack |
| `pnpm --filter web e2e:kiro` | You changed harness-specific trace flows | Only Kiro-marked tests execute |
| `pnpm --filter web e2e:ui` | You need interactive Playwright debugging | Playwright UI opens instead of headless execution |

If you are already inside `web/`, the package scripts are the same without the `--filter web` prefix.

## 3) When screenshots are required

Any change to a user-visible frontend surface should carry screenshot proof when the UI meaningfully changes. The README-visible surfaces that most often require screenshots are:

- Registry home and agent/component cards
- Agent builder and preview panel
- Component edit forms and version dropdowns
- Review queue and review diff dialogs
- Session trace detail and span tree
- Insight reports
- Leaderboard
- Audit log

### Targeted screenshot specs

| Surface | Playwright spec | Common use |
|---|---|---|
| Component edit form/detail | `tests/e2e/component-edit-screenshots.spec.ts` | Editing tabs, version dropdowns, detail form states |
| Review diff dialog | `tests/e2e/review-diff-screenshots.spec.ts` | Approve/reject dialogs and diff rendering |

These specs are useful when you need deterministic before/after images for a PR or when changing layout, spacing, theme tokens, or conditional rendering.

### General screenshot guidance

- Capture the exact state that changed: loading, empty, error, authenticated/unauthenticated, selected tab, open dropdown, diff open, etc.
- Use a fixed viewport when you need repeatable imagery.
- Verify the page has finished its network work before shooting.
- Prefer the smallest targeted screenshot spec over a full-suite run when only one surface changed.

## 4) Verification order for common web changes

### Route/page/component change

1. Run the static helper.
2. Run `pnpm --filter web typecheck`.
3. Run `pnpm --filter web build` if the change affects routes, imports, or styling.
4. Run a targeted Playwright spec or the specific E2E flow that touches the page.
5. Add screenshots if the UI changed in a visible way.

### API/hook/type change

1. Update the typed client in `web/src/lib/api.ts`.
2. Update the shared type file in `web/src/lib/types/*.ts`.
3. Update the hook module and `web/src/hooks/use-api.ts` if the hook is reusable.
4. Run the static helper.
5. Run `pnpm --filter web typecheck`.
6. Run the focused Playwright flow that depends on the response shape.

### Theme/token change

1. Update `web/src/app.css` and any theme-specific token blocks.
2. Check the affected surface in both light and dark/system modes.
3. Run screenshots on at least one representative page.
4. Run `pnpm --filter web build` to ensure Tailwind/TSC still compile.

### Auth/session change

1. Verify token storage behavior in `web/src/lib/api.ts` and `web/src/hooks/use-auth.ts`.
2. Test the login/new-tab refresh path and a rejected-refresh path.
3. Run the affected auth E2E flow.
4. Confirm the user returns to `/login` with the expected `next` behavior only when refresh is truly rejected.

## 5) Playwright environment facts

`web/playwright.config.ts` sets:

- local base URL: `http://localhost:3000`
- CI base URL: `http://localhost:80`
- local web server: `pnpm dev`
- retries: `1`
- screenshots: only on failure by default
- trace capture: retained on failure

If Playwright cannot see the app:

- check that the correct base URL is active for the environment
- check that the Vite dev server is running locally, or the Docker stack is up in CI
- check that the API server is reachable through the proxy/stack before blaming the UI code

## 6) Synthetic usability cases this skill must cover

### A. Server-driven harness data on a registry page

Validate that a registry surface:

- reads harness display data from the server, not a hardcoded list
- uses `useHarnesses()` or a hook over `config.harnesses()`
- keeps default harness handling server-driven
- passes typecheck/build after the new query hook and page wiring
- renders the expected badges/labels in a screenshot or browser check

### B. Auth refresh and stale-session recovery

Validate that the frontend:

- restores an access token from a refresh token in a new tab
- does not destroy a session during a transient network error
- clears the session and redirects only when refresh is actually rejected
- updates the sidebar/nav state after profile data changes

These are the most likely web-only regressions that can look like API or harness failures if they are not tested directly.
