# CLI reference

## When to read

Read this when translating user requests into ACT++ command arguments. These command shapes describe the repository CLIs and are intentionally checkout-agnostic: run them from a prepared ACT++ checkout, or adapt them through the bundled checker/wrapper scripts that accept `--repo-root`.

## Environment prefix for commands

For headless simulation and training hosts, set:

```bash
export MUJOCO_GL=egl
```

For model training/eval and VINN workflows, confirm CUDA first:

```bash
python scripts/check_environment.py
```

## Simulation and data utilities

| Command shape | Purpose | Notes |
| --- | --- | --- |
| `python record_sim_episodes.py --task_name sim_transfer_cube_scripted --dataset_dir <dataset-dir> --num_episodes 50` | Generate scripted transfer-cube demos. | Uses EE-space policy rollout, then joint-space replay. Add `--onscreen_render` only on an interactive display. |
| `python record_sim_episodes.py --task_name sim_insertion_scripted --dataset_dir <dataset-dir> --num_episodes 50` | Generate scripted insertion demos. | Same pipeline with insertion scripted policy. |
| `python visualize_episodes.py --dataset_dir <dataset-dir> --episode_idx 0` | Save `episode_0_video.mp4` and `episode_0_qpos.png`. | Add `--ismirror` to visualize `mirror_episode_0.hdf5`. |
| `python replay_episodes.py --dataset_path <dataset-dir>/episode_0.hdf5` | Replay actions in the transfer-cube sim and save a replay MP4. | The script currently uses transfer cube regardless of source task. |
| `python postprocess_episodes.py --dataset_dir <dataset-dir> --num_episodes 50` | Create mirrored/compressed episodes. | Writes `mirror_episode_<idx>.hdf5`; check `/compress_len` if decoding fails. |
| `python compress_data.py --dataset_dir <dataset-dir>` | Batch-compress uncompressed HDF5 episodes into `<dataset-dir>_compressed`. | Keeps non-image datasets and JPEG-compresses RGB images. |
| `python truncate_data.py --dataset_dir <dataset-dir>` | Truncate compressed episodes into `<dataset-dir>_truncated`. | Uses hard-coded `TRUNCATE_LEN = 2250`. |

## ACT / CNNMLP / Diffusion training and evaluation

Current `imitate_episodes.py` uses step-based training. Prefer `--num_steps`; older docs may show `--num_epochs` for this same workflow.

### ACT training template

```bash
python imitate_episodes.py \
  --task_name sim_transfer_cube_scripted \
  --ckpt_dir <ckpt-dir> \
  --policy_class ACT \
  --kl_weight 10 \
  --chunk_size 100 \
  --hidden_dim 512 \
  --batch_size 8 \
  --dim_feedforward 3200 \
  --num_steps 100000 \
  --eval_every 2000 \
  --validate_every 2000 \
  --save_every 2000 \
  --lr 1e-5 \
  --seed 0
```

Outputs include `config.pkl`, `dataset_stats.pkl`, `policy_step_<step>_seed_<seed>.ckpt`, `policy_last.ckpt`, and `policy_best.ckpt`.

### Evaluation template

```bash
python imitate_episodes.py \
  --eval \
  --task_name sim_transfer_cube_scripted \
  --ckpt_dir <ckpt-dir> \
  --policy_class ACT \
  --kl_weight 10 \
  --chunk_size 100 \
  --hidden_dim 512 \
  --batch_size 8 \
  --dim_feedforward 3200 \
  --num_steps 1 \
  --lr 1e-5 \
  --seed 0
```

Evaluation loads `policy_last.ckpt` and `dataset_stats.pkl` from `ckpt_dir`, then writes `result_policy_last.txt`. Use `--temporal_agg` for temporal action aggregation.

### Diffusion template differences

Use `--policy_class Diffusion` and supply `--chunk_size`, `--batch_size`, `--num_steps`, and `--lr`. Diffusion uses action min/max normalization, image augmentation, robomimic visual encoders, diffusers schedulers, and CUDA.

### Latent model training

`train_latent_model.py` expects a trained VQ ACT `policy_last.ckpt` in `ckpt_dir` and uses epoch-based arguments:

```bash
python train_latent_model.py \
  --task_name sim_transfer_cube_scripted \
  --ckpt_dir <ckpt-dir> \
  --policy_class ACT \
  --batch_size 8 \
  --seed 0 \
  --num_epochs 1000 \
  --lr 1e-4 \
  --kl_weight 10 \
  --chunk_size 100 \
  --hidden_dim 512 \
  --dim_feedforward 3200 \
  --use_vq \
  --vq_class <classes> \
  --vq_dim <dim>
```

## VINN offline utilities

| Command shape | Purpose | Notes |
| --- | --- | --- |
| `python vinn_cache_feature.py --ckpt_path <byol-task-DUMMY-seed-N.pt> --dataset_dir <dataset-dir>` | Cache per-camera ResNet18 features for every episode. | Replaces `DUMMY` in checkpoint path with each camera name. Requires CUDA. |
| `python sub-skills/vinn-offline/scripts/select_k.py --dataset-dir <dataset-dir> --ckpt-dir <out-dir>` | Non-interactive k-selection over cached VINN features. | Bundled replacement for the source k-selection logic without its interactive breakpoint. |

Avoid unattended calls to the raw k-selection/eval scripts until you read [VINN troubleshooting](../sub-skills/vinn-offline/references/troubleshooting.md); one script opens `IPython.embed()`, and the eval script hard-codes a real-robot branch.
