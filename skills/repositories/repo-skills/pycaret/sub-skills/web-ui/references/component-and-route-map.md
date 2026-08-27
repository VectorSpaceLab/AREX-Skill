# Component and Route Map

## Purpose

Read this before changing React routes, pages, major layout/navigation components, experiment forms, run/trial pages, deployment screens, LLM widgets, or design-system conventions. It distills the UI structure so future agents do not need to reopen the original repository.

## App shell and routing model

`src/App.tsx` is the route table. `src/main.tsx` mounts `QueryClientProvider` and `BrowserRouter`, then renders `App`. Public routes are outside `AuthGate`; authenticated routes are nested under `<AuthGate><Layout /></AuthGate>`.

`Layout` owns the persistent sidebar, workspace context, command palette, workspace switcher, user menu, and floating `AIAdvisorWidget`. It derives workspace context from `/workspaces/:wsId`, from flat `/runs/:runId`, or from flat `/deployments/:deploymentId` by fetching the run/deployment row. Sidebar groups are Build, Models, Automation, Settings, and Account.

### Route table

| Route | Page/component | Auth | Main role |
|---|---|---:|---|
| `/setup` | `Setup` | No | First admin + workspace bootstrap. Redirects to login when already bootstrapped. |
| `/login` | `Login` | No | Sign in and set token pair in auth store. |
| `/` | `Workspaces` | Yes | Workspace list and modal create flow. |
| `/workspaces/:id` | `WorkspaceDetail` | Yes | Workspace project/data-source landing page. Note this route uses param `id`, not `wsId`. |
| `/workspaces/:wsId/home` | `WorkspaceHome` | Yes | Workspace dashboard, KPI strip, recent runs, shortcut rows. |
| `/workspaces/:wsId/projects/:projectId` | `ProjectDetail` | Yes | Project header, CSV/data sources, experiments list, New Experiment CTA. |
| `/workspaces/:wsId/projects/:projectId/experiments/new` | `NewExperiment` | Yes | End-to-end experiment wizard; creates experiment then submits a compare run. |
| `/workspaces/:wsId/projects/:projectId/experiments/:experimentId` | `ExperimentDetail` | Yes | Experiment setup summary and runs table. |
| `/runs/:runId` | `RunDetail` | Yes | Run status, live log drawer, worker/load cards, trials leaderboard, AI explain/debug, snapshot. |
| `/runs/:runId/trials/:trialId` | `TrialDetail` | Yes | Candidate model dashboard: metrics, pipeline, params, plots, predict, validation, artifact, tune/ensemble/promote. |
| `/runs/:runId/compare` | `TrialCompare` | Yes | Side-by-side trial comparison using query params `a` and `b`. |
| `/runs/:runId/model-card` | `ModelCard` | Yes | Best-trial plots/metrics grouped by diagnostics/explainability/curves/raw. |
| `/runs/:runId/forecast` | `ForecastWorkbench` | Yes | Time-series run dashboard for forecast and residual diagnostics. |
| `/workspaces/:wsId/datasets` | `AllDatasets` | Yes | Workspace-level DataSource list. |
| `/workspaces/:wsId/datasets/:dataSourceId` | `Datasets` | Yes | Dataset version history for one DataSource. |
| `/workspaces/:wsId/datasets/:dataSourceId/profile` | `DataProfile` | Yes | EDA/profile dashboard from `GET /data-sources/:id/profile`. |
| `/workspaces/:wsId/models` | `RegisteredModels` | Yes | Model registry list. |
| `/workspaces/:wsId/models/:modelId` | `RegisteredModelDetail` | Yes | Version history, approvals, status changes, deploy per version. |
| `/workspaces/:wsId/deployments` | `Deployments` | Yes | Workspace deployment list with latency/error counters. |
| `/deployments/:deploymentId` | `DeploymentDetail` | Yes | Endpoint detail, metrics, `PredictTester`, versions/rollback, prediction logs, drift reports. |
| `/workspaces/:wsId/monitoring` | `Monitoring` | Yes | Alert rules and deployment metric charts. |
| `/workspaces/:wsId/drift` | `DriftDashboard` | Yes | Drift report list and analysis. |
| `/workspaces/:wsId/lineage` | `Lineage` | Yes | Workspace lineage graph using plain SVG. |
| `/workspaces/:wsId/approvals` | `Approvals` | Yes | Governance inbox for approve/reject/execute workflows. |
| `/workspaces/:wsId/schedules` | `Schedules` | Yes | Schedule list and new schedule form. |
| `/workspaces/:wsId/templates` | `ExperimentTemplates` | Yes | Saved experiment setup/plan parameter bundles. |
| `/workspaces/:wsId/webhooks` | `Webhooks` | Yes | Outgoing webhook subscriptions. |
| `/workspaces/:wsId/secrets` | `Secrets` | Yes | Encrypted workspace secret store. |
| `/workspaces/:wsId/connections` | `Connections` | Yes | Backend connection config and tests. |
| `/workspaces/:wsId/git` | `GitRepositories` | Yes | Linked Git repositories and publish action. |
| `/workspaces/:wsId/llm` | `LLMSettings` | Yes | Workspace LLM provider settings and connection test. |
| `/workspaces/:wsId/members` | `WorkspaceMembers` | Yes | Members, invites, role updates, removal. |
| `/workspaces/:wsId/admin` | `AdminWorkspace` | Yes | Workspace admin hub. |
| `/workspaces/:wsId/admin/integrations` | `AdminIntegrations` | Yes | Integrations hub linking LLM, webhooks, Git, connections. |
| `/workspaces/:wsId/projects/:projectId/notebooks` | `Notebooks` | Yes | Notebook list and Jupyter session launcher placeholder/runtime. |
| `/workspaces/:wsId/projects/:projectId/analyses` | `Analyses` | Yes | Statistical analysis list, quick-run, saved analysis runs. |
| `/account/api-keys` | `ApiKeysScreen` | Yes | Personal API keys. |
| `/admin/audit` | `AuditLogViewer` | Yes | Installation-wide audit log viewer. |
| `/admin/users` | `AdminUsers` | Yes | Superuser platform user management. |
| `/admin/queues` | `QueueAdmin` | Yes | Queue and worker visibility. |
| `*` | inline not-found | Mixed | Fallback 404 page. |

