# ODS Installer Troubleshooting Reference

Use this reference to diagnose install failures without immediately rerunning a host-mutating installer. Start with the failing platform, the current phase, dry-run/static evidence, and whether the user authorized real repair commands.

## First Triage

1. Identify the platform path:
   - Linux/WSL shell path: `ods/install-core.sh` through `ods/install.sh`.
   - macOS full path: `ods/installers/macos/install-macos.sh`.
   - Windows native path: root `install.ps1` to `ods/installers/windows/install-windows.ps1`.
2. Capture the failing phase or section. Linux prints `INSTALL_PHASE` in the error trap. Windows phases throw `ODS_INSTALL_ABORTED` for intentional fatal phase aborts. macOS prints major phase names.
3. Prefer read-only/static checks before repair:

```bash
python3 sub-skills/installers-and-platforms/scripts/check_installer_layout.py --repo <ODS checkout>
cd <ODS checkout>/ods
bash -n install.sh install-core.sh installers/dispatch.sh installers/common.sh installers/phases/*.sh installers/lib/*.sh
```

4. For real install/runtime diagnostics, warn that reports and compose configs can include secrets. Redact `.env` values, API keys, hostnames, and local paths before sharing publicly.

## Phase-Oriented Diagnosis

| Failing phase/surface | Likely class | First safe check | Notes |
| --- | --- | --- | --- |
| Dispatch before phase 01 | Wrong shell/OS, missing target, PowerShell unavailable from Bash path | Static layout checker; inspect `ods/installers/dispatch.sh` routing | Windows users should normally use root `install.ps1` in PowerShell. |
| Linux `01-preflight` / Windows `01-preflight.ps1` / macOS preflight | Root/admin mismatch, unsupported OS, missing base tools, Docker Desktop not reachable | Platform preflight commands and syntax checks | Linux rejects root; Windows warns against Administrator. |
| Detection / requirements | Driver/GPU ambiguity, low RAM/disk, port conflicts | Preflight fixtures; platform-specific preflight report | Route tier/model internals to `hardware-and-models`. |
| Docker setup/validation | Docker not installed/running, permissions, Compose missing, GPU runtime unavailable | `docker info`, compose syntax validation, contract tests | Docker fixes can mutate host; ask before installing packages. |
| Phase 06 / setup/config | Permission mismatch, malformed `.env`, stale generated config, missing schema key, writer parity bug | Generated-config writer map; `.env.schema.json` validation | Check Linux/macOS/Windows writers together. |
| Image/model launch | Registry failure, slow/corrupt model download, bootstrap hot-swap state, compose launch failure | Logs and compose diagnostics; avoid deleting model state prematurely | Existing valid models should be preserved. |
| Health/verification | Slow service startup, wrong service URL, auth mismatch, bootstrap model swap active | Health URLs from `.env`, service logs, readiness summary | Health budget bugs can look like broken installs. |
| Summary/shortcuts | Hostname/shortcut/report issue | Confirm install actually works before failing on cosmetic output | Linux phase 13 is intentionally non-fatal in the orchestrator. |

## Linux Issues

### Python/PyYAML fails near system detection

Symptoms include `No module named 'yaml'` around installer startup or compose resolver use. ODS prefers system Python during Linux install because distro packages such as `python3-yaml` are installed for `/usr/bin/python3`. An active Conda/venv first in `PATH` can hide that package.

Safe fixes to suggest:

```bash
conda deactivate
./install.sh
```

or, if the user owns the active Python environment:

```bash
python3 -m pip install pyyaml
./install.sh
```

### Non-interactive install appears hung during sudo work

In `--non-interactive`, Docker or NVIDIA setup can require sudo. Cache credentials first or run interactively:

```bash
sudo -v
./install.sh --non-interactive
```

If sudo requires a password and no terminal prompt is possible, fail visibly rather than hiding the skipped prerequisite.

