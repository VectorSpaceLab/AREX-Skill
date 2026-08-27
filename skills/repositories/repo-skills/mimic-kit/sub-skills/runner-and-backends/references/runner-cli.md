# Runner and CLI semantics

This reference distills the shared runner behavior from the target checkout's runner, the argument parser, the env / agent / engine builders, the README install/train/test sections, and the repo-maintained argument presets.

For generated-skill recipes, launch the runner through the bundled helper rather than pointing future agents at a source script path:

```bash
python sub-skills/runner-and-backends/scripts/run_mimickit.py \
  --repo-root <mimickit-checkout> \
  -- --arg_file args/deepmimic_humanoid_ppo_args.txt --visualize false
```

The helper sets the target checkout as the working directory and prepends `<repo-root>/mimickit:<repo-root>` to `PYTHONPATH`, matching MimicKit's script-oriented import layout.

## End-to-end flow

The main runner follows this sequence:

1. Parse CLI tokens into the custom argument table.
2. If `--arg_file` is present, load that file as a second argument source.
3. Build the environment from `env_config` + `engine_config`.
4. Build the agent from `agent_config`.
5. Optionally load `--model_file` into the agent.
6. Branch into `train` or `test` mode.
7. In multi-device runs, spawn one worker per device and initialize distributed communication.

### Practical meaning

- The runner is **config-driven**: the YAML triad selects the backend, environment family, and agent family.
- The target runner imports the engine builder first because some simulator stacks need that import order.
- The root process is rank 0; extra devices run in spawned processes.

## Argument-file behavior

`--arg_file` is a plain text preset file with the same token syntax as the CLI. The target runner opens the path exactly as written. When using the bundled `scripts/run_mimickit.py` helper, paths are resolved from the explicit `--repo-root` checkout.

### Syntax rules

- Keys start with `--`.
- Values follow until the next key.
- Blank lines are ignored.
- Lines that begin with `#` are comments.
- Treat inline comments as unsafe; keep comments on their own lines.
- Boolean flags accept truthy literals like `true`, `True`, `1`, `T`, and `t`; anything else is false.

### Precedence rules

- CLI tokens are loaded first.
- The preset file is loaded second.
- Existing keys are **not** overwritten when the file is loaded.
- Therefore, **CLI flags win** over the preset file.
- Within one token source, the first occurrence of a key wins.

### Practical override pattern

Use presets for stable defaults, then override only the experiment-specific flags on the command line.

## Core flags

| Flag | Meaning | Default / notes |
| --- | --- | --- |
| `--mode` | Chooses `train` or `test`. | Default: `train`. No other values are supported. |
| `--arg_file` | Loads a preset file. | Useful for repo-maintained experiment bundles. |
| `--engine_config` | Selects the backend config YAML. | Required for real runs. Must match the simulator backend and asset format. |
| `--env_config` | Selects the environment YAML. | Required for real runs. `env_name` decides which env builder branch is used. |
| `--agent_config` | Selects the agent YAML. | Optional only when intentionally using the Dummy agent. If omitted, the runner falls back to `DummyAgent`. `agent_name` decides the agent branch. |
| `--num_envs` | Number of parallel environments. | Default: `1`. Some backends / tasks are not parallel-friendly. |
| `--visualize` | Enables the viewer. | Default: `true`. Use `false` for headless speed or headless-only logging. |
| `--video` | Enables headless video capture. | Default: `false`. Engines disable recording when visualization is on. |
| `--out_dir` | Output root. | Default: `output/`. Training writes checkpoints and logs here. |
| `--logger` | Logging backend. | `txt`, `tb`, or `wandb`. Default: `txt`. |
| `--model_file` | Loads a trained checkpoint before mode selection. | Needed for test / warm-start workflows. |
| `--devices` | Distributed device list. | Default: `cuda:0`. Use `cpu` or multiple `cuda:{i}` values as needed. |
| `--master_port` | Distributed TCP port. | Random 6000-6999 if omitted. Set it explicitly when coordinating jobs. |
| `--save_int_models` | Saves periodic intermediate checkpoints. | Default: `false`. Train-only. |
| `--max_samples` | Training budget. | Default: large integer max. Train-only. |
| `--test_episodes` | Evaluation episode budget. | Default: large integer max. Test-only. |

## Output files and logs

### Training mode

Training writes these files under `--out_dir`:

- `model.pt`
- `log.txt`
- `engine_config.yaml`
- `env_config.yaml`
- `agent_config.yaml`
- optional `int_models/model_<iteration>.pt` when `--save_int_models true`

### Logger-specific output

- `txt`: plain text log file at `log.txt`; video objects are not rendered there
- `tb`: TensorBoard event files in the same output directory
- `wandb`: W&B run metadata / metrics are uploaded to the `mimickit` project; the local model and text log still land in `--out_dir`

### Test mode

Test mode prints summary metrics to stdout:

- mean return
- mean episode length
- number of episodes

Test mode does **not** create the training checkpoint outputs above unless the surrounding workflow does so separately.

## Command-building checklists

### 1. Choose the right backend first

- Isaac Gym: use the Isaac Gym engine YAML and XML/MJCF assets.
- Isaac Lab: use the Isaac Lab engine YAML and USD assets.
- Newton: use the Newton engine YAML and XML or URDF assets.

### 2. Match the triad

- `engine_config` decides the simulator backend.
- `env_config` decides the env family and asset names.
- `agent_config` decides the policy / trainer family.

### 3. Keep headless jobs truly headless

- For fast training, set `--visualize false`.
- If you want logger-visible video, keep `--visualize false`, set `--video true`, and choose a logger that can surface `Video` objects (`tb` or `wandb`).
- Do **not** assume `--video true` still works when `--visualize true`; the engine constructors disable recording in that case.

### 4. Set the process plan explicitly for distributed jobs

- Pass the full device list with `--devices`.
- Use a fixed `--master_port` if multiple jobs may run on the same host.
- Keep the device family consistent across all workers.

### 5. Save the exact experiment record

- Use `--out_dir` so the runner copies the resolved YAML files into the output directory.
- Use the text logger for the simplest portable artifact set.
- Use TensorBoard or W&B only when their backend is actually available in your environment.

## Representative preset families

The repo-maintained `args/*.txt` files fall into a few recurring groups:

- DeepMimic / AWR / LCP training presets
- AMP / ADD / ASE training presets
- SMP training presets
- `view_motion` presets for motion playback; these usually omit `agent_config` and fall back to `DummyAgent`
- `dof_test` presets for DoF sanity checks; these also usually omit `agent_config`
- `vault` presets for vault-style imitation workflows

The bundled presets are the quickest way to confirm the expected argument combination for each family.

## Safe override heuristics

Prefer these overrides when adapting a preset:

- change `--out_dir` for a new experiment
- change `--num_envs` when testing backend limits
- change `--model_file` for evaluation / warm-start
- change `--devices` and `--master_port` for distributed launches
- change `--visualize` and `--video` for headless vs interactive runs

Avoid changing the YAML triad unless you are intentionally switching backend or task family.
