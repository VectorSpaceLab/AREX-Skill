# Training CLI

This reference covers the installed `train` command, the RSL-RL config objects
it exposes, and the safety boundaries around distributed or credentialed runs.
Use `train --help` first whenever you need the exact Tyro surface for a task.

## Quick safety guide

| Command | Safety | What it proves |
|---|---|---|
| `uv run list-envs` | safe | registry discovery works |
| `uv run train <TASK> --help` | safe | task-specific training flags parse |
| `uv run train <TASK> --agent.max-iterations 1 --env.scene.num-envs 1 --gpu-ids None --agent.logger tensorboard --agent.upload-model False` | bounded but not help-only | tiny CPU smoke; creates local logs |
| `uv run train <TASK> --gpu-ids "[0, 1]"` | long GPU job | multi-GPU launch path works |
| `uv run play <TASK> --help` | safe | playback flags parse |
| `uv run demo` | networked | demo assets download and play |
| `uv run export-scene <TARGET>` | local | export path is valid |

## `train` command surface

The installed command is task-first:

```bash
uv run train Mjlab-Velocity-Flat-Unitree-G1 \
  --env.scene.num-envs 4096 \
  --agent.algorithm.learning-rate 3e-4 \
  --agent.resume True
```

Useful top-level flags:

- `--registry-name` for tracking tasks that need a motions registry artifact
- `--video` / `--video-length` / `--video-interval` for rollout capture
- `--enable-nan-guard True` for stability debugging
- `--log-root` for the experiment log root
- `--torchrunx-log-dir` to control multi-GPU worker logs
- `--wandb-run-path` and `--wandb-checkpoint-name` for checkpoint resume
- `--gpu-ids` for CPU, single-GPU, or multi-GPU selection

## Tyro syntax notes

The CLI uses Tyro with a strict style:

- booleans must be explicit: `--agent.resume True`, not a bare switch
- collection values use Python literal syntax: `--gpu-ids "[0, 1]"`
- nested fields use dotted paths and hyphenated field names from help output
- inspect `--help` whenever a field name is unclear

## RSL-RL config objects

The training stack exposes three important config objects:

- `RslRlOnPolicyRunnerCfg`: seed, rollout length, iterations, observation
  groups, save interval, experiment name, logging choices, resume options,
  action clipping, model upload, and actor/critic/algorithm subconfigs
- `RslRlModelCfg`: hidden dims, activation, obs normalization, optional CNN or
  RNN settings, and distribution config
- `RslRlPpoAlgorithmCfg`: learning-rate schedule, epochs, minibatches, PPO
  hyperparameters, optimizer, and KL/entropy controls

The wrapper and runner behavior matters too:

- `RslRlVecEnvWrapper` resets the env on construction, merges terminated and
  truncated into `dones`, and passes `time_outs` for infinite-horizon tasks
- `MjlabOnPolicyRunner` persists environment step counters in checkpoints and
  keeps the ONNX export path compatible with the installed runner format

## Checkpoints and logs

Training artifacts are written under a run directory similar to:

```text
logs/rsl_rl/{experiment_name}/{timestamp}/
  params/env.yaml
  params/agent.yaml
  model_*.pt
  videos/train/
  torchrunx/
```

Checkpoint selection rules:

- `--agent.resume True` resumes from the latest matching local run
- `--agent.load-run` and `--agent.load-checkpoint` are regex filters
- `--wandb-run-path entity/project/run_id` loads from W&B instead of local files
- `--wandb-checkpoint-name` narrows the checkpoint inside that run
- `--agent.upload-model False` keeps metric logging but skips model uploads

## Distributed training

`--gpu-ids` accepts `None`, a list, or `all`:

- `None` selects CPU mode
- a list selects indices relative to `CUDA_VISIBLE_DEVICES`
- `all` uses every visible GPU

Multi-GPU training is data-parallel, not work-splitting:

- each GPU runs the full environment count
- gradients are synchronized across processes
- scale `--agent.max-iterations` down if you want the same total training time
- `--torchrunx-log-dir ""` disables worker log files

## Cloud and benchmark boundaries

Cloud launchers, W&B sweeps, and benchmark automation are long-running,
credentialed, or networked. Treat them as reference-only unless the user asks
for that workflow explicitly. They should not be used as ordinary bounded
verification commands.

## Safe verification ladder

Helper paths below are relative to this sub-skill directory.

1. `uv run list-envs`
2. `uv run train <TASK> --help`
3. `uv run play <TASK> --help`
4. `uv run python scripts/check_task_registry.py --json`
5. `uv run python scripts/validate_motion_csv_schema.py --help`

Optional tiny run, only with an explicit runtime budget:

```bash
uv run train <TASK> \
  --agent.max-iterations 1 \
  --env.scene.num-envs 1 \
  --gpu-ids None \
  --agent.logger tensorboard \
  --agent.upload-model False
```

If a command fails before training starts, fix the config or registry first.
Do not jump to a long GPU run until the help surface and registry lookup both
work.
