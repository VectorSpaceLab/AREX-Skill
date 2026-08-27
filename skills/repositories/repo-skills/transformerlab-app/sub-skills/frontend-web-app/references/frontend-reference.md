# Frontend Web App Reference

This reference distills the frontend, auth, task/job UI, and smoke-test evidence into operating guidance for future work on Transformer Lab's web interface.

## Runtime Model

- The UI is a React 18 + TypeScript web app served by webpack. The browser entry creates a React root, wraps the app in an `easy-peasy` `StoreProvider`, and uses `HashRouter` from `react-router-dom`.
- Electron has been removed. Do not add Electron dependencies, `ipcRenderer`, `ipcMain`, `BrowserWindow`, preload scripts, or main-process assumptions.
- The app shell wraps content in Joy's `CssVarsProvider` and `CssBaseline`, then layers providers in this order: notifications, auth, analytics, experiment info, and the main routed content.
- Development uses the frontend dev server on port `1212` and the API on port `8338`. The API base helper maps localhost or port `1212` to `8338` and preserves path-prefix deployments because HashRouter keeps `window.location.pathname` stable.
- Use Node v22 for frontend development even though package metadata may be broader. Avoid v23+ unless project maintainers explicitly update support.

## Routing

Routes are defined in `src/renderer/components/MainAppPanel.tsx`; the router itself is installed in `src/renderer/index.tsx`.

Important route shapes:

| Route | Screen / purpose |
| --- | --- |
| `/` | Welcome/home page |
| `/experiment/:experimentName` | Experiment layout that syncs `:experimentName` into experiment context |
| `/experiment/:experimentName/notes` | Experiment notes |
| `/experiment/:experimentName/tasks` | Task templates and jobs |
| `/experiment/:experimentName/evals` | Evaluation page |
| `/experiment/:experimentName/interactive` | Interactive task/job page |
| `/experiment/:experimentName/documents` | Documents |
| `/experiment/:experimentName/settings` | Experiment settings |
| `/experiment/:experimentName/jobs/:jobId` | Job detail page |
| `/experiment/:experimentName/tasks/:taskId/runs` | Task run history |
| `/cli-auth` | CLI auth handoff page |
| `/api`, `/zoo`, `/zoo/registry`, `/zoo/registry/:groupId` | API and model registry screens |
| `/data`, `/data/registry`, `/data/registry/:groupId` | Dataset screens |
| `/tasks-gallery`, `/compute`, `/settings` | Global screens |
| `/user/*`, `/team`, `/team/usage-report` | User and team screens |

Route rules:

- URLs are hash-based (`/#/...`). Use `navigate('/experiment/...')`, `RouterLink`, or Joy `component={RouterLink}` with app-relative paths.
- Do not replace `HashRouter` with browser routing unless the API-base and reverse-proxy path-prefix behavior is redesigned.
- When adding an experiment-scoped route, make sure `ExperimentLayout` or equivalent context synchronization keeps `ExperimentInfoContext` current.
- For job deep links, preserve the pattern `/experiment/${experimentInfo.id}/jobs/${jobId}` and pass a `state.from` path when returning to a list view is useful.

## UI Component Conventions

The UI library is MUI Joy, not MUI Material.

Use:

```tsx
import { Button, FormControl, FormLabel, Input, Modal, ModalDialog, Sheet, Stack, Typography } from '@mui/joy';
import { PlayIcon } from 'lucide-react';
```

Avoid:

```tsx
import Button from '@mui/material/Button';
import { PlayArrow } from '@mui/icons-material';
```

Patterns to follow:

- Functional components with typed props and hooks.
- Joy layout primitives (`Sheet`, `Stack`, `Box`, `Card`) and `sx` styling.
- Joy forms: `FormControl`, `FormLabel`, `Input`, `Select`, `Option`, `Textarea`, `Switch`, `Checkbox`, `RadioGroup`.
- Joy modal shape: `Modal` -> `ModalDialog` -> optional `ModalClose`, `DialogTitle`, `DialogContent`, `DialogActions`.
- `lucide-react` icons for buttons, menus, alerts, and navigation affordances.
- Local `useState` for form fields and modal visibility; React context for auth, experiment, analytics, and notifications; `easy-peasy` only where neighboring code already uses the store.
- Prefer strict interfaces for new props and response shapes. Legacy files use `any` in places; do not expand that habit unless integration with existing untyped data makes it unavoidable.

## Auth, Team Context, and Data Access

`src/renderer/lib/authContext.ts` is the canonical frontend auth layer.

Key facts:

