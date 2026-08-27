# Manifest And Runtime

This file describes the test-rig model used by the repository: groups, tiers, runtime modes, reports, and critical-path coverage.

## Manifests

### `tests/groups.yaml`

This file is the single source of truth for test selection.

Important keys include:

- `tier`: `unit`, `integration`, or `e2e`.
- `workdir`: the directory from which the group runs.
- `paths`: pytest paths or node IDs.
- `markers`: a pytest marker expression.
- `requires_services`: infra such as PostgreSQL, Redis, RabbitMQ, or MinIO.
- `requires_platform`: whether the full platform stack must be brought up.
- `depends_on`: dependency groups that must run first.
- `optional`: whether the group can be skipped without failing the lane.
- `coverage_source`: the source tree that group coverage should be attributed to.

### `tests/critical_paths.yaml`

This file records the user and system flows that the repo promises not to break. Each path includes:

- an `id`,
- a description / entry,
- and the test groups that are supposed to cover it.

## Runtime Modes

The rig supports three runtime modes:

| Mode | When to use it | Notes |
| --- | --- | --- |
| `compose` | CI or full stack verification | Reuses the repo's Docker Compose stack plus the test overlay |
| `testcontainers` | Local infra-only iteration | Provisions infra, but does not auto-launch the whole app stack today |
| `local` | You already started the stack yourself | Reads URLs from the environment |

The runtime exports `UNSTRACT_*_URL` values and an `UNSTRACT_RIG_SESSION_ID` so tests can prove the rig ran.

## CLI Surface

`tests.rig` exposes these subcommands:

- `run` — execute selected groups with dependency expansion.
- `list-groups` — print group names, tiers, dependencies, and flags.
- `list-critical-paths` — print critical-path status.
- `expand` — show what `run` would execute.
- `validate` — validate the manifests.
- `platform up|down|status` — manage the platform runtime.
- `report combine` — re-aggregate existing reports.

## Reports

The rig writes reports under `reports/` with per-group JUnit / markdown output and a combined summary. Coverage is aggregated after the run when coverage is enabled.

## Important Coverage Facts

- The rig does not chase 100% line coverage; it is aimed at critical-path coverage.
- A critical path can still be a gap if no covered group ran green.
- The fan-out half of workflow execution remains a deliberate gap until the product exposes a stable observable for it.

## When To Read This File

Read this file when you need to decide which groups to run, how a path is covered, or how a runtime mode changes the test environment.
