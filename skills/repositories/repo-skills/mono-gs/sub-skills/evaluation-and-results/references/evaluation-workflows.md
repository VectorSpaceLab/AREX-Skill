# Evaluation Workflows

## What `--eval` changes

The `slam.py --eval` branch overrides the loaded config before constructing the
SLAM object:

- `Results.save_results = True`
- `Results.use_gui = False`
- `Results.eval_rendering = True`
- `Results.use_wandb = True`

This makes the run headless and metric-oriented, but it also enables W&B unless
you disable W&B through the environment.

## Built-in evaluation command

From a MonoGS checkout with data and CUDA dependencies ready:

```bash
WANDB_MODE=disabled python slam.py --config configs/mono/tum/fr3_office.yaml --eval
```

Use `WANDB_MODE=disabled` for offline or unauthenticated environments. Omit it
only when the user explicitly wants W&B logging and has credentials/network
ready.

## W&B-free config-copy route

When a user wants rendering metrics but does not want `--eval` to force
`use_wandb=True`, create a copy of the target config and set:

```yaml
Results:
  save_results: true
  use_gui: false
  eval_rendering: true
  use_wandb: false
```

Then run without `--eval`:

```bash
python slam.py --config path/to/headless_eval_config.yaml
```

This still initializes W&B in disabled mode because `slam.py` uses
`mode="disabled"` when `Results.use_wandb` is false.

## Which configs are evaluation candidates

- Monocular: `configs/mono/tum/fr1_desk.yaml`, `fr2_xyz.yaml`, `fr3_office.yaml`
- RGB-D TUM: `configs/rgbd/tum/fr1_desk.yaml`, `fr2_xyz.yaml`, `fr3_office.yaml`
- RGB-D Replica: `configs/rgbd/replica/<office|room>.yaml` and `_sp.yaml`
- Stereo EuRoC: `configs/stereo/euroc/mh02.yaml`

Live RealSense configs are not good evaluation candidates because they do not
load fixed ground-truth trajectories from an offline dataset tree.

## Reproducibility cautions

MonoGS reports that multi-process performance has randomness from GPU
utilization. Treat single-run deltas as approximate unless the user has fixed the
dataset, GPU model, driver, PyTorch/CUDA versions, `single_thread` flags, and GUI
state. The paper-tested reference hardware was an RTX 4090; other GPUs can have
different FPS and memory behavior.