### Docker not installed, daemon stopped, or permission denied

Safe probes:

```bash
command -v docker
docker info
docker compose version || docker-compose version
```

Common fixes after user approval:

```bash
sudo systemctl start docker
sudo usermod -aG docker "$USER"
```

The group change requires a new login/session. Do not claim it fixed the current shell unless the user starts a new session or uses an equivalent group refresh.

### Port conflicts

Use precise port ownership checks before killing anything:

```bash
sudo lsof -i :3000
sudo lsof -i :8080
sudo lsof -i :11434
```

Prefer changing `.env` port variables or stopping the known conflicting service. Avoid `kill -9` unless the user explicitly confirms the process is safe to terminate.

### Disk and model download failures

Check disk before retrying downloads:

```bash
df -h
```

If a model download failed, rerun the installer to resume. Do not delete partial model/bootstrap state unless the file is proven corrupt or the installer directs removal.

### NVIDIA Blackwell driver/device mismatch

When `nvidia-smi` shows the driver but container devices fail, Blackwell systems may require NVIDIA open kernel modules. On Ubuntu-family hosts, the fix is typically `nvidia-open` or branch-specific `nvidia-driver-<branch>-open`, followed by reboot. Treat this as a host driver change requiring user approval.

### Linux preflight reports

Structured preflight commands:

```bash
cd ods
./scripts/linux-install-preflight.sh
./scripts/linux-install-preflight.sh --json
./ods-preflight.sh --install-env --json
```

The JSON includes summary counts and stable check IDs. Redact local paths and hostnames before sharing.

## macOS Issues

### Bash 4+ missing

The full macOS installer needs Bash 4+. In dry-run mode, it prints that a real install would run `brew install bash` and exits without mutation. In a real install, Homebrew may be required. Installing Homebrew or Bash changes the host; ask before advising real execution.

### Docker Desktop not running

The macOS installer requires a reachable Docker engine. Ask the user to start Docker Desktop and wait until it is ready, then check:

```bash
docker version
docker info
```

Docker Desktop, Colima, Rancher Desktop, OrbStack, or a forwarded socket may be acceptable in source detection, but user-facing quickstarts assume Docker Desktop.

### Not Apple Silicon

The full macOS path rejects Intel Macs because local inference requires Metal acceleration on Apple Silicon. Do not route Intel Macs to the native macOS installer; suggest a supported Linux/Windows/cloud path instead.

### Port 9000 conflict / AirPlay Receiver

macOS AirPlay Receiver commonly uses port `9000`. The installer auto-reassigns Whisper to `9100` when it detects that conflict and points users to the AirPlay Receiver setting if they want to free `9000`.

### Native llama-server or LaunchAgent issues

Remember macOS uses native host processes for llama-server and OpenCode. Troubleshooting differs from Linux Docker-only assumptions:

```bash
cd ~/ods
./ods-macos.sh status
./ods-macos.sh logs llama-server 50
```

LaunchAgents need a launchd-friendly `PATH`; installer code computes one explicitly because launchd does not inherit the login shell environment.

### macOS service limitations

- ComfyUI is not shipped on macOS in the current installer.
- TEI embeddings may run under Rosetta emulation and can be slower to become healthy.
- Dashboard GPU display can be limited because the dashboard container is Linux-based while Metal runs on the host.

## Windows Issues

### PowerShell script execution blocked