- Login posts form data to the JWT login endpoint with `credentials: 'include'`, letting the server set auth cookies.
- `fetchWithAuth(url, options)` resolves relative/full API URLs, sends cookies, adds `X-Team-Id` and `X-Team-Name` when a team is selected, and retries once after a `401` by using the refresh endpoint.
- Refresh is singleton-protected so simultaneous `401` responses share one refresh attempt.
- Team selection is cached per user, stored in local storage, mirrored in a `tlab_team_id` cookie for non-fetch requests, and changing teams triggers a full app reload to reset state.
- Health checks avoid extra team headers so they can stay lightweight and avoid unnecessary CORS preflights.

Preferred read patterns:

```tsx
import { useSWRWithAuth as useSWR, useAPI, useAuth } from 'renderer/lib/authContext';
import * as chatAPI from 'renderer/lib/transformerlab-api-sdk';
import { fetcher } from 'renderer/lib/transformerlab-api-sdk';

const { team, fetchWithAuth } = useAuth();
const { data, isLoading, isError, mutate } = useSWR(
  experimentId ? chatAPI.Endpoints.Task.List(experimentId) : null,
  fetcher,
  { refreshInterval: 10000, revalidateOnFocus: false },
);

const { data: providers } = useAPI('compute_provider', ['list'], {
  teamId: team?.id ?? null,
});
```

Mutation pattern:

```tsx
const response = await fetchWithAuth(chatAPI.Endpoints.Jobs.UpdateJobData(experimentId, jobId), {
  method: 'PUT',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ updates: { favorite: nextValue } }),
});

if (response.ok) await mutate();
```

Data-access rules:

- Use `useSWRWithAuth` from `authContext.ts`; this version did not contain a standalone `src/renderer/lib/swr.ts` file.
- Use the shared `fetcher` for JSON reads when the default response handling is sufficient.
- Use `useAPI` for endpoints declared in `api-client/allEndpoints.json` and resolved by `getPath`/`getAPIFullPath`.
- Use `fetchWithAuth` or `chatAPI.authenticatedFetch` for `POST`, `PUT`, `PATCH`, and `DELETE` calls.
- Use a `null` SWR key until required IDs, team context, or modal-open state are ready. This prevents unauthenticated or malformed requests.
- After a mutation, call the relevant SWR `mutate`; for optimistic UI updates, pass `{ revalidate: false }`, then roll back on failure.
- If adding a new stable endpoint helper, add it to `src/renderer/lib/api-client/endpoints.ts`, URL-encode path/query values, and consume it through `renderer/lib/transformerlab-api-sdk` exports.
- Do not bypass `fetchWithAuth` for protected endpoints; direct `fetch` is appropriate only for explicitly unauthenticated or special health/auth bootstrap calls.

Common endpoint families already used by task/job screens:

- `Endpoints.Task.List`, `ListBySubtypeInExperiment`, `GetByID`, `CreateTemplate`, `UpdateTemplate`, `DeleteTemplate`, gallery/team-gallery helpers, YAML/file helpers.
- `Endpoints.ComputeProvider.List`, `LaunchTemplate`, `CheckSweepStatus`, `StopCluster`, setup/check/debug helpers.
- `Endpoints.Jobs.List`, `ListWithFilters`, `Get`, `Delete`, `Stop`, `Update`, `UpdateJobData`, `Metrics`.
- `Endpoints.Experiment.GetTasksOutputFromJob`, `GetProviderLogs`, `GetRequestLogs`, `GetTunnelInfo`, artifact/eval/sweep result helpers.

## Task and Job UI Screens

Primary screens and components:

- `Tasks.tsx`: owns the task template list, jobs panel, modal state, queue flow, job mutations, and polling.
- `TaskTemplateList`: renders reusable task templates and queue/edit/delete/export controls.
- `QueueTaskModal`: lets users select a compute provider and override parameters/resources/tracking/profiling/sweeps before launch.
- `JobsPanel` and `JobsList`: render searchable jobs, job actions, artifacts, outputs, favorites/hidden/discard controls, and compare-eval selection.
- `JobProgress`: renders status chips, progress bars, stop controls, live status, launch progress, sweep progress, and terminal-completion details.
- `ViewOutputModalStreaming` and `EmbeddableStreamingOutput`: render Lab SDK output, provider machine logs, and orchestration logs.
- `PollingOutputTerminal`: polls task output and writes it to xterm.js.

Polling behavior to preserve:

- Remote jobs: SWR refresh every ~3 seconds, revalidate on reconnect, poll while hidden, do not poll while offline.
- Sweep status: SWR refresh every ~10 seconds via the sweep-status endpoint.
- Templates: SWR refresh every ~10 seconds; explicit `mutate` after create/edit/delete is still required.
- Output terminal: active jobs refresh faster than idle/completed jobs. Provider logs have separate active/idle intervals.

Queue flow:

