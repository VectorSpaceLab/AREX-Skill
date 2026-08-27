# ODS Repo Provenance

This provenance file records the source snapshot used to build the generated ODS repo skill. It is a public refresh baseline and intentionally omits local checkout paths, private environment paths, and command logs.

Schema: `disco.repo-provenance.v1`.

## Source snapshot

| Field | Value |
| --- | --- |
| Repository | ODS (Osmantic Deployment System) |
| Remote URL | `https://github.com/Osmantic/ODS.git` |
| Commit | `5a4450765976e2ad2792b9ac8927f4873dac60f6` |
| Branch | `main` |
| Exact tag | none detected at `HEAD` |
| Product version evidence | `ods/manifest.json` declares `ods_version: 2.6.0` and release channel `stable` |
| Source dirty state before skill generation | clean |
| Dirty state after skill generation | generated `skills/` output is untracked by design |
| Import policy for this run | not imported by user request |

## Evidence paths used

### Product overview and architecture

- `README.md`
- `ods/README.md`
- `ods/manifest.json`
- `ods/docs/INSTALLER-ARCHITECTURE.md`
- `ods/docs/EXTENSIONS.md`
- `ods/docs/DASHBOARD-API-DEVELOPMENT.md`
- `ods/docs/ODS_CLI_DECOMPOSITION.md`
- `ods/docs/TESTING.md`
- `ods/docs/RELEASE_VALIDATION.md`
- `ods/docs/VALIDATION-MATRIX.md`

### Installers and platforms

- `install.sh`
- `install.ps1`
- `ods/install.sh`
- `ods/install-core.sh`
- `ods/installers/lib/`
- `ods/installers/phases/`
- `ods/installers/macos/`
- `ods/installers/windows/`
- `ods/tests/contracts/test-installer-contracts.sh`
- `ods/tests/contracts/test-preflight-fixtures.sh`
- `ods/tests/smoke/`

### Hardware, models, and backends

- `ods/installers/lib/detection.sh`
- `ods/installers/lib/tier-map.sh`
- `ods/installers/macos/lib/tier-map.sh`
- `ods/installers/windows/lib/tier-map.ps1`
- `ods/config/backends/`
- `ods/config/model-library.json`
- `ods/config/hardware-classes.json`
- `ods/config/gpu-database.json`
- `ods/scripts/select-model.py`
- `ods/scripts/detect-hardware.sh`
- `ods/scripts/classify-hardware.sh`
- `ods/scripts/load-backend-contract.sh`
- `ods/bin/model_switchboard/`
- `ods/tests/test-tier-map.sh`
- `ods/tests/test-tier-map-parity.sh`
- `ods/tests/contracts/test-overlay-map-coherence.sh`

### Services and extensions

- `ods/extensions/services/*/manifest.yaml`
- `ods/extensions/services/*/compose*.yaml`
- `ods/extensions/library/`
- `ods/extensions/schema/`
- `ods/extensions/templates/`
- `ods/scripts/resolve-compose-stack.sh`
- `ods/scripts/audit-extensions.py`
- `ods/lib/service-registry.sh`
- `ods/tests/test-extension-audit.sh`
- `ods/tests/test-resolve-compose-resilient.sh`

### Dashboard API and UI

- `ods/extensions/services/dashboard-api/`
- `ods/extensions/services/dashboard-api/requirements.txt`
- `ods/extensions/services/dashboard-api/tests/`
- `ods/extensions/services/dashboard/`
- `ods/extensions/services/dashboard/package.json`
- `ods/extensions/services/dashboard/src/`
- `ods/extensions/services/dashboard/vite.config.js`

### Operator CLI and host tools

- `ods/ods-cli`
- `ods/ods-backup.sh`
- `ods/ods-restore.sh`
- `ods/ods-update.sh`
- `ods/ods-uninstall.sh`
- `ods/scripts/ods-doctor.sh`
- `ods/scripts/ods-support-bundle.sh`
- `ods/bin/ods-host-agent.py`
- `ods/bin/remote_provider/`
- `ods/memory-shepherd/`
- CLI, doctor, backup/restore, remote-provider, and support-bundle tests under `ods/tests/`

### Testing, CI, and release validation

- `ods/Makefile`
- `ods/tests/`
- `.github/workflows/`
- `.pre-commit-config.yaml`
- `.gitleaks.toml`
- `ods/scripts/validate*.sh`
- `ods/scripts/release-gate.sh`
- `ods/scripts/simulate-installers.sh`

## Inspection environment summary

A private Python 3.11 environment was prepared only to inspect dashboard-api imports and route structure. It installed the dashboard-api runtime and test requirements, passed `pip check`, and imported selected API modules. Do not treat that private environment as part of the public repo skill, and do not copy local interpreter paths into downstream runtime instructions.

## Backend verification baseline

The generated skill covers multi-backend ODS source workflows. For skill creation, required verification was limited to CPU/host-safe repo checks and dashboard-api import inspection. NVIDIA CUDA, AMD ROCm/Lemonade, Intel Arc/SYCL, Apple Metal/MPS, Windows WSL2/Docker Desktop, full Docker service launches, and model downloads remain product validation lanes to run only when a downstream task explicitly needs them and the host supports them.

## Refresh guidance

Refresh this repo skill when any of these change materially:

- Installer phase ordering, platform entry points, generated config writers, or preflight contracts.
- GPU detection, tier maps, backend contracts, compose overlays, model library, or model lifecycle behavior.
- Service manifest schema, bundled service catalog, extension library/install/update/rollback semantics, or compose resolver security rules.
- Dashboard API route groups, auth/session behavior, frontend dev workflow, dashboard package scripts, or API dependencies.
- `ods-cli` command families, host-agent/remote-provider APIs, backup/restore/update/doctor/support-bundle behavior.
- Make targets, CI workflows, release validation policy, or important test fixtures.
