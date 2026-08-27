# Cross-Cutting Troubleshooting

Use this reference before escalating to expensive app startup, broad dependency installation, Docker/Playwright, GPU tasks, or real cloud providers.

## Fast Triage

1. Identify the surface: frontend, backend API, task/job/provider, CLI, SDK, or cross-surface.
2. Read the owning sub-skill first:
   - [frontend-web-app](../sub-skills/frontend-web-app/SKILL.md)
   - [backend-api-services](../sub-skills/backend-api-services/SKILL.md)
   - [task-execution-compute](../sub-skills/task-execution-compute/SKILL.md)
   - [cli-sdk-workflows](../sub-skills/cli-sdk-workflows/SKILL.md)
3. Run the read-only readiness helper before installing or starting services:

```bash
python <this-skill>/scripts/check_transformerlab_dev_readiness.py --repo-root <checkout>
```

## Environment and Install Failures

| Symptom | Likely cause | Next action |
| --- | --- | --- |
| Frontend build or dependency behavior differs from docs/CI | Unsupported Node version | Use Node v22. Avoid v23+ unless maintainers changed the repo support contract. |
| `npm start` fails on port conflict | API or frontend port already in use | Check ports `8338` and `1212`; stop the blocker deliberately instead of letting scripts kill unknown processes unattended. |
| Backend import fails from repo root | API code is source-run from `api/` | Run API commands from `api/` or set the appropriate source path in a controlled check. Do not assume `transformerlab.api` is an installed package. |
| Backend uses stale SDK behavior | API imports installed `lab` package | Reinstall `lab-sdk` into the API runtime after SDK changes and restart the API. |
| API install wants broad CPU/GPU packages | `api/install.sh` selects dependency variants and mutates envs | Ask before running broad install/repair. Do not install GPU/gallery dependencies unless the selected task requires them. |
| `ruff`, `pytest`, `lab`, or `uvicorn` missing | Wrong environment active | Use the documented API/CLI/SDK environment for that surface; avoid mutating Conda base. |

## Auth and Team Context

| Symptom | Likely cause | Next action |
| --- | --- | --- |
| Protected API returns `401` | Missing/expired JWT or API key | For browser/API checks, log in and retry with refreshed JWT; for CLI, validate active API key/profile. |
| API returns team header/cookie error | Missing team context | Include `X-Team-Id` for protected API calls or use frontend/CLI helpers that attach team context. |
| CLI command has auth but wrong team | Active CLI profile lacks `team_id` or points to another profile | Inspect `lab --profile <name> config`/profile state; remember `--profile` must appear before the subcommand. |
| Background thread resolves wrong workspace | Organization context var did not propagate | Set `lab.dirs.set_organization_id(team_id)` inside the scheduled coroutine/thread and clear it afterward. |

## Task, Job, and Provider Failures

| Symptom | Likely cause | Next action |
| --- | --- | --- |
| Job stuck in `WAITING` | Local provider queue is occupied | Inspect existing local jobs and queue worker state; do not queue more local jobs blindly. |
| Job stuck in `LAUNCHING` | Setup/provisioning is still running or waiting for input | Check launch progress and local stdout/stderr or remote request logs. Make setup non-interactive. |
| No logs in UI | Wrong log source or xterm rendering caveat | Use provider log API or task/job log endpoints. xterm.js text is not reliable DOM text. |
| `tfl-remote-trap` did not update status | SDK missing remotely, env vars absent, wrapper not applied | Verify setup installs SDK, normal launch wraps run command, and job id/experiment env are present. |
| Provider tests pass but real launch fails | Credentials, cloud quota, SSH, image, or GPU availability differ | Keep unit tests mocked; run real provider checks only with user-approved credentials and budget. |
| GPU/gallery example fails | Optional ML task dependencies or hardware mismatch | Treat gallery task dependencies as task-specific. Do not install all gallery packages globally. |

## Frontend/UI Failures

| Symptom | Likely cause | Next action |
| --- | --- | --- |
| Import error from `@mui/material` or icons | Project uses Joy UI and `lucide-react` | Replace with `@mui/joy` components and `lucide-react` icons. |
| Code references Electron or IPC | Electron has been removed | Use browser-safe React code and authenticated API endpoints. |
| UI state does not refresh after mutation | Missing SWR `mutate`/cache update | Use the authenticated fetch pattern and revalidate the relevant SWR key. |
| Test cannot find terminal log text | xterm output not in DOM | Poll the corresponding API endpoint and assert the response content. |
| Visual layout regression not covered by tests | No browser inspection | Start the app and use browser visual verification; only run Playwright when requested or when E2E files changed. |

## Backend/Data/DB Failures

| Symptom | Likely cause | Next action |
| --- | --- | --- |
| New router has too much business logic | Service pattern violation | Move logic into `api/transformerlab/services/`, keep router validation/response code thin. |
| Migration breaks SQLite/Postgres compatibility | DB-specific SQL or foreign key assumption | Avoid foreign keys; use portable SQLAlchemy patterns and service-level validation. |
| Datetime comparison bug | Local/aware/deprecated datetime use | Use `utc_now_naive()` for SQLAlchemy `DateTime` values. |
| Task YAML save/import mismatch | `task.yaml` and `index.json` fields drifted | Validate through `TaskYamlSpec` and ensure save paths resync the flat `index.json` metadata. |

## When To Stop

Stop and ask before:

- Running broad `api/install.sh` repairs or GPU dependency installs.
- Starting/stopping real services that may affect a user's current app session.
- Running Docker/Playwright stacks that build images or mutate containers.
- Launching remote providers, using cloud credentials, or spending quota.
- Applying migrations against non-disposable data.
- Deleting jobs, datasets, models, artifacts, tasks, profiles, or credentials.
