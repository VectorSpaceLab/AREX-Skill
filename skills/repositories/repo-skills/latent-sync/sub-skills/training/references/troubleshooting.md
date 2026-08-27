# LatentSync Training Troubleshooting

Use this guide before starting expensive training and whenever a launch fails. The most common issues are stale placeholder paths, missing checkpoints, plain-`python` launches, and choosing a stage that exceeds per-GPU VRAM.

## Plain Python or Broken DDP Launch

Symptoms:

- `KeyError: 'RANK'`, missing `WORLD_SIZE`, or `LOCAL_RANK`-related failures.
- `RuntimeError: No GPUs available for training.`
- NCCL initialization failures before the dataloader starts.

Cause:

- `scripts.train_unet` and `scripts.train_syncnet` call `latentsync.utils.util.init_dist()`, which reads distributed environment variables and initializes NCCL.

Fix:

- Launch with `torchrun`, even for one GPU:
  ```bash
  torchrun --nnodes=1 --nproc_per_node=1 --master_port=25679 \
    -m scripts.train_unet --unet_config_path configs/unet/stage1.yaml
  ```
- Prefer the bundled renderer:
  ```bash
  python skills/disco/latent-sync/sub-skills/training/scripts/run_training.py \
    --repo-root . --config configs/unet/stage1.yaml --nproc-per-node 1
  ```
- Select GPUs with `CUDA_VISIBLE_DEVICES`, not with config fields.
- Keep `--nproc_per_node` no larger than the number of visible GPUs on the node. DDP replicates the model per process; it does not make `stage2_512` fit on smaller GPUs.

## Wrong Working Directory or Import Path

Symptoms:

- `FileNotFoundError: configs/audio.yaml`.
- `DDIMScheduler.from_pretrained("configs")` cannot find scheduler config.
- Checkpoint paths that exist from the repo root are reported missing.
- `ModuleNotFoundError: latentsync` or `ModuleNotFoundError: scripts`.

Fix:

- Run from the repository root, or pass `--repo-root` to the bundled helper. The wrapper sets the command working directory to the repo root.
- Because the repo has no `pyproject.toml`, `setup.py`, or `setup.cfg`, do not assume an installed package. Use module execution from the checkout root: `torchrun -m scripts.train_unet ...`.
- Avoid public runtime docs or configs that depend on one machine's absolute checkout path.

## Empty or Malformed Fileslist

Symptoms:

- Dataloader fails with unclear `random.randint` / empty-range errors.
- Training appears to hang while repeatedly printing video path errors.
- `ValueError: data_dir and fileslist cannot be both empty`.
- `decord` cannot open entries from the fileslist.

Causes:

- `train_fileslist` or `val_fileslist` points to a missing file.
- The fileslist has zero valid rows, blank rows, non-`.mp4` rows, or paths that are not readable from the training working directory.
- The config still uses shipped private `/mnt/...` paths.

Fix:

1. Regenerate the list with the bundled helper:
   ```bash
   python skills/disco/latent-sync/sub-skills/training/scripts/write_fileslist.py \
     --dataset-dir /data/processed/high_visual_quality/train \
     --output /data/latentsync/fileslists/train.txt \
     --overwrite
   ```
2. Run launch preflight before training:
   ```bash
   python skills/disco/latent-sync/sub-skills/training/scripts/run_training.py \
     --repo-root . --config configs/unet/stage1.yaml --preflight
   ```
3. For U-Net, prefer `train_fileslist`; the `train_data_dir` fallback scans only top-level `.mp4` files.
4. For SyncNet, provide both train and validation sources; `val_fileslist` or `val_data_dir` must resolve to real `.mp4` files.

## Checkpoint Path Failures

Symptoms:

- `FileNotFoundError` or `RuntimeError` while loading a checkpoint.
- U-Net loads a checkpoint but later quality is unexpectedly poor.
- Stage-2 U-Net reports `ValueError: SyncNet path is not provided`.
- Validation fails before or at the first checkpoint interval.

Checkpoint map:

| Path/config field | Used by | Notes |
| --- | --- | --- |
| U-Net `ckpt.resume_ckpt_path` | `scripts.train_unet` | Must be a U-Net checkpoint with `state_dict`, optionally `global_step`. Shipped configs point at `checkpoints/latentsync_unet.pt`. |
| SyncNet config `ckpt.resume_ckpt_path` | `scripts.train_syncnet` | Must be a SyncNet training checkpoint, not a U-Net checkpoint. |
| SyncNet config `ckpt.inference_ckpt_path` | U-Net stage-2 SyncNet supervision | `scripts.train_syncnet` does not use this, but U-Net loads it when `run.use_syncnet: true`. |
| `checkpoints/stable_syncnet.pt` | Default stage-2 U-Net supervision | Download or replace with a compatible `StableSyncNet` checkpoint. |
| `checkpoints/whisper/tiny.pt` or `small.pt` | U-Net audio features | `cross_attention_dim: 384` uses `tiny.pt`; `768` uses `small.pt`. |
| `checkpoints/auxiliary/syncnet_v2.model` | U-Net validation sync confidence path | Loaded by `scripts.train_unet` early; missing file can block U-Net training before checkpoint validation. |
| `checkpoints/auxiliary/vit_g_hybrid_pt_1200e_ssv2_ft.pth` | TREPA loss | Used when `pixel_space_supervise` and `trepa_loss_weight != 0`; source may try a Hugging Face download if missing. |

Fixes:

