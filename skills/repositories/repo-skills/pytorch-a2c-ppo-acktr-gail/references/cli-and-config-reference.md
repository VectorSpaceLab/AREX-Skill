# CLI and Configuration Reference

## When to read

Read this for shared parser flags and source-script mapping before choosing a sub-skill. For full training recipes, continue to `sub-skills/training-workflows/`.

## Package and command surfaces

| Surface | Runtime role | Skill-owned replacement or route |
| --- | --- | --- |
| Training entrypoint (`main.py` in a checkout/copy) | Runs A2C, PPO, ACKTR, and optional GAIL training. | `sub-skills/training-workflows/scripts/build_training_command.py` prints safe current commands; training details live in `sub-skills/training-workflows/references/training-and-evaluation.md`. |
| Playback entrypoint (`enjoy.py` in a checkout/copy) | Loads checkpoint tuple and renders policy actions in a loop. | Command builder `--mode enjoy`; details in `training-workflows`. |
| `gail_experts/convert_to_pytorch.py` | Converts expert HDF5 demonstrations to `.pt`. | `sub-skills/gail-imitation/scripts/convert_gail_h5_to_pt.py` is the bundled safe converter. |
| `generate_tmux_yaml.py` / `run_all.yaml` | Historical multi-seed launch templates. | Reference-only because templates can contain stale `--tau`; use command builder instead. |
| `visualize.ipynb` | Historical plotting notebook for monitor CSV logs. | Reference-only; log artifact notes live in `references/data-and-artifacts.md`. |

## Shared parser facts

Important flags verified from the parser and CLI help:

- `--algo` accepts `a2c`, `ppo`, or `acktr`.
- `--gail` enables imitation learning and expects expert files under `--gail-experts-dir` named `trajs_<env-prefix>.pt`.
- `--gae-lambda` is the current GAE parameter; do not use stale `--tau` from old generated experiment files.
- `--recurrent-policy` is rejected with `--algo acktr`.
- `--use-proper-time-limits` changes return computation through time-limit masks and is recommended for MuJoCo-like control tasks.
- `--no-cuda` forces CPU; otherwise CUDA is used only when `torch.cuda.is_available()` returns true.
- `--save-dir` stores checkpoints under `<save-dir>/<algo>/<env-name>.pt`.
- `--log-dir` is cleaned of existing `*.monitor.csv` files before training starts.

## Safe command construction

Use the bundled helper to avoid stale flags and accidental execution:

```bash
python sub-skills/training-workflows/scripts/build_training_command.py \
  --preset mujoco-ppo \
  --env-name Reacher-v2 \
  --no-cuda \
  --log-dir runs/reacher-smoke \
  --seed 0
```

The helper prints a command. It does not import Gym or start training.
