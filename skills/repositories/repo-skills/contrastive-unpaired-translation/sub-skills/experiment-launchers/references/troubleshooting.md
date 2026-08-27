# Troubleshooting

Use this page for `python -m experiments` launcher problems.

## Missing `id` argument

### Symptoms
- The launcher prints usage and says `id` is required.

### Likely causes
- The native CLI always expects at least one id after `<name> <cmd>`.

### Recovery
- Use `0`, another listed integer id, or `all` when the command supports it.
- For inspection, prefer `scripts/list_experiment_commands.py`.

## Broken `dry` action

### Symptoms
- `python -m experiments grumpifycat dry 0` fails with a `TypeError` about `launch()` missing `ids`.

### Likely causes
- In this checkout, `TmuxLauncher.dry()` calls `self.launch(dry=True)` without passing the required ids.

### Recovery
- Do not use `dry` for command inspection.
- Use `scripts/list_experiment_commands.py` instead.
- If editing the source launcher, pass ids into `dry()` or rewrite it to use a safe command-listing path.

## tmux side effects

### Symptoms
- tmux windows are created, killed, or commands are sent to panes.

### Likely causes
- `launch`, `launch_test`, `stop`, and `close` are orchestration commands, not passive inspection commands.

### Recovery
- Avoid those commands unless the user explicitly wants tmux orchestration.
- For command strings only, use the bundled command-list helper.

## Missing `GPUtil`

### Symptoms
- Importing or running launcher code fails with `ModuleNotFoundError: GPUtil`.

### Likely causes
- The native launcher imports `GPUtil` at module import time.

### Recovery
- Install `GPUtil` in the runtime environment.
- Use the bundled helper when you only need static command tables; it has no GPUtil dependency.

## GPU-selection surprises

### Symptoms
- A command runs on a different GPU than expected.
- Multi-GPU commands fail because not enough devices are available.

### Likely causes
- `TmuxLauncher.refine_command` rewrites `CUDA_VISIBLE_DEVICES` using available GPUs or a passed `--gpu_id`.

### Recovery
- Inspect the command with the bundled helper first.
- Pass explicit `--gpu_id` to native launcher runs when you need one GPU.
- For multi-GPU commands, confirm the requested `--gpu_ids` list length and the available devices.

## Stale placeholder launcher

### Symptoms
- `placeholder_launcher.py` emits options such as `model=contrastive_cycle_gan` or `evaluation_metrics` that do not match this checkout's active model/parser set.

### Likely causes
- The placeholder launcher is maintainer/demo scaffolding, not a supported current workflow.

### Recovery
- Do not use it for user-facing commands.
- Use `grumpifycat`, `pretrained`, or `singleimage` presets instead.
