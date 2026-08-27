# ODS Installer Architecture Reference

This reference distills the installer/platform facts needed for future ODS maintenance. It is self-contained; source repo paths are named as provenance, not as runtime dependencies.

## Entry Points And Dispatch

| Surface | Source path | Current behavior |
| --- | --- | --- |
| Root Bash wrapper | `install.sh` | Prints an ODS banner, verifies the `ods/` directory exists, then `cd ods` and `exec ./install.sh "$@"`. |
| Root PowerShell wrapper | `install.ps1` | Defines installer flags, resolves `ods/installers/windows/install-windows.ps1`, forwards bound parameters, and exits with the delegated installer status. |
| Product Bash entry | `ods/install.sh` | Sources `installers/dispatch.sh`, calls `resolve_installer_target`, then execs Bash or PowerShell depending on the resolved target. |
| Dispatch helper | `ods/installers/dispatch.sh` | Uses `detect_platform` from `installers/common.sh` and routes `linux|wsl` to `install-core.sh`, `macos` to `installers/macos/install-macos.sh`, `windows` to `installers/windows/install-windows.ps1`, and mobile shells to `installers/mobile/install-mobile.sh`. |
| Platform detector | `ods/installers/common.sh` | Detects Termux, a-Shell/iOS, WSL via `/proc/version`, Windows shell families, macOS via `OSTYPE=darwin*`, Linux via `OSTYPE=linux*`, or `ODS_PLATFORM_OVERRIDE`. |

Operational guidance:

- Linux and WSL shell installs share the Linux orchestrator path: `ods/install-core.sh`.
- The primary macOS path is `ods/installers/macos/install-macos.sh`. The sibling `ods/installers/macos.sh` is a preflight/doctor-style helper kept for smoke coverage and should not be confused with the full macOS installer.
- The primary Windows user path is the root `install.ps1` wrapper in a normal PowerShell session. `ods/installers/windows.ps1` is a WSL2-delegated preflight path, not the native Windows orchestrator.
- Unsupported dispatch returns `unsupported:unknown` and reports `docs/SUPPORT-MATRIX.md` in source output; runtime guidance should summarize support directly instead of depending on that doc.

## Linux Orchestrator Contract

`ods/install-core.sh` is the Linux/WSL installer orchestrator. It:

1. Enables `set -euo pipefail`.
2. Installs a `cleanup_on_error` trap that prints the failing `INSTALL_PHASE`, log file, partial install location, and rerun advice.
3. Installs a double-tap `Ctrl+C` handler and ignores `Ctrl+Z`.
4. Sources installer libraries in a fixed order.
5. Parses CLI flags and feature defaults.
6. Detects package manager, prepares sudo, ensures PyYAML for the compose resolver, loads the service registry when available, then sources phase files in order.

### Linux Library Files

`ods/installers/lib/` currently contains these Bash library modules. They are intended to define functions/constants and avoid immediate host mutations when sourced:

| File | Installer role |
| --- | --- |
| `constants.sh` | Version, colors, install paths, default ports, model/bootstrap constants. |
| `logging.sh` | `log`, `success`, `warn`, `error`, and elapsed logging helpers. |
| `ui.sh` | CRT-style installer UI, menus, banners, spinners. |
| `sudo.sh` | Sudo credential preparation and privilege prompts. |
| `detection.sh` | Hardware/backend detection orchestration. Route tier/model internals to `hardware-and-models`. |
| `host-arch.sh` | Host architecture normalization. |
| `tier-map.sh` | Tier-to-model/context defaults. Route deep tier logic to `hardware-and-models`. |
| `docker-images.sh` | Docker image planning helpers. |
| `compose-images.sh` | Compose/image inventory helpers. |
| `compose-select.sh` | Compose overlay selection. Route extension compose mechanics to `services-and-extensions`. |
| `compose-failure-report.sh` | Diagnostics when compose operations fail. |
| `readiness-summary.sh` | Post-start readiness output. |
| `packaging.sh` | Distro package manager abstraction. |
| `python-runtime.sh` | Python/PyYAML discovery and installation helpers. |
| `progress.sh` | Installer progress reporting. |
| `model-lifecycle-lock.sh` | Locking around model configuration and bootstrap hot-swap. |
| `external-services.sh` | Host Ollama/LM Studio/external LLM route detection and validation. |
| `amd-topo.sh` | AMD GPU topology helpers. |
| `nvidia-topo.sh` | NVIDIA GPU topology helpers. |
| `background-tasks.sh` | Background task helpers. |
| `bootstrap-model.sh` | Bootstrap model lifecycle helpers. |
| `llama-memory-budget.sh` | llama-server memory budget helpers. |
| `path-utils.sh` | Portable path utilities. |

The orchestrator also loads `lib/service-registry.sh` when present so phases can resolve manifest-backed service ports and health paths.

### Linux Phase Order

The source docs describe 13 ordered phases, with `02b-external-services.sh` inserted as an extra detection-adjacent phase file. Treat the exact current source order below as canonical for maintenance:

| Order | `INSTALL_PHASE` value | Source file or step | Owns / mutates | Idempotency expectation |
| --- | --- | --- | --- | --- |
| 1 | `01-preflight` | `installers/phases/01-preflight.sh` | User/OS/tool checks, existing related install detection. | Safe to rerun. |
| 2 | `02-detection` | `installers/phases/02-detection.sh` | Hardware/backend detection, tier assignment, compose hints. | Safe to rerun; route tier internals elsewhere. |
| 3 | `02b-external-services` | `installers/phases/02b-external-services.sh` | Detect/validate explicit or reusable host Ollama/LM Studio endpoints. | Should preserve explicit external-LLM choices. |
| 4 | `03-features` | `installers/phases/03-features.sh` | Feature/profile selection and GPU assignment. | Preserve explicit CLI/user choices. |
| 5 | `04-requirements` | `installers/phases/04-requirements.sh` | RAM, disk, GPU, and port availability checks. | Safe to rerun. |
| 6 | `05-docker` | `installers/phases/05-docker.sh` | Docker, Compose, NVIDIA/ROCm prerequisites. | Avoid unnecessary reinstall; can mutate host runtime. |
| 7 | `model-lifecycle-lock` | `ods_model_lifecycle_lock_acquire` | Model configuration lock before generated config/model phases. | Must release after launch phase. |
| 8 | `06-directories` | `installers/phases/06-directories.sh` | Install dirs, source copy, `.env`, secrets, SearXNG, OpenClaw/Hermes/LiteLLM config, schema validation. | Preserve secrets/user state unless forced. |
| 9 | `07-devtools` | `installers/phases/07-devtools.sh` | Claude Code, Codex CLI, OpenCode, host agent, mDNS helper. | Skip existing tools when possible. |
| 10 | `08-images` | `installers/phases/08-images.sh` | Pull/build Docker images. | Resume pulls/builds when possible. |
| 11 | `09-offline` | `installers/phases/09-offline.sh` | Offline/air-gapped markers and config. | Safe when disabled. |
| 12 | `10-amd-tuning` | `installers/phases/10-amd-tuning.sh` | AMD APU groups, sysctl, modprobe, GRUB/tuned/systemd user timers. | Avoid duplicate host config; clearly host-mutating. |
| 13 | `11-services` | `installers/phases/11-services.sh` | Model download/bootstrap, `models.ini`, local image builds, compose stack launch. | Preserve valid models/secrets; resume bootstrap where possible. |
| 14 | lock release | `ods_model_lifecycle_lock_release` | Releases model lifecycle lock before health checks. | Must run after service launch path. |
| 15 | `12-health` | `installers/phases/12-health.sh` | Service health checks, Perplexica config, STT model pre-download. | Extend/defer around active model swaps. |
| 16 | `13-summary` | `installers/phases/13-summary.sh` | Summary URLs, desktop shortcut/sidebar pin, summary JSON, final preflight output. | Informational; orchestrator runs it under `set +e` so cosmetic failure does not fail install. |

## macOS Installer Shape

The full macOS installer is `ods/installers/macos/install-macos.sh`. It is a large Bash orchestrator with inline numbered sections, not separate `phases/*.sh` files.

Key facts:

- Requires Apple Silicon (`arm64`); Intel Macs are rejected for the full native Metal path.
- Requires Bash 4+. macOS ships Bash 3.2, so the installer re-execs a Homebrew Bash when available. In `--dry-run`, it reports the missing Bash 4+ bootstrap without installing Homebrew Bash.
- `llama-server` runs natively with Metal on host port `8080`; the rest of the stack runs under Docker Desktop. Containers reach host inference through `host.docker.internal:8080`.
- Uses macOS libraries in `ods/installers/macos/lib/`: `constants.sh`, `ui.sh`, `bridge-manager.sh`, `tier-map.sh`, `detection.sh`, `preflight-fs.sh`, `env-generator.sh`, and `installed-footprint.sh`.
- Major sections: preflight checks, hardware detection, feature selection, setup/directories/config generation, launch/model/Docker services, host-agent setup, and verification.
- `ods/installers/macos/ods-macos.sh` is the installed management CLI for status/start/stop/restart/logs/update and native llama-server lifecycle.
- ComfyUI is explicitly not available on macOS in the current installer because a suitable MPS Docker image is not shipped.

## Windows Installer Shape

The primary Windows orchestrator is `ods/installers/windows/install-windows.ps1`, reached from the root `install.ps1` wrapper.

Key facts:

- Run from a normal PowerShell session, not as Administrator for standard installs. Admin-owned user files are a known source of update/runtime friction.
- The source checkout and runtime directory are separate by default. Runtime defaults to `$env:USERPROFILE\ods`, or `$env:ODS_HOME`/`-InstallDir` when set.
- Requires Docker Desktop with the WSL2 backend. NVIDIA uses Docker GPU passthrough. AMD Strix Halo uses the Windows native accelerated path: Lemonade preferred, native Vulkan llama-server fallback when Lemonade is unavailable.
- Windows libraries live in `ods/installers/windows/lib/`: `constants.ps1`, `ui.ps1`, `compose-diagnostics.ps1`, `backend-contract.ps1`, `tier-map.ps1`, `detection.ps1`, `env-generator.ps1`, `installed-footprint.ps1`, `llm-endpoint.ps1`, `opencode-config.ps1`, `readiness-summary.ps1`, `service-plan.ps1`, `install-report.ps1`, and `model-activation.ps1`.
- Extracted Windows phases currently stop at phase file `07-devtools.ps1`; phases 08 and 09 are inline in `install-windows.ps1`. Do not invent separate Windows phase files unless the extraction is part of the task.

Windows phase files:

| Phase file | Owns |
| --- | --- |
| `phases/01-preflight.ps1` | Admin warning, PowerShell/Windows/Docker/disk/Ollama/source compose preflight. |
| `phases/02-detection.ps1` | GPU/RAM/tier selection, driver check, tier disk re-check. |
| `phases/03-features.ps1` | Feature defaults, CLI flags, interactive menu suppression in dry/non-interactive modes. |
| `phases/04-requirements.ps1` | Tier resource gates, Windows port conflicts, prompt/abort behavior. |
| `phases/05-docker.ps1` | Docker daemon, Compose detection, NVIDIA passthrough smoke, compose syntax validation. |
| `phases/06-directories.ps1` | Directory tree, source copy, `.env`, SearXNG, OpenClaw/Hermes/LiteLLM config, schema validation. |
| `phases/07-devtools.ps1` | OpenCode, Claude Code, Codex CLI, Windows Scheduled Task/helper setup. |
| inline phase 8 | Model/bootstrap download, native AMD inference, Docker compose launch. |
| inline phase 9 | Health checks, Perplexica config, shortcuts, summary JSON. |

## Generated Config Writer Synchronization

Generated config bugs often survive when only one platform writer is fixed. Review every writer below when the surface changes.

| Config surface | Linux writer | macOS writer | Windows writer | Upgrade/runtime writer to remember |
| --- | --- | --- | --- | --- |
| `.env`, core ports, secrets | `installers/phases/06-directories.sh` | `installers/macos/lib/env-generator.sh` | `installers/windows/lib/env-generator.ps1` | `ods config`, `ods update`, installer re-runs, env schema validation. |
| SearXNG settings | `installers/phases/06-directories.sh` | `installers/macos/lib/env-generator.sh` | `installers/windows/lib/env-generator.ps1` | Reinstall/forced regeneration paths. |
| OpenCode config | `installers/phases/07-devtools.sh` | `installers/macos/install-macos.sh` | `installers/windows/lib/opencode-config.ps1` | Windows OpenCode update script, bootstrap upgrade. |
| LiteLLM Lemonade config | `installers/phases/06-directories.sh` | Not a macOS primary writer | `installers/windows/lib/env-generator.ps1` and install orchestration for AMD | Bootstrap upgrade and host-agent model activation/repair. |
| Perplexica config | `installers/phases/12-health.sh`, `installers/phases/13-summary.sh` | `installers/macos/lib/env-generator.sh`, `installers/macos/install-macos.sh` | `installers/windows/lib/env-generator.ps1`, `installers/windows/install-windows.ps1` | Bootstrap upgrade and repair helpers. |
| Hermes config | `installers/phases/11-services.sh`, `scripts/patch-hermes-config.py` | `installers/macos/install-macos.sh` | `installers/windows/phases/06-directories.ps1`, `installers/windows/install-windows.ps1` | Bootstrap upgrade and host-agent activation. |
| External LLM route | `installers/phases/02b-external-services.sh`, `installers/phases/06-directories.sh` | Not installer-managed in current macOS path | Not installer-managed in current Windows path | Linux reruns with `--no-external-llm` or explicit external endpoint flags. |

Writer review rule: if a change affects generated routes, credentials, ports, model identity, context, or service URLs, check Linux, macOS, Windows, bootstrap/upgrade, host-agent, and dashboard-management paths before claiming parity.

## Validation Hooks For Architecture Changes

Prefer these safe checks before any real install:

```bash
# From the inner ods/ source directory.
bash -n install.sh install-core.sh installers/dispatch.sh installers/common.sh installers/phases/*.sh installers/lib/*.sh
bash tests/contracts/test-installer-contracts.sh
bash tests/contracts/test-preflight-fixtures.sh
bash tests/smoke/macos-dispatch.sh
bash tests/smoke/wsl-logic.sh
```

Use the bundled static checker for quick layout/phase-order review:

```bash
python3 sub-skills/installers-and-platforms/scripts/check_installer_layout.py --repo <ODS checkout>
```

Escalate to platform smoke, Docker, PowerShell, or real install only when the user accepts host mutation and platform requirements are available.