Use the bundled route lister to inspect a checkout:

```bash
node scripts/list_ui_routes.mjs REPO_ROOT
```

## Major component roles

### Layout/navigation

- `Layout`: sidebar, workspace context resolution, workspace switcher, user menu, theme toggles, command palette trigger, `AIAdvisorWidget` mount.
- `CommandPalette`: global `Cmd/Ctrl+K` navigation. Workspace-specific commands are built when `wsId` exists.
- `BackButton`, `Dialog`: shared interaction primitives.

### Experiment creation and data-driven forms

- `NewExperiment`: single-screen wizard. Select task, data source, target, and configuration; then `experimentsApi.create` followed by `runsApi.submit` with `plan: 'compare'`.
- `DynamicForm`: generic, schema-driven setup parameter renderer. It must remain free of hard-coded setup parameter names. It switches only on `SetupParam.kind` and uses `schema.groups` ordering.
- `DynamicForm.helpers`: `applyDefaults` and `stripDefaults`; keeps user intent in payloads by dropping defaults and empty values.
- `ExperimentConfigForm`: curated visual form for common setup knobs. It is allowed to hand-render selected names, but it still reads defaults/descriptions from the schema and preserves an "Other options" fallback for new engine params.
- `ColumnPickerModal`, `DataSourcesSection`, `SampleDatasetsBrowserModal`, `DatasetExploreModal`, `DataProfile`: dataset selection and profile surfaces.

### Run/trial workflow