1. `handleQueue` refreshes the latest task by ID before opening the modal so YAML edits do not launch stale config.
2. The modal preloads models, datasets, provider list, local provider details, provider resource groups, and provider-specific settings only when needed.
3. Parameter definitions support shorthand values and schema values with `type`, `default`, `min`, `max`, `step`, `options`, `enum`, `ui_widget`, `title`, and `required`.
4. `ui_widget` supports task-specific controls such as model/dataset select, slider/range, switch, radio, password, and JSON-object editing.
5. Resource fields (`cpus`, `memory`, `disk_space`, `accelerators`, `num_nodes`, `minutes_requested`) are authoritative for the run. Empty strings become `null` to intentionally clear a template requirement; `undefined` means fall back to the template.
6. Provider-specific options include SLURM custom sbatch flags, SkyPilot Docker image/region/spot, dstack fleet name, RunPod image, Trackio, profiling, and sweeps.
7. `handleQueueSubmit` strips modal-only fields, sends parameter overrides as `config`, and posts to `Endpoints.ComputeProvider.LaunchTemplate(providerId)`.
8. On launch success, it adds the new job ID to a per-experiment pending placeholder list, mutates jobs/templates, and closes the modal.

Job status display:

- UI-visible statuses include `NOT_STARTED`, `QUEUED`, `WAITING`, `LAUNCHING`, `INTERACTIVE`, `RUNNING`, `STOPPING`, `COMPLETE`, `STOPPED`, `FAILED`, `CANCELLED`, `DELETED`, and `UNAUTHORIZED`.
- Terminal statuses safe for record deletion are `COMPLETE`, `STOPPED`, `FAILED`, `CANCELLED`, `DELETED`, and `UNAUTHORIZED`; queued-but-never-dispatched records may also be removable.
- `STOPPING` and optimistic `job_data.stop_requested` are both treated as stop-pending in UI controls.
- `job_data.launch_progress` drives progress bars/messages for launch phases.
- Sweep parent jobs show aggregate complete/running/failed counts and sweep progress instead of ordinary single-job progress.

For exact provider execution, lifecycle ownership, and backend state transitions, route to [task-execution-compute](../../task-execution-compute/SKILL.md).

## Log and Terminal Rendering

- Lab SDK output tab uses `Endpoints.Experiment.GetTasksOutputFromJob` through `PollingOutputTerminal`.
- Machine Logs tab uses `Endpoints.Experiment.GetProviderLogs(experimentId, jobId, tailLines, live)`.
- Orchestration Logs tab uses `Endpoints.Experiment.GetRequestLogs` and only appears when a provider launch request ID exists.
- xterm.js output is not ordinary DOM text. Visual checks can inspect the terminal, but automated assertions should poll the corresponding API endpoint and check returned JSON/text.
- Live provider logs may disappear after remote resources stop; persistent provider logs should be checked with `live=false` when asserting completed jobs.

## Difficult Frontend Cases

### Endpoint-backed modal with authenticated fetch

When adding a modal that reads and mutates backend data:

1. Define a narrow props interface (`open`, `onClose`, required IDs, and callbacks such as `onSaved`).
2. Gate reads with `open && requiredId ? endpoint : null`.
3. Add an `Endpoints` helper for any new URL and URL-encode dynamic values.
4. Use `useSWRWithAuth` or shared `fetcher` for reads and `fetchWithAuth` for the mutation.
5. Disable submit while saving, parse non-OK response text/JSON into a user-facing notification, and revalidate parent SWR keys on success.
6. If the call is team-scoped, do not manually assemble `X-Team-Id`; get `fetchWithAuth` from `useAuth()` and wait for `team?.id` before firing team-dependent reads.

### Terminal log assertion by API polling

When validating output or provider logs:

1. Let the UI render and open the output modal for the target job.
2. Extract or carry the job ID from the job row/modal title/state.
3. Poll `provider_logs` or task-output endpoints with the experiment ID and job ID.
4. Assert the returned payload contains the expected content. Do not assert on xterm.js DOM text.

## Frontend Change Checklist

Before finishing a frontend change:

- No `@mui/material`, `@mui/icons-material`, Electron, or IPC imports were introduced.
- Routes remain hash-router compatible and experiment-scoped routes keep experiment context in sync.
- Protected calls use `fetchWithAuth`, `useSWRWithAuth`, `useAPI`, or `authenticatedFetch`.
- Mutations revalidate or optimistically update affected SWR caches.
- New components use typed props and Joy/lucide conventions.
- Task/job changes preserve pending placeholders, stale-task refresh before queueing, resource-clear semantics, and terminal-log caveats.
- Formatting and the appropriate verification steps from [Verification](verification.md) were run or explicitly deferred.
