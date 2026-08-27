---
name: ods
description: "Route ODS repository work for local AI stack installers, GPU/model
  backends, Docker services and extensions, dashboard API/UI, operator CLI, host
  tools, and validation lanes."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# ODS Repo Skill

Use this skill for tasks involving ODS (Osmantic Deployment System): a local AI server stack with shell/PowerShell installers, GPU-aware model routing, Docker Compose services, extension manifests, a FastAPI/React dashboard, an operator CLI, host helpers, and a large validation surface.

This root file is a router. Read the smallest sub-skill that owns the requested workflow, then use the linked references and bundled helper scripts there.

## First checks

1. If the task touches a repository checkout, run `scripts/check_ods_repo.py --help` and optionally `scripts/check_ods_repo.py --root <checkout>` to see whether the layout still matches this skill's assumptions.
2. Read `references/repo-provenance.md` before deciding whether this skill is stale for a newer ODS commit.
3. Use `references/architecture-map.md` when the task spans multiple ODS areas.
4. Use `references/troubleshooting.md` for cross-cutting symptoms, then route to the nearest sub-skill troubleshooting file.
5. Treat real install, update, service lifecycle, backup/restore, Docker, model download, GPU smoke, and fleet commands as host-mutating unless a sub-skill explicitly marks a check read-only.

## Sub-skill routes

| User task | Read this |
| --- | --- |
| Installers, platform entry points, installer phases, preflight, generated config writers, install/update/uninstall flow, Linux/macOS/Windows install troubleshooting | `sub-skills/installers-and-platforms/SKILL.md` |
| GPU/backend detection, hardware tiers, model catalogs/profiles, context policy, inference backend overlays, model download/load/swap, model switchboard | `sub-skills/hardware-and-models/SKILL.md` |
| Service manifests, extension catalog/library, compose fragments and GPU overlays, compose resolver/security scanner, service registry, extension install/update/rollback semantics | `sub-skills/services-and-extensions/SKILL.md` |
| Dashboard API routes, FastAPI auth/session behavior, dashboard frontend pages/components/hooks, Vite/uvicorn dev workflow, dashboard tests | `sub-skills/dashboard-and-api/SKILL.md` |
| `ods` CLI, lifecycle/status/logs/config/mode/model commands, backup/restore/update, doctor/support bundle, host-agent, remote-provider, mDNS, memory-shepherd | `sub-skills/ops-cli-and-host-tools/SKILL.md` |
| Selecting focused tests, interpreting Make targets and CI, release validation, smoke/simulate/fleet lanes, secret scanning, test troubleshooting | `sub-skills/testing-and-release/SKILL.md` |

## Common workflow routing

### Modify an installer or platform path

Read `installers-and-platforms` first. Cross-check:

- `hardware-and-models` if detection, tier, backend, model, context, or compose overlay selection changes.
- `services-and-extensions` if service manifests or compose layers change.
- `ops-cli-and-host-tools` if installed `ods` behavior changes after install.
- `testing-and-release` to choose syntax, contract, preflight, smoke, or simulation lanes.

### Add or debug a service extension

Read `services-and-extensions` first. Cross-check:

- `dashboard-and-api` for Dashboard extension portal, API endpoints, progress, update, rollback, and UI behavior.
- `ops-cli-and-host-tools` for `ods enable`, `ods disable`, `ods list`, `ods audit`, logs, and lifecycle effects.
- `hardware-and-models` for GPU-only or LLM-consuming services.
- `testing-and-release` for manifest audit, compose resolver, integration, and smoke tests.

### Change model or backend behavior

Read `hardware-and-models` first. Cross-check:

- `installers-and-platforms` for `.env` generation and platform detection paths.
- `ops-cli-and-host-tools` for `ods model`, `ods mode`, and runtime route reconciliation.
- `dashboard-and-api` for model pages, model-route probes, and API state.
- `testing-and-release` for tier-map parity, model-library, overlay, and runtime-tunable tests.

### Work on Dashboard API or UI

Read `dashboard-and-api` first. Cross-check:

- `services-and-extensions` when catalog/extension semantics change.
- `hardware-and-models` for model, GPU, and route data displayed by the dashboard.
- `ops-cli-and-host-tools` for host-agent-backed actions, keys, update/model/lifecycle calls, and diagnostics.
- `testing-and-release` for dashboard pytest/Vitest/build lanes.

### Operate or debug an installed ODS instance

Read `ops-cli-and-host-tools` first for safe command classification and diagnostics. Route symptoms to installer, hardware/model, services/extensions, or dashboard sub-skills as needed. Do not run destructive repair, purge, uninstall, delete-data, backup/restore, or update flows without explicit user intent.

### Choose validation for a change

Read `testing-and-release` first. It maps changed paths to focused lanes and marks expensive or host-mutating checks. Then use the owning sub-skill to understand why that lane matters.

## Public prerequisites and install model

ODS is not a single Python library. It is a source/runtime stack built from Bash, PowerShell, Python, React/Vite, Docker Compose, service manifests, and config files. Public operation usually starts from one of these entry paths:

- Linux/macOS shell bootstrap or clone-based `install.sh`.
- Windows PowerShell bootstrap or source checkout `install.ps1`/platform installer.
- Installed runtime `ods` CLI for status, logs, config, models, mode, extensions, diagnostics, backup/restore, and updates.
- Dashboard UI/API for browser-based control.

For repo maintenance, use focused syntax/tests instead of installing the stack unless the task specifically requires an installed-system run.

## Bundled references and scripts

- `references/architecture-map.md` — repository map, sub-skill boundaries, cross-skill workflows, and safety policy.
- `references/troubleshooting.md` — cross-cutting triage and high-risk operation warnings.
- `references/repo-provenance.md` — source commit/version/evidence paths and refresh baseline.
- `references/repo-routing-metadata.json` — structured routing metadata for managed imports; retained even though this run was not imported.
- `scripts/check_ods_repo.py` — read-only layout checker for current or future ODS checkouts.

## Verification baseline

This skill was generated with a private Python inspection environment for dashboard-api import and route inspection plus source/test evidence for the rest of ODS. Required repo-skill verification uses CPU/host-safe checks. Live GPU, Docker service launch, model download, full smoke, fleet, and release gates are optional product validation lanes, not prerequisites for using this skill.