Use a per-session execution policy bypass rather than changing machine policy:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\install.ps1
```

or:

```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1
```

### Administrator shell warning

Normal Windows installs should not run as Administrator. Continuing can create `.opencode`, `.env`, and `data\` under an elevated account and cause later permission/update problems. Ask the user to reopen a normal PowerShell unless they intentionally accept admin-owned files.

### Source checkout versus runtime directory confusion

The downloaded/cloned source folder is not the runtime by default. Runtime defaults to `$env:USERPROFILE\ods` or `-InstallDir`. Manual Compose commands must run from the runtime directory so `.env` and relative volumes resolve correctly.

```powershell
$installDir = "$env:USERPROFILE\ods"
cd $installDir
.\ods.ps1 status
```

### Docker Desktop / WSL2 not ready

First checks:

```powershell
docker info
wsl --status
docker pull alpine:3.20
```

Common fixes:

- Start Docker Desktop and wait until the whale icon is ready.
- Enable “Use the WSL2 based engine”.
- Enable WSL integration for the target distro when using WSL-based probes.
- Add the installed runtime directory, usually `C:\Users\<you>\ods`, to Docker Desktop file sharing if bind mounts fail.

### NVIDIA visible on Windows but not WSL/Docker

Probe in layers:

```powershell
nvidia-smi
wsl nvidia-smi
docker run --rm --gpus all nvidia/cuda:12.0.0-base-ubuntu22.04 nvidia-smi
```

If Windows works but WSL/Docker fails, focus on WSL2 backend, Docker Desktop WSL integration, NVIDIA driver freshness, and antivirus/security exclusions for Docker. Driver/security changes require user approval.

### AMD Lemonade MSI failure

ODS installs Lemonade for the current user under `%LOCALAPPDATA%\lemonade_server`; it does not require Administrator or all-users `Program Files` installation. The verbose MSI log is under the ODS runtime logs directory, typically:

```text
%USERPROFILE%\ods\logs\lemonade-msi-install.log
```

If `-InstallDir` was used, use that runtime directory. ODS can fall back to native Vulkan `llama-server`, but the installer output should make Lemonade failure explicit.

### Windows compose failure diagnostics

When `install-windows.ps1` or `ods.ps1` reports compose failure, it prints a diagnostics block with Docker version/info, compose config output, and container state. `docker compose config` can interpolate `.env` secrets; redact before public sharing.

### Generate a Windows report

From a source checkout or runtime with `ods.ps1` available:

```powershell
.\ods\installers\windows\ods.ps1 report
```

or from the runtime directory:

```powershell
.\ods.ps1 report
```

The report includes platform/GPU basics, compose flags, Docker info, compose config/ps output, and local health checks. Redact secrets and private paths.

## Cross-Platform Generated Config Troubleshooting

When `.env`, service URL, auth, model id, context, or generated YAML/JSON is wrong:

1. Identify the writer that produced the bad file.
2. Check all sibling writers, not just the failing platform.
3. Check `.env.schema.json` and generated config contract tests.
4. Check bootstrap-upgrade and host-agent activation/repair writers if the config can be rewritten after install.
5. Re-run safe generated-config tests before real install.

Minimum writer map:

| Surface | Linux | macOS | Windows |
| --- | --- | --- | --- |
| `.env` and secrets | `installers/phases/06-directories.sh` | `installers/macos/lib/env-generator.sh` | `installers/windows/lib/env-generator.ps1` |
| OpenCode | `installers/phases/07-devtools.sh` | `installers/macos/install-macos.sh` | `installers/windows/lib/opencode-config.ps1` |
| Perplexica | `installers/phases/12-health.sh`, `installers/phases/13-summary.sh` | macOS env generator and installer | Windows env generator and installer |
| Hermes | `installers/phases/11-services.sh`, Hermes patch script | macOS installer | Windows phase 06 and installer |
| LiteLLM/Lemonade | Linux phase 06 | Not primary macOS surface | Windows env generator / AMD path |

## Safe Escalation Checklist

Before telling the user to rerun a real installer:

- State which platform path and phase failed.
- State what the rerun may mutate.
- Prefer `--dry-run`/`-DryRun` first if the problem is configuration or layout.
- Preserve downloaded models, `.env`, and data unless corruption is proven.
- Ask before deleting runtime directories, changing groups/drivers, installing packages, disabling security tools, killing unknown processes, or running uninstall.
- Use focused native tests or smoke checks before full release gates.
