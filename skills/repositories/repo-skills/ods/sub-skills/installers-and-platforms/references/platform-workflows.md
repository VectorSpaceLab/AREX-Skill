# ODS Platform Workflows Reference

Use this reference for platform-specific install, dry-run, quickstart, uninstall, and safe validation advice. Commands shown here are public workflows; always confirm host mutation before running a real install or lifecycle command.

## Host-Mutation Warning

Real ODS installers are not passive checks. Depending on platform and flags, they can:

- Create or replace a runtime directory such as `~/ods` or `$env:USERPROFILE\ods`.
- Generate `.env` secrets and config files.
- Install or configure Docker, NVIDIA/ROCm prerequisites, Homebrew Bash, Node/npm tooling, OpenCode, Claude Code, Codex CLI, LaunchAgents, Scheduled Tasks, or systemd units.
- Download large GGUF models and Docker images.
- Start, stop, or recreate containers and native inference servers.
- On AMD Linux, adjust user groups, sysctl, modprobe, GRUB/tuned, and user timers.

Default to dry-runs, syntax checks, contract tests, and static review until the user explicitly authorizes host mutation.

## Linux / WSL Workflow

### Entry Point

From a source checkout root:

```bash
./install.sh [options]
```

From the product runtime directory inside the checkout:

```bash
cd ods
./install.sh [options]
```

`ods/install.sh` dispatches Linux and WSL shells to `ods/install-core.sh`.

### Common Linux Options

The Linux orchestrator parses these installer options:

| Option | Use |
| --- | --- |
| `--dry-run` | Print planned actions without installing, pulling, or starting services. Prefer first. |
| `--skip-docker` | Do not install Docker; assume it is already available. Useful in dry-runs and controlled hosts. |
| `--force` | Allow overwrite/reset paths where the installer supports them. Treat as destructive-risk. |
| `--tier N` | Force tier `1`-`4` instead of auto-detecting. Route tier reasoning to `hardware-and-models`. |
| `--cloud` | Skip local GPU inference and use cloud/API-backed mode. |
| `--use-existing-lemonade` | Reuse an already-running Lemonade SDK endpoint for Linux AMD LLM inference. |
| `--lemonade-url U`, `--lemonade-api-key K` | Explicit Lemonade endpoint/auth for existing-Lemonade mode. |
| `--external-llm-url U`, `--external-llm-provider P`, `--external-llm-model M` | Explicit host Ollama/LM Studio/OpenAI-compatible reuse. |
| `--reuse-external-llm` | Permit non-interactive reuse of a detected matching external endpoint. |
| `--no-external-llm` | Clear persisted external-LLM selection on rerun. |
| `--voice` / `--no-voice` | Enable/disable Whisper + Kokoro. |
| `--workflows` / `--no-workflows` | Enable/disable n8n workflows. |
| `--rag` / `--no-rag` | Enable/disable Qdrant/embeddings RAG. |
| `--recommended` / `--no-recommended` | Enable/disable LiteLLM, SearXNG, Token Spy support services. |
| `--hermes` / `--no-hermes` | Enable/disable Hermes Agent. Hermes is the current default agent. |
| `--openclaw` / `--no-openclaw` | Enable/disable deprecated OpenClaw. Fresh installs keep it disabled unless explicitly opted in. |
| `--comfyui` / `--no-comfyui` | Enable/disable ComfyUI. Disabling saves large image-generation downloads. |
| `--langfuse` / `--no-langfuse` | Enable/disable Langfuse observability. Defaults off unless `--all` or explicit. |
| `--all` | Enable all optional current services except deprecated OpenClaw unless separately requested. |
| `--non-interactive` | Suppress prompts and use flags/defaults. Ensure sudo is cached or non-interactive-safe. |
| `--offline` | Configure offline/air-gapped mode. |
| `--lan` | Bind services to `0.0.0.0` instead of loopback. Increases network exposure. |
| `--no-bootstrap` | Wait for the full model instead of starting with the small bootstrap model. |
| `--summary-json P` | Write machine-readable install summary JSON to path `P`. |

### Safe Linux Dry-Run And Static Checks

```bash
cd ods
bash -n install.sh install-core.sh installers/dispatch.sh installers/common.sh installers/phases/*.sh installers/lib/*.sh
bash install-core.sh --dry-run --non-interactive --skip-docker --force
bash tests/contracts/test-installer-contracts.sh
bash tests/contracts/test-preflight-fixtures.sh
```

The dry-run still reads host state and may report missing prerequisites, but it should not create the runtime tree, install packages, pull images, download models, or start services.

### Linux Quickstart Notes

