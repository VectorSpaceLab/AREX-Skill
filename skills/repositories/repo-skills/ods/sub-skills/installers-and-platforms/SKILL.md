---
name: installers-and-platforms
description: "Route ODS Linux, macOS, and Windows installer work, phase
  ordering, platform dry-runs, quickstarts, generated-config writer review, and
  install troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Installers And Platforms

Use this sub-skill when the task touches ODS installer entry points, platform dispatch, ordered install phases, dry-run behavior, quickstart guidance, or install-time troubleshooting.

## First Moves

1. Read [references/installer-architecture.md](references/installer-architecture.md) before changing installer structure, phase order, or generated config writers.
2. Read [references/platform-workflows.md](references/platform-workflows.md) before advising a Linux, macOS, Windows, WSL, dry-run, update, or uninstall workflow.
3. Read [references/troubleshooting.md](references/troubleshooting.md) when diagnosing failed installs, Docker/PowerShell/WSL/macOS issues, port conflicts, phase handoffs, or generated config drift.
4. Use the bundled read-only checker when reviewing layout changes:

```bash
python3 sub-skills/installers-and-platforms/scripts/check_installer_layout.py --repo <ODS checkout>
```

Run it from the generated repo-skill root or pass the path to a source checkout. The script is static and read-only; it does not install packages, start Docker, download models, or edit files.

## Route Here For

- `install.sh`, `install.ps1`, `ods/install.sh`, `ods/install-core.sh`, `ods/installers/dispatch.sh`, and platform installer entry-point behavior.
- Linux installer libraries in `ods/installers/lib/` and ordered phase files in `ods/installers/phases/` when the task is about installer orchestration rather than hardware/model internals.
- macOS installer behavior in `ods/installers/macos/install-macos.sh`, macOS helper libraries, native llama-server launch, and `ods-macos.sh` install-management workflows.
- Windows installer behavior in `ods/installers/windows/install-windows.ps1`, Windows installer libraries/phases, `install.ps1` wrapper forwarding, and `ods.ps1` install-management workflows.
- Host-mutating install review: identify safer dry-run, syntax, contract, or smoke checks before running real installers.
- Cross-platform generated config writer review for `.env`, SearXNG, OpenCode, Hermes, Perplexica, LiteLLM/Lemonade, and external-LLM route changes.

## Route Elsewhere

- Hardware tier thresholds, model catalog selection, GPU backend internals, and compose backend overlays: use `../hardware-and-models/SKILL.md`.
- Service manifest schema, extension compose mechanics, extension enable/disable, and compose security scanning: use `../services-and-extensions/SKILL.md`.
- Operator CLI command families after install (`ods start`, `ods enable`, backups, doctor/support bundle depth): use `../ops-cli-and-host-tools/SKILL.md`.
- Validation lane selection, CI/release gates, full smoke/simulate/gate interpretation: use `../testing-and-release/SKILL.md`.

## Safety Rules

- Treat real installers as host-mutating. They can create runtime directories, generate secrets, install or configure Docker/tooling, download large models/images, change user groups/LaunchAgents/Scheduled Tasks/systemd units, tune AMD Linux hosts, and start services.
- Prefer static checks, `--dry-run`, syntax checks, and contract tests unless the user explicitly authorizes a real install or lifecycle operation.
- Do not ask a future agent to depend on the original checkout docs or scripts as runtime dependencies. Use these bundled references and scripts; source repo paths named here are evidence and provenance.
- Do not leak local absolute paths, private environment names, temporary API keys, generated secrets, or command logs into user-facing advice.
- When a generated config writer changes, check every platform writer and relevant upgrade/runtime writer before calling the fix complete.

## Verification Shortlist

Safe first-pass checks for installer/platform work:

```bash
# Static layout check supplied by this skill.
python3 sub-skills/installers-and-platforms/scripts/check_installer_layout.py --repo <ODS checkout>

# Native source-check candidates from ODS when available and appropriate.
cd <ODS checkout>/ods
bash -n install.sh install-core.sh installers/dispatch.sh installers/common.sh installers/phases/*.sh installers/lib/*.sh
bash tests/contracts/test-installer-contracts.sh
bash tests/contracts/test-preflight-fixtures.sh
bash tests/smoke/linux-nvidia.sh
bash tests/smoke/linux-amd.sh
bash tests/smoke/macos-dispatch.sh
bash tests/smoke/wsl-logic.sh
```

Only run platform-specific PowerShell, Docker, full smoke, or real installer commands after confirming host impact and user intent.
