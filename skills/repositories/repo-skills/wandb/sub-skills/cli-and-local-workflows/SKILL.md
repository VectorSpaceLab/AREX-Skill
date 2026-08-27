---
name: cli-and-local-workflows
description: "Use W&B CLI and local workflows safely: login, init, status,
  offline/online/disabled modes, syncing offline runs, cache cleanup, Docker
  wrapping, self-hosted verification, and local state inspection."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# W&B CLI and Local Workflows

Use this sub-skill when an agent needs to configure a local W&B checkout or runtime environment without writing Python tracking code: authentication, workspace settings, local/offline run recovery, cache hygiene, Docker command wrapping, or self-hosted connectivity checks.

## Start Here

1. Confirm the CLI is available with `wandb --help` or `python -m wandb --help`; `wb` is an equivalent console-script entry point when installed.
2. Inspect current local state before changing anything:
   - `wandb status`
   - `python sub-skills/cli-and-local-workflows/scripts/inspect_wandb_local_state.py --root .`
3. Choose the least-destructive mode/configuration command for the user's goal:
   - `wandb init --project <project> --entity <entity>` for workspace defaults.
   - `wandb offline` or `wandb init --mode offline` to keep future run data local.
   - `wandb online` to clear offline mode for future runs.
   - `wandb disabled` only when the user wants no W&B logging/syncing.
4. For offline recovery, run `wandb sync` first to summarize candidates; sync explicit run directories or use `wandb sync --sync-all` only after confirming destination `entity`, `project`, and server URL.

## Reference Map

- [CLI reference](references/cli-reference.md): command routing, command behavior, safe dry-run/help checks, sync and Docker workflows.
- [Configuration](references/configuration.md): settings files, environment variables, mode precedence, offline run layout, and non-interactive CI setup.
- [Troubleshooting](references/troubleshooting.md): API keys, self-hosted host mismatch, sync path mistakes, destructive cleanup, local server caveats, and cache cleanup.
- [Local-state inspector](scripts/inspect_wandb_local_state.py): read-only helper that reports CLI availability, selected `WANDB_*` variables with secrets redacted, workspace settings, and candidate run directories.

## Boundaries

- Artifact commands such as `wandb artifact ...` and artifact cache details belong in the artifacts/registries sub-skill.
- Sweep and launch commands belong in the sweeps/launch sub-skill.
- Public API automation and Python-side run querying belong in the public API sub-skill.
- Do not include API keys in commands, logs, examples, or generated files; prefer environment injection by the caller or secret manager.