- The public one-line installer is `curl -fsSL https://install.osmantic.com/ods.sh | bash`; for maintenance work prefer source checkout commands so changes are testable.
- Docker must be installed/running or installable by the package manager unless `--skip-docker` is used for dry-run/control.
- The installer rejects root execution; use a regular user with sudo access.
- Linux Docker installs expose llama-server on host `http://localhost:11434` by default (`OLLAMA_PORT`) while containers use `llama-server:8080`.
- Re-runs should preserve `.env` secrets and data unless a force/reset path explicitly says otherwise.

## macOS Workflow

### Entry Point

From a source checkout:

```bash
cd ods
./install.sh [options]
```

or directly:

```bash
cd ods
./installers/macos/install-macos.sh [options]
```

`ods/install.sh` dispatches macOS to `installers/macos/install-macos.sh`.

### macOS Requirements And Behavior

- Apple Silicon is required for the full installer.
- Docker Desktop must be installed and running.
- Bash 4+ is required. The installer can use Homebrew Bash; in `--dry-run` it reports a missing Bash 4+ without installing it.
- Native Metal `llama-server` runs on host port `8080`; Docker services connect through `host.docker.internal:8080`.
- Runtime defaults to `~/ods`; config is `~/ods/.env`; models live under `~/ods/data/models/`.
- ComfyUI is not available on macOS in the current installer.

### Common macOS Options

| Option | Use |
| --- | --- |
| `--dry-run` | Validate planned actions without installing or mutating host state. |
| `--tier N` | Force a tier. Route tier/model reasoning to `hardware-and-models`. |
| `--force` | Allow overwrite paths; confirm risk. |
| `--non-interactive` | Use defaults without prompts. |
| `--all` | Enable all current optional macOS-supported features. |
| `--cloud` | Use cloud/API-backed mode instead of local native inference. |
| `--no-bootstrap` | Wait for the full model rather than bootstrap fast-start. |
| `--voice`, `--workflows`, `--rag`, `--recommended`, `--hermes`, `--openclaw`, `--langfuse` | Enable optional feature groups where supported. |

### macOS Management Commands

After install, run management commands from the runtime directory:

```bash
cd ~/ods
./ods-macos.sh status
./ods-macos.sh start
./ods-macos.sh stop
./ods-macos.sh restart
./ods-macos.sh logs llama-server 50
./ods-macos.sh update
```

`llama-server` logs are native host logs, not Docker container logs. For Docker services, `ods-macos.sh logs <service>` delegates to Docker Compose.

### Safe macOS Checks

```bash
cd ods
bash -n installers/macos/install-macos.sh installers/macos/ods-macos.sh installers/macos/lib/*.sh
bash tests/smoke/macos-dispatch.sh
bash tests/contracts/test-install-footprint-macos.sh
```

Do not run the full macOS installer on a non-macOS host. On macOS, still prefer `--dry-run` before real installation.

## Windows Workflow

### Entry Point

