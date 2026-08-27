# Frontend Troubleshooting

Use this reference when a Transformer Lab frontend change fails to build, authenticate, route, refresh data, or verify visually.

## Fast Checks

Run these inspections before deeper debugging:

```bash
rg "@mui/material|@mui/icons-material|electron|ipcRenderer|ipcMain|BrowserWindow" src package.json
rg "useSWRWithAuth|fetchWithAuth|authenticatedFetch|Endpoints\." src/renderer
node -v
npm run format:check
```

Expected:

- No Material UI, MUI icons, Electron, or IPC imports in frontend source.
- Protected frontend calls go through `fetchWithAuth`, `authenticatedFetch`, `useSWRWithAuth`, `useAPI`, or shared endpoint helpers.
- Node is v22 for supported local development.

## Symptom Matrix

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Build fails after adding `@mui/material` import | Project uses Joy UI, not Material UI | Replace with `@mui/joy` components and adjust API/props; use `sx` styling and Joy modal/form primitives |
| Icons fail to resolve | MUI icons package is not installed | Use `lucide-react` icons instead |
| New code references Electron, IPC, preload, or main process | App is now a pure browser app | Replace with browser-safe React code and authenticated API endpoints |
| Authenticated request returns `401` | Bypassed `fetchWithAuth`, expired cookie refresh failed, or request fired before auth initialized | Use `fetchWithAuth`/`useSWRWithAuth`; gate SWR key on required state; let refresh retry happen automatically |
| Protected endpoint returns team-related `400` | No team context or team header/cookie | Wait for `team?.id`; use `fetchWithAuth` so `X-Team-Id`/`X-Team-Name` are attached; avoid direct `fetch` for protected endpoints |
| Data is stale after create/update/delete | SWR cache not revalidated | Call the relevant `mutate`; for optimistic updates, use `{ revalidate: false }` then roll back on failure |
| SWR fetch fires with `undefined` IDs | Key not null-gated | Use `id ? endpoint(id) : null`, and include `open` state for modal-only reads |
| API URL is wrong behind a path prefix | HashRouter/path-prefix assumptions were broken or URL was hand-built | Use `API_URL`, `getAPIFullPath`, or `Endpoints` helpers; keep HashRouter semantics intact |
| Frontend connects to wrong port in dev | API/frontend port mismatch | Frontend dev server is `1212`; API is `8338`; on localhost the API-base helper maps frontend origin to `8338` |
| `npm start` or app boot fails with port errors | Existing process owns port `1212` or `8338` | Run `npm run check-ports`, stop the conflicting process, then restart |
| Node/tooling errors differ from CI/dev docs | Unsupported Node version | Switch to Node v22; avoid v23+ unless maintainers update the support contract |
| Queue modal launches stale task data | Modal opened from cached task list after YAML edit | Refresh latest task by ID before opening queue modal; keep the existing `handleQueue` pattern |
| Clearing a resource field does not remove requirement | Empty value was omitted instead of sent as `null` | Preserve QueueTaskModal semantics: `null` means intentional clear; `undefined` means fall back to template |
| Provider dropdown is empty | Team-scoped provider list did not load or team context missing | Fetch providers with `useAPI('compute_provider', ['list'], { teamId: team?.id ?? null })`; show loading/empty state |
| Job row does not update after launch | Missing pending placeholder or jobs mutate | Add returned job ID to pending IDs and call jobs/templates `mutate` after launch |
| Job stop button stays enabled while stopping | UI did not account for optimistic stop state | Treat `status === 'STOPPING'` and `job_data.stop_requested` as stop-pending |
| Terminal text cannot be selected/asserted in tests | xterm.js renders outside normal text DOM | Validate log contents by polling output/provider-log/request-log API endpoints |
| Provider logs disappear for a remote completed job | Live logs were fetched from a stopped remote machine | Use persisted provider logs with `live=false` for completed-job assertions |
| E2E selectors hit old jobs/tasks | Prior test runs leave data behind | Use unique suffixes, role/text selectors, and `.first()` where duplicate rows are expected |
| Smoke navigation passes but a modal is visually broken | No visual check covered the modal state | Start the app and inspect the specific modal with agent-browser; do not rely only on page-load smoke |