- Download the public checkpoints described in the README for the target release, and download `stable_syncnet.pt` before stage-2 U-Net training.
- Set stage-2 `data.syncnet_config_path` to a SyncNet config whose `model` section matches the checkpoint in `ckpt.inference_ckpt_path`.
- If running offline, pre-populate auxiliary/TREPA/LPIPS-related weights or disable optional losses deliberately in the copied config.
- Do not mix U-Net and SyncNet checkpoints; their `state_dict` keys and expected architectures differ.

## VRAM Out of Memory

Symptoms:

- CUDA OOM during VAE encode/decode, SyncNet loss, TREPA/LPIPS loss, or validation video generation.
- Training works for stage 1 but fails at stage 2.
- 512px stage-2 fails on 40GB-class GPUs.

Expected memory tiers from the README:

| Config | Approx. VRAM per GPU process |
| --- | ---: |
| `stage1.yaml` | 23 GB |
| `stage2.yaml` | 30 GB |
| `stage2_efficient.yaml` | 20 GB |
| `stage1_512.yaml` | 30 GB |
| `stage2_512.yaml` | 55 GB |

Fixes:

- Use `stage2_efficient.yaml` instead of `stage2.yaml` when memory is tight.
- Do not treat multi-GPU DDP as memory pooling; each process still needs the model and batch on one GPU.
- Keep U-Net `batch_size: 1` for first launches; increase only after memory is measured.
- Keep `mixed_precision_training: true` and `enable_gradient_checkpointing: true` unless debugging.
- Avoid `stage2_512.yaml` unless a single visible GPU has enough memory; the bundled wrapper refuses execution without `--ack-high-vram`.
- For SyncNet, reduce `data.batch_size`, reduce `num_val_samples`, or use gradient accumulation to preserve effective batch size.

## Config/Checkpoint Mismatch

Symptoms:

- Missing or unexpected keys during checkpoint load.
- Shape mismatch in `attn2.to_k`, `attn2.to_v`, `conv_in`, or `conv_out`.
- SyncNet visual encoder shape errors after changing `num_frames`, `latent_space`, or resolution.
- Training launches but appears to have partially reset important weights.

U-Net notes:

- `UNet3DConditionModel.load_state_dict` removes mismatched `conv_in`, `conv_out`, and cross-attention key/value weights before loading with `strict=False`. This can let a run start while silently reinitializing important layers.
- `cross_attention_dim` must match the Whisper checkpoint choice and the prior U-Net checkpoint. Shipped configs use `384` and `checkpoints/whisper/tiny.pt`.
- `in_channels: 13` and `out_channels: 4` are tied to latent/mask/reference concatenation and SD-style latent prediction. Do not change them casually.
- 512px v1.6 configs change `resolution`; the README says model structure and strategy are otherwise compatible.

SyncNet notes:

- Pixel-space 16-frame configs expect visual input channels `48` (`16 * 3`).
- Latent-space 16-frame config expects visual input channels `64` (`16 * 4`).
- If changing `num_frames`, update `visual_encoder.in_channels` and downsampling architecture according to `docs/syncnet_arch.md`.
- `lower_half: true` crops pixel frames after stacking channels; changing it changes visual input geometry and may require architecture changes.

Fix:

- Revert to the closest shipped config, change one axis at a time, and re-run command rendering/preflight.
- When using a custom checkpoint, keep the same config family that produced it.
- Treat partial U-Net checkpoint loads as intentional fine-tuning only if you understand which layers are reset.

## Validation and Output Confusion

Symptoms:

- Checkpoints exist but no validation videos or charts are found.
- Loss charts are under a different directory than expected.
- Resume starts from step 0.

Expected U-Net layout:

```text
<data.train_output_dir>/train-.../
  checkpoints/checkpoint-STEP.pt
  val_videos/val_video_STEP.mp4
  sync_conf_results/sync_conf_chart-STEP.png
```

Expected SyncNet layout:

```text
<data.train_output_dir>/train-.../
  checkpoints/checkpoint-STEP.pt
  loss_charts/loss_chart-STEP.png
```

Fixes:

- Look below the timestamped `train-*` directory, not directly under `train_output_dir`.
- U-Net validation occurs when `global_step % ckpt.save_ckpt_steps == 0`.
- SyncNet validation and charting occur when `global_step % run.validation_steps == 0`.
- To resume U-Net, set `ckpt.resume_ckpt_path` to a U-Net checkpoint with `global_step`; to resume SyncNet, use a SyncNet checkpoint with saved loss history.

## Environment Dependency Issues

Symptoms:

- `pkg_resources` import errors from audio/librosa-related dependencies.
- CUDA import succeeds but `torch.cuda.is_available()` is false.
- `ffmpeg` or video decode errors.

Fixes:

- Use a Python 3.10 CUDA environment compatible with the repo requirements. The inspected environment verified torch 2.5.1+cu121, torchvision 0.20.1+cu121, diffusers 0.32.2, transformers 4.48.0, decord, onnxruntime-gpu, gradio, numpy 1.26.4, ffmpeg, and setuptools 80.9.0.
- Ensure `ffmpeg` is on `PATH` before training or validation video generation.
- Confirm CUDA before launch:
  ```bash
  python - <<'PY'
  import torch
  print(torch.__version__, torch.cuda.is_available(), torch.cuda.device_count())
  PY
  ```
- If using isolated Python (`python -I`), expose the checkout root intentionally or run module commands from the repo root as the bundled helper does.