Run from a normal PowerShell session in the source checkout root:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\install.ps1 [options]
```

Do not use an Administrator shell for normal installs. The Windows preflight warns because user-level files like `.opencode`, `.env`, and `data\` should normally belong to the regular account.

### Windows Requirements And Behavior

- Windows 10 2004+ or Windows 11.
- Docker Desktop with WSL2 backend enabled.
- NVIDIA GPUs use Docker Desktop GPU passthrough through WSL2.
- AMD Strix Halo uses a Windows native accelerated path: Lemonade preferred, native Vulkan llama-server fallback when Lemonade cannot be installed.
- Runtime defaults to `$env:USERPROFILE\ods`, or a custom `-InstallDir` / `ODS_HOME` value.
- The source checkout is not the runtime directory. After install, run `ods.ps1` and manual Compose commands from the runtime directory so `.env` and relative volumes resolve correctly.

### Common Windows Options

| Option | Use |
| --- | --- |
| `-DryRun` | Simulate install without making changes. Prefer first. |
| `-Tier 2` | Force a tier. Route tier/model reasoning elsewhere. |
| `-Cloud` | Use cloud/API-backed mode. |
| `-All` | Enable full stack except deprecated OpenClaw unless `-OpenClaw` is also passed. |
| `-NoBootstrap` | Wait for the full model before launch. |
| `-InstallDir <path>` | Place runtime files on a chosen NTFS/ReFS path with enough space. |
| `-Voice`, `-Workflows`, `-Rag`, `-Recommended`, `-NoRecommended` | Feature group controls. |
| `-Hermes`, `-NoHermes`, `-OpenClaw`, `-Comfyui`, `-NoComfyui`, `-Langfuse`, `-NoLangfuse` | Agent/image/observability feature controls. |
| `-Lan` | Bind exposed services for LAN access. Confirm network exposure. |
| `-SummaryJsonPath <path>` | Write summary JSON to a requested path. |

### Windows Management Commands

After install:

```powershell
$installDir = "$env:USERPROFILE\ods"
cd $installDir
.\ods.ps1 status
.\ods.ps1 start
.\ods.ps1 stop
.\ods.ps1 restart
.\ods.ps1 logs llama-server 100
.\ods.ps1 update
.\ods.ps1 report
```

If installed with `-InstallDir`, use that same path instead of `$env:USERPROFILE\ods`.

### Safe Windows Checks

On a host with PowerShell available:

```powershell
# Parse/load checks only; do not run a real install.
pwsh -NoLogo -NoProfile -Command "$null = [scriptblock]::Create((Get-Content -Raw .\install.ps1)); 'root wrapper parse ok'"
pwsh -NoLogo -NoProfile -Command "$null = [scriptblock]::Create((Get-Content -Raw .\ods\installers\windows\install-windows.ps1)); 'windows installer parse ok'"
```

From a shell in the `ods/` source directory, safe contract candidates include:

```bash
bash tests/test-windows-installer-flags.sh
bash tests/contracts/test-windows-amd-local-compose.sh
bash tests/contracts/test-windows-hermes-config-patching.sh
bash tests/contracts/test-windows-lemonade-swap-wait.sh
bash tests/contracts/test-windows-llm-model-readiness.sh
bash tests/test-windows-port-preflight.sh
bash tests/test-windows-phase-abort.sh
bash tests/test-windows-env-dotfile-recovery.sh
```

Run PowerShell `.ps1` tests only on an appropriate Windows/PowerShell environment and only when their side effects are understood.

## Uninstall / Cleanup Workflows

Confirm intent before running uninstall commands.

Linux/macOS runtime cleanup:

```bash
cd ~/ods
./ods-uninstall.sh --force
```

Windows runtime cleanup:

```powershell
$installDir = "$env:USERPROFILE\ods"
cd $installDir
.\ods.ps1 uninstall --force
```

Preservation flags such as `--keep-data` and `--keep-models` exist for Windows and documented runtime uninstall paths. If a Windows runtime is partial and `ods.ps1` is missing, use the source-checkout fallback cleanup command from the checkout root:

```powershell
.\ods\installers\windows\ods.ps1 uninstall --force
```

That fallback removes Docker resources labelled as the ODS compose project before removing the runtime directory.

## Native Candidate Matrix

These are useful ODS-native candidates for final verification planning, not mandatory commands for every task:

| Candidate | Capability | Safety class | Expected signal |
| --- | --- | --- | --- |
| `bash tests/contracts/test-installer-contracts.sh` | Installer, backend, port, footprint, bootstrap guard contracts. | Safe-runnable shell contract; may require `jq`/Python. | Exits 0 and prints contract progress. |
| `bash tests/contracts/test-preflight-fixtures.sh` | Preflight engine fixtures for Linux, Windows, macOS, cloud, disk blockers. | Safe-runnable; creates temp files only. | Expected blocker counts match fixture. |
| `bash tests/smoke/linux-nvidia.sh` | Linux NVIDIA path/static service existence. | Static smoke. | Grep/file checks pass. |
| `bash tests/smoke/linux-amd.sh` | Linux AMD compose/static service contract. | Static smoke. | Grep/file checks pass. |
| `bash tests/smoke/macos-dispatch.sh` | macOS dispatch/support messaging. | Static smoke. | Dispatch and support strings present. |
| `bash tests/smoke/wsl-logic.sh` | WSL dispatch and support messaging. | Static smoke. | Dispatch/doc strings present. |
| `bash tests/test-windows-installer-flags.sh` | Root/Windows flag parity and docs. | Static shell grep test. | All flag parity checks pass. |
| Windows PowerShell contract tests under `ods/tests/contracts/` | Windows footprint, Docker pull, task cleanup, runtime recovery. | Platform-specific; inspect before running. | Expected assertions pass on Windows-capable host. |

## Difficult Synthetic Usability Cases

Use these when native tests do not cover a requested maintenance review deeply enough:

1. **Phase 06 generated `.env` drift across platforms.** A new environment key is added for a service URL. Determine every writer and validator that must change: Linux `installers/phases/06-directories.sh`, macOS `installers/macos/lib/env-generator.sh`, Windows `installers/windows/lib/env-generator.ps1`, `.env.schema.json`, bootstrap/upgrade and host-agent repair/activation writers if the key affects runtime routes, plus focused generated-config validation.
2. **New installer phase review.** A contributor adds `installers/phases/14-example.sh`. Review whether the phase belongs in Linux only or has macOS/Windows equivalents, whether its header declares Purpose/Expects/Provides/Modder notes, where `INSTALL_PHASE` is set in `install-core.sh`, whether it is idempotent, whether `--dry-run` avoids mutation, and which syntax/contract/smoke checks prove it.
