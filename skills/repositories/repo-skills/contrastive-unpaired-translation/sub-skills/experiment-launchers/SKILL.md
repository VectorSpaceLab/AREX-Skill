---
name: experiment-launchers
description: "Routes safe command-generation and launcher preset workflows for
  CUT, FastCUT, SinCUT, and pretrained experiments."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# experiment-launchers

Use this sub-skill when the user asks about `python -m experiments`, launcher presets, or how to list the concrete training/testing command strings for the repository's known experiment families.

## Read this when

- The user wants the preset commands for `grumpifycat`, `pretrained`, or `singleimage`.
- The user wants to inspect commands without starting tmux panes or running training.
- The user asks what the launcher `id` argument means.
- The user hits the broken `dry` path in this checkout.
- The user wants to map launcher output back to `train.py` or `test.py` commands.

## What this sub-skill covers

- Launcher CLI shape: `python -m experiments <name> <cmd> <id...>`.
- Supported families: `grumpifycat`, `pretrained`, and `singleimage`.
- Supported actions such as `run`, `train`, `test`, `run_test`, `print_names`, and `print_test_names`.
- GPU selection and epoch continuation behavior in the launcher wrapper.
- A safe bundled command-list helper that does not call tmux or execute training.

## What this sub-skill does not cover

- Actual training or testing execution. Read `../translation-workflows/` for that.
- Dataset conversion or layout preparation. Read `../data-preparation/` for that.
- `placeholder_launcher.py` as a supported workflow; it references stale or unsupported options.

## Use the bundled helper

Run `scripts/list_experiment_commands.py` to inspect known presets safely:

```bash
python scripts/list_experiment_commands.py --family grumpifycat --kind train
python scripts/list_experiment_commands.py --family pretrained --kind test --ids 2,3
python scripts/list_experiment_commands.py --family singleimage --kind both --json
```

The helper prints command strings only; it never starts tmux, allocates GPUs, downloads datasets, or runs model training.

## Read next

- `references/launcher-reference.md` for preset command tables and CLI behavior.
- `references/troubleshooting.md` for the broken `dry` command, missing `id`, and tmux/GPUtil issues.
- `../translation-workflows/references/cli-reference.md` when you need to edit the commands the launchers emit.

## Quick reminders

- `print_names` and `print_test_names` were verified as safe inspection commands.
- The upstream `dry` command fails in this checkout because its method call omits required ids.
- `launch`, `launch_test`, `stop`, and `close` can create or kill tmux windows; do not use them merely to inspect command strings.