- `RunDetail`: polls the run while queued/running; owns cancel, live log open state, `RunRunningCard`, `WorkerLoadCard`, `TrainingChart`, `TrialsCard`, AI explain/debug cards, snapshot display, promoted-version section.
- `EventLogDrawer`: right-side live WebSocket log. It connects only while open, deduplicates replayed events, filters success/failed/all, and retries unexpected close once.
- `EventStream`: inline older event-stream component with the same WebSocket contract; useful for focused tests and any simpler inline log usage.
- `TrialsCard`: run-scoped leaderboard. Loads run trials, resolves `model_id` to friendly names with `describeApi.models(task)`, supports table/chart toggle, blend/stack selection, and deep-links to trial detail.
- `ExperimentTrialsCard`: experiment-scoped trial list grouped by parent run and filterable by trial kind.
- `TrialDetail`: one candidate model dashboard. Tabs cover overview, pipeline, hyperparameters, plots, prediction, validation, and artifact. Tune/ensemble actions open dialogs and then show the run event log.
- `TrialActionDialog`: tune, ensemble, blend, stack dialogs that post follow-on action endpoints.
- `PipelineDiagram`, `PlotlyFigure`, `TrainingChart`: visualization primitives for pipelines, Plotly figures, and live metrics.

### Deployment/model registry workflow

- `RegisteredModels`: registry list by workspace.
- `RegisteredModelDetail`: version rows; request promotion via approval workflow; execute/route to approvals; deploy a specific version through an inline dialog.
- `DeployFromPipelineDialog`: create deployment for an existing pipeline from run/trial promoted-version surfaces. Validates endpoint slug client-side with the deployment slug regex.
- `Deployments`: workspace deployment table with status, auth mode, prediction count, errors, p50/p95, last hit.
- `DeploymentDetail`: endpoint metrics, `PredictTester`, deployment versions/rollback, prediction logs, and drift reports.
- `PredictTester`: JSON row textarea for endpoint prediction; validates JSON client-side before calling `deploymentsApi.predict`.
- `DeploymentVersionsCard`, `PredictionLogsCard`, `DriftReportsCard`, `DriftAnalysisModal`: deployment operations and monitoring panels.

### LLM advisory widgets

- `AIAdvisorWidget`: floating workspace-scoped panel listing provider status and recent consultations.
- `LLMSettings`: provider, model, API-key rotation/clear/test UI. Shows "advisory" expectations in copy.
- `AnalyzeDatasetModal`, `ExperimentDesignerModal`, `RunExplainerCard`, `FailureDebuggerCard`, `DeploymentReviewModal`, `DriftAnalysisModal`: render the standard LLM advice envelope. They must not directly execute destructive actions.

## Design-system conventions

Use Tailwind classes plus shared component-layer primitives from `src/index.css`:

- Buttons: `btn-primary`, `btn-secondary`, `btn-ghost`, `btn-danger`, `btn-accent`.
- Forms: `field`, `input`, `input-bare`, `hint`, `error`.
- Surfaces: `card`, `card-tight`.
- Type: `h-page`, `h-section`, `muted`, `kbd`.
- Status: `pill-neutral`, `pill-success`, `pill-danger`, `pill-warn`, `pill-accent`.

The UI currently boots light mode in `main.tsx`, although dark variants remain in styles. Avoid unreviewed dark-only assumptions. Inline styles exist in a few older components, but new work should prefer Tailwind and the primitives above.

## When adding a route

1. Add the page file under `src/pages` with a named export.
2. Import it in `src/App.tsx`.
3. Add the `<Route>` under the authenticated layout unless intentionally public.
4. If it is a sidebar destination, add a `SidebarLink` in `Layout` and a command in `CommandPalette`.
5. Add a focused component/page test if the page has logic beyond static rendering.
6. Run `node scripts/list_ui_routes.mjs` to confirm the route appears.

## Gotchas

- Flat `/runs/:runId` and `/deployments/:deploymentId` pages are authenticated but not workspace-prefixed; `Layout` fetches the record to recover workspace context.
- `WorkspaceDetail` receives `id`, not `wsId`, because route path is `/workspaces/:id`.
- Tests that use React Query should wrap components in a fresh `QueryClientProvider` with retries disabled.
- Components that export React components and non-component helpers in the same file can trip `react-refresh/only-export-components`; put pure helpers in a separate file as `DynamicForm.helpers.ts` does.
- Plotly charts should go through `PlotlyFigure` unless a component needs special custom Plotly layout behavior, as `TrialsCard` does for the leaderboard chart.