## Auth and Team Debugging

Checklist:

1. Is the component under `AuthProvider`? Most app screens are; standalone public/share or invite flows may differ.
2. Is the user known? `useAuth()` exposes `user`, `isAuthenticated`, `initializing`, and `userIsLoading`.
3. Is a team selected? Team-dependent requests should wait for `team?.id`.
4. Is the request protected? If yes, use `fetchWithAuth` or hooks built on it.
5. Did a `401` happen? `fetchWithAuth` should refresh once. If refresh fails, the user is logged out and team state is cleared.
6. Did team selection change? A full reload is expected so state from the old team does not leak into the new team.

Common repair:

```tsx
const { team, fetchWithAuth } = useAuth();
const key = open && team?.id && experimentId ? Endpoints.Some.List(experimentId) : null;
const { data, mutate } = useSWR(key, fetcher, { revalidateOnFocus: false });
```

## SWR and Mutation Debugging

When the UI does not update:

- Confirm the component consumes the same key that is mutated.
- Confirm `mutate()` is awaited when subsequent UI depends on fresh data.
- For optimistic updates, make sure rollback restores the previous value on request failure.
- Avoid creating a new but semantically different endpoint string for the same data; SWR keys must match.
- Set `revalidateOnFocus`, `revalidateOnReconnect`, `refreshInterval`, `refreshWhenHidden`, and `refreshWhenOffline` intentionally. Job status screens poll more aggressively than template lists.

## Queue Task Modal Debugging

Common failure points:

- **No provider selected:** keep submit disabled and show a warning before launch.
- **Provider no longer exists:** after queue modal opens, validate the selected provider still exists before launch.
- **Parameter validation:** schema `min`/`max` should produce visible validation errors before submit.
- **Model/dataset selectors:** `lab_model_select` and `lab_dataset_select` need models/datasets loaded while the modal is open; allow custom strings when the user checks the custom option.
- **Provider-specific fields:** only send SLURM flags, SkyPilot overrides, dstack fleet, RunPod image, Trackio, profiling, and sweep fields when relevant and enabled.
- **Stale template:** fetch the latest task snapshot before opening the modal.
- **Resource clearing:** keep `null` values in launch payload when users clear resource fields.

For backend launch semantics, provider-specific errors, and job lifecycle behavior, route to [task-execution-compute](../../task-execution-compute/SKILL.md).

## Route and Browser Debugging

- HashRouter routes appear after `/#/`. If a deep route is blank, confirm the path exists in `MainAppPanel` and that the parent experiment route has an `Outlet` when nested.
- If a direct browser URL works locally but fails behind a reverse proxy, check any code that changed API-base derivation or replaced hash routing.
- If login redirects to the wrong page, inspect `redirectAfterLogin` usage and avoid persisting stale deep links across explicit logout.
- If a public/share or invite page is affected, remember those flows bypass the normal authenticated main-shell rendering.

## Terminal and Job Log Debugging

- Lab SDK Output polls task output; Machine Logs poll provider logs; Orchestration Logs fetch request logs.
- Active statuses (`RUNNING`, `LAUNCHING`, `INTERACTIVE`, `WAITING`, `QUEUED`, `STOPPING`) refresh more frequently than idle statuses.
- xterm containers are for display. For assertions, call the corresponding endpoint and inspect returned payload:
  - task output for Lab SDK output,
  - provider logs for Machine Logs,
  - request logs for Orchestration Logs.
- If provider logs are empty for a local job, the job may still be setting up or may not have written output. If provider logs are empty for remote, try persisted logs after completion or live logs while the machine is still running.

## Formatting and Verification Failures

- If `npm run format:check` fails, run `npm run format` and review the diff.
- If the app cannot start, check Node version and port conflicts before editing application code.
- If visual verification shows broken layout, fix the UI before handing off; do not substitute Playwright if the issue is visibly present.
- If Playwright is explicitly requested and fails on selectors, inspect the live DOM/snapshot first, prefer role/text/placeholder selectors, and use `.first()` for duplicate historical rows.
