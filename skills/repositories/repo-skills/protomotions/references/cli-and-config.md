# CLI and configuration contract

## Top-level CLI

`protomotions` dispatches three commands:

```bash
protomotions info [--json]
protomotions train-agent <training args>
protomotions inference-agent <inference args>
```

`protomotions info --json` is the safest first command because it avoids raising on missing optional simulator modules and reports package version, asset root, simulator-module availability, and Isaac Sim EULA opt-in state.

## Training CLI essentials

Required training arguments:

- `--robot-name`: one of the registered robot factory names such as `g1`, `h1_2`, `smpl`, `smplx`, `amp`, or `soma23`.
- `--simulator`: backend name such as `isaaclab`, `isaacgym`, `newton`, `genesis`, or `mujoco`.
- `--num-envs`: number of parallel environments per process/GPU.
- `--batch-size`: PPO batch size per process/GPU.
- `--motion-file`: MotionLib `.pt`, `.yaml`, or single motion path expected by the experiment.
- `--experiment-path`: Python experiment config file.
- `--experiment-name`: output/resume run name.

Common optional flags:

- `--checkpoint`: warm-start from an explicit checkpoint when using a new experiment name.
- `--use-wandb`, `--wandb-project`: W&B logging.
- `--ngpu`, `--nodes`: distributed training scale.
- `--use-slurm`: register SLURM autoresume behavior.
- `--training-max-steps` or `--training-max-iterations`: bounded runs.
- `--create-config-only`: create config artifacts without training; useful when migrating old checkpoints.
- `--overrides key=value ...`: scalar config overrides saved into the run.

## Inference CLI essentials

Required inference arguments:

- `--checkpoint`: path to `last.ckpt` or compatible checkpoint.
- `--simulator`: backend to use for inference.

Useful optional flags:

- `--full-eval`: evaluate the motion set and exit instead of running an interactive loop.
- `--headless`: disable rendering.
- `--num-envs`: parallel evaluation envs; use more for full evaluation when the backend supports it.
- `--motion-file`: replace the checkpoint's motion source.
- `--scenes-file`: replace the checkpoint's scene source.
- `--overrides`: scalar inference overrides.
- `--command-source target=keyboard`: make target-control inference interactive with W/A/S/D when the experiment has a target control component.

## Config object lifecycle

Training first builds configs from:

1. `robot_config(args.robot_name)`;
2. `simulator_config(args.simulator, robot_cfg, args.headless, args.num_envs, args.experiment_name)`;
3. optional experiment `configure_robot_and_simulator()`;
4. experiment `terrain_config()`, `scene_lib_config()`, `motion_lib_config()`, `env_config()`, and optional `agent_config()`;
5. scalar CLI `--overrides`.

The run saves:

- `config.yaml`: CLI args plus W&B ID;
- `resolved_configs.pt`: exact Python object graph and primary resume source;
- `resolved_configs.yaml`: best-effort readable sidecar;
- `experiment_config.py`: copy of the experiment file;
- `resolved_configs_inference.pt` and YAML sidecar for inference;
- checkpoints such as `last.ckpt` and sometimes `inference_last.ckpt`.

Never edit a `resolved_configs.yaml` expecting it to affect runtime. For small changes, use `--overrides` on a new run. For large changes, create a new experiment config or run `--create-config-only` and move the resulting `.pt` artifact deliberately.

## Resume and warm-start rules

- Same `--experiment-name` with existing results resumes from saved configs; training CLI overrides are ignored during resume because the saved `.pt` config is authoritative.
- New `--experiment-name` plus `--checkpoint` warm-starts model weights into freshly built configs.
- Use `last.ckpt` for resume/warm-start. Use `inference_last.ckpt` only for inference/share paths when the model card says it is intended for that role.

## Cross-simulator inference

`protomotions.inference_agent` can update simulator config target fields when switching simulators, but policy transfer still depends on physics compatibility and training randomization. Prefer `mujoco` for quick G1/H1 deployment validation; do not assume SMPL/SMPL-X spherical-joint policies transfer cleanly to MuJoCo/Newton.
