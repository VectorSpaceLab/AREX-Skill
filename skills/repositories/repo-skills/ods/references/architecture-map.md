# ODS Architecture Map

This reference is the root map for the generated ODS repo skill. Use it when a task spans more than one sub-skill or when you need to decide where a change belongs.

## Product shape

ODS (Osmantic Deployment System) is a shell-first, Docker-backed local AI stack. The source tree has two layers:

- Repository root: public README, top-level Linux/macOS and Windows bootstrap entry points, project security/contributor files, CI workflows, and the optional Tauri installer wrapper.
- `ods/`: core product runtime, installer phases/libraries, Docker Compose overlays, service manifests, dashboard API/UI, operator CLI, scripts, config, docs, and tests.

ODS wires local and optional hybrid AI services: llama-server, Open WebUI, Dashboard, Dashboard API, LiteLLM, Hermes, Token Spy, SearXNG, n8n, Qdrant, embeddings, Whisper, Kokoro, Privacy Shield, Langfuse, ComfyUI, remote-provider helpers, and other extensions. Services bind to loopback by default unless the manifest/compose contract explicitly broadens exposure.

## Core concepts

| Concept | Meaning | Owning sub-skill |
| --- | --- | --- |
| Installer phases | `install-core.sh` sources pure libraries, then ordered side-effectful phases from preflight through summary. | `installers-and-platforms` |
| Platform entry points | Linux/macOS shell bootstrap, macOS native Metal bridge flow, Windows PowerShell/WSL2 flows. | `installers-and-platforms` |
| Hardware tiering | GPU/backend detection maps hardware to a tier, model, GGUF file, context, and compose overlay. | `hardware-and-models` |
| Model lifecycle | Bootstrap model, full model download/swap, model catalog, model state, and switchboard reconciliation. | `hardware-and-models` |
| Service extension system | Manifest + compose fragment + GPU overlays + service registry + dashboard catalog. | `services-and-extensions` |
| Compose layering | Base compose plus backend/cloud/multigpu/profile/user-extension overlays resolved by the compose resolver. | `services-and-extensions` |
| Dashboard control plane | FastAPI service on port 3002 and React/Vite dashboard on port 3001. | `dashboard-and-api` |
| Operator CLI | Installed `ods` command for status, lifecycle, config, models, extensions, backup/restore, doctor, and support flows. | `ops-cli-and-host-tools` |
| Validation lanes | Make targets, shell/Python/JS tests, BATS, smoke, simulate, fleet, CI, and release validation. | `testing-and-release` |

## Source evidence by capability

- Installer source: `ods/install-core.sh`, `ods/installers/lib/`, `ods/installers/phases/`, `ods/installers/macos/`, `ods/installers/windows/`, top-level `install.sh` and `install.ps1`.
- Hardware/model source: `ods/installers/lib/detection.sh`, `ods/installers/lib/tier-map.sh`, platform tier maps, `ods/config/backends/`, `ods/config/model-library.json`, `ods/scripts/select-model.py`, `ods/bin/model_switchboard/`.
- Services/extensions source: `ods/extensions/services/`, `ods/extensions/library/`, `ods/extensions/schema/`, `ods/extensions/templates/`, `ods/scripts/resolve-compose-stack.sh`, `ods/scripts/audit-extensions.py`, `ods/lib/service-registry.sh`.
- Dashboard source: `ods/extensions/services/dashboard-api/`, `ods/extensions/services/dashboard/`.
- Operator source: `ods/ods-cli`, `ods/ods-*.sh`, `ods/scripts/ods-doctor.sh`, `ods/scripts/ods-support-bundle.sh`, `ods/bin/`, `ods/memory-shepherd/`.
- Validation source: `ods/Makefile`, `ods/tests/`, `.github/workflows/`, validation scripts and release docs.

These paths are evidence identifiers for current-checkout work. Runtime guidance in this generated skill is self-contained; do not require a future agent to open original docs just to understand a workflow.

## Sub-skill routing

1. `sub-skills/installers-and-platforms/SKILL.md` — use for installer code, install commands, phase order, platform-specific installer behavior, generated config writers, and install troubleshooting.
2. `sub-skills/hardware-and-models/SKILL.md` — use for GPU detection, tiers, model catalogs/profiles, backend contracts, model download/load/swap, and inference overlay consequences.
3. `sub-skills/services-and-extensions/SKILL.md` — use for service manifests, extension catalog entries, compose overlays, resolver/security scanner behavior, and service registry issues.
4. `sub-skills/dashboard-and-api/SKILL.md` — use for Dashboard API routes, React dashboard pages/components, dev-server workflow, auth/session handling, and dashboard tests.
5. `sub-skills/ops-cli-and-host-tools/SKILL.md` — use for the `ods` CLI, lifecycle operations, diagnostics, backup/restore/update, host-agent, remote-provider, mDNS, and memory-shepherd.
6. `sub-skills/testing-and-release/SKILL.md` — use to choose focused tests, interpret CI, run safe validation lanes, and decide when release-grade or fleet validation is required.

## Cross-skill workflows

### Adding a new service extension

1. Start in `services-and-extensions` for manifest fields, compose fragments, GPU overlays, library receipt semantics, and security scanner constraints.
2. If the service appears in the Dashboard extension portal, cross-check `dashboard-and-api` for catalog/install/update API and UI behavior.
3. If the operator CLI must expose or audit it, cross-check `ops-cli-and-host-tools`.
4. Use `testing-and-release` to select extension audit, compose resolver, dashboard, and smoke checks.

### Adding or changing a hardware tier

1. Start in `hardware-and-models` for detection, tier maps, backend contracts, model catalog, and context policy.
2. Cross-check `installers-and-platforms` when installer-generated `.env` or platform entry points change.
3. Cross-check `services-and-extensions` when compose overlays or GPU service policies change.
4. Use `testing-and-release` for tier-map parity, model-library, overlay, and smoke lane selection.

### Debugging an installed-system failure

1. Use `ops-cli-and-host-tools` for read-only status/log/config/doctor/support guidance.
2. Route to `installers-and-platforms` if the issue came from initial install or platform-specific generated config.
3. Route to `services-and-extensions` for compose or manifest failures.
4. Route to `hardware-and-models` for GPU/model/backend symptoms.
5. Route to `dashboard-and-api` for API/UI/auth/host-agent symptoms.

## Safety policy for future agents

- Treat install, update, backup/restore, service lifecycle, model downloads, Docker compose operations, and platform smoke tests as host-mutating unless a reference explicitly marks a command read-only.
- Prefer static checks, `--help`, syntax checks, selected contract tests, and dry-runs before launching services or touching host state.
- Do not run fleet, full release gate, Docker image pulls, full model downloads, or GPU/platform smoke lanes unless the user explicitly asks and the host constraints are acceptable.
- Keep secrets out of logs and reports. ODS has generated API keys, LiteLLM keys, OAuth/session tokens, and support-bundle redaction rules.

## Bundled helper scripts

- Root `scripts/check_ods_repo.py` checks whether a supplied checkout still resembles the source snapshot this skill was built from.
- Each sub-skill has its own read-only helper for layout, catalog, manifest, route, CLI, or validation-lane inspection. Run helpers with `--help` first.
