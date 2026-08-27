# LatentSync Training Workflows

LatentSync training has two maintained entry points:

- U-Net: `torchrun -m scripts.train_unet --unet_config_path <configs/unet/*.yaml>`
- SyncNet: `torchrun -m scripts.train_syncnet --config_path <configs/syncnet/*.yaml>`

Both call the repo's distributed initializer, so launch with `torchrun` even for one GPU. The bundled `../scripts/run_training.py` helper renders the command and can execute it only when `--execute` is supplied.

## Preflight Sequence

1. **Start from a prepared video tree.** Training expects processed `.mp4` files, normally the output of the data-preparation flow such as `high_visual_quality/train` and `high_visual_quality/val`. Do not debug raw preprocessing stages here.
2. **Build file lists deliberately.** Prefer explicit fileslists over hard-coded private paths in the shipped configs.
3. **Edit a copied config.** Replace `train_fileslist`, `val_fileslist`, `train_data_dir`, `val_data_dir`, cache dirs, checkpoint paths, and `train_output_dir`.
4. **Choose a stage/variant.** Use the tables below and `configuration.md`; do not choose `stage2_512.yaml` for smoke checks.
5. **Render before running.** Use `run_training.py` without `--execute`, then add `--preflight` to catch empty/malformed file lists.
6. **Launch only after checkpoints and VRAM are ready.** U-Net stage-2 configs require SyncNet and auxiliary validation checkpoints; 512 stage-2 needs a very large per-GPU memory budget.

## Dataset File-List Preparation

The repo source tool `tools/write_fileslist.py` appends recursively gathered `.mp4` paths from hard-coded private directories. Use the bundled safe helper instead:

```bash
python skills/disco/latent-sync/sub-skills/training/scripts/write_fileslist.py \
  --dataset-dir /data/VoxCeleb2/high_visual_quality/train \
  --dataset-dir /data/HDTF/high_visual_quality/train \
  --output /data/latentsync/fileslists/train.txt
```

For validation:

```bash
python skills/disco/latent-sync/sub-skills/training/scripts/write_fileslist.py \
  --dataset-dir /data/VoxCeleb2/high_visual_quality/val \
  --output /data/latentsync/fileslists/val.txt
```

Important reader behavior from `latentsync/data/`:

- `UNetDataset` uses `data.train_fileslist` if it is non-empty. If it falls back to `data.train_data_dir`, it scans only top-level `.mp4` files, not recursively.
- `SyncNetDataset` uses a fileslist when provided; otherwise it recursively gathers `.mp4` files from `train_data_dir` or `val_data_dir`.
- Blank lines, non-`.mp4` entries, or missing paths can lead to unclear errors or endless retry loops in the dataset readers. Run `run_training.py --preflight` before long training.
- Fileslists should contain paths resolvable from the repository-root working directory. Absolute paths are simplest for cluster jobs.

## U-Net Training Workflow

The U-Net training script builds a distributed dataloader, DDIM scheduler from `configs/`, VAE from `stabilityai/sd-vae-ft-mse`, Whisper audio features from `checkpoints/whisper/*.pt`, and a LatentSync U-Net from `ckpt.resume_ckpt_path`. It writes a timestamped run under `data.train_output_dir`.

### U-Net Stage Selection

| Config | Resolution | Stage semantics | Approx. VRAM | Use when |
| --- | ---: | --- | ---: | --- |
| `configs/unet/stage1.yaml` | 256 | Full U-Net training with latent reconstruction; no pixel-space supervision or SyncNet loss. | 23 GB | First 256px training/fine-tuning stage; safer smoke target after data paths are tiny and checkpoints exist. |
| `configs/unet/stage2.yaml` | 256 | Pixel-space supervision, SyncNet loss, TREPA/LPIPS losses, temporal motion modules; trains selected motion/attention parameters. | 30 GB | Standard 256px stage-2 quality training when GPU memory is sufficient. |
| `configs/unet/stage2_efficient.yaml` | 256 | Lower-memory stage-2: decoder-side motion modules and audio cross-attention, TREPA disabled. | 20 GB | Preferred consumer/low-VRAM stage-2 path; may slightly reduce quality/temporal consistency. |
| `configs/unet/stage1_512.yaml` | 512 | Stage-1 behavior on 512px videos. | 30 GB | 512px/v1.6 data when stage-1 objective is intended. |
| `configs/unet/stage2_512.yaml` | 512 | Stage-2 behavior on 512px videos. | 55 GB | High-VRAM quality run only; not a casual smoke target and not suitable for 40GB-per-GPU hosts without changes. |

The source `train_unet.sh` currently launches one process with `configs/unet/stage1_512.yaml`. Treat it as an example shell shim, not a universal default.

### Render and Launch

Render the command:

```bash
python skills/disco/latent-sync/sub-skills/training/scripts/run_training.py \
  --repo-root . \
  --config configs/unet/stage2_efficient.yaml \
  --nproc-per-node 1
```

Preflight after editing data paths:

```bash
python skills/disco/latent-sync/sub-skills/training/scripts/run_training.py \
  --repo-root . \
  --config configs/unet/stage2_efficient.yaml \
  --nproc-per-node 1 \
  --preflight
```

Execute only when ready:

```bash
python skills/disco/latent-sync/sub-skills/training/scripts/run_training.py \
  --repo-root . \
  --config configs/unet/stage2_efficient.yaml \
  --nproc-per-node 1 \
  --execute
```

For `stage2_512.yaml`, the helper requires `--ack-high-vram` in addition to `--execute`.

### U-Net Outputs

For each launch, `scripts.train_unet` creates:

```text
<data.train_output_dir>/train-YYYY_MM_DD-HH:MM:SS/
  checkpoints/checkpoint-STEP.pt
  val_videos/val_video_STEP.mp4
  sync_conf_results/sync_conf_chart-STEP.png
  <copied unet config>
  <copied syncnet config>
```

Checkpoints contain at least `state_dict` and `global_step`. Resume by setting `ckpt.resume_ckpt_path` to a compatible U-Net checkpoint and keeping the chosen model config compatible.

## SyncNet Training Workflow

SyncNet training reads processed videos and mel spectrograms, builds positive and negative AV pairs, trains `StableSyncNet`, validates every `run.validation_steps`, and writes checkpoints/loss charts under `data.train_output_dir`.

### SyncNet Variant Selection

| Config | Representation | Visual input channels | Attention blocks | Use when |
| --- | --- | ---: | --- | --- |
| `configs/syncnet/syncnet_16_pixel.yaml` | Pixel frames, lower half by default | `16 * 3 = 48` | none | Baseline 16-frame pixel-space SyncNet. |
| `configs/syncnet/syncnet_16_pixel_attn.yaml` | Pixel frames, lower half by default | `16 * 3 = 48` | deeper audio/visual self-attention enabled | Preferred/default stronger SyncNet; U-Net configs point to it for sync supervision. |
| `configs/syncnet/syncnet_16_latent.yaml` | VAE latents | `16 * 4 = 64` | none | Latent-space SyncNet experiments; requires VAE encoding and matching checkpoint architecture. |

The source `train_syncnet.sh` launches one process with `configs/syncnet/syncnet_16_pixel_attn.yaml`.

### Render and Launch

```bash
python skills/disco/latent-sync/sub-skills/training/scripts/run_training.py \
  --repo-root . \
  --config configs/syncnet/syncnet_16_pixel_attn.yaml \
  --nproc-per-node 1 \
  --preflight
```

Then add `--execute` after fileslists, validation data, and output dirs are correct.

### SyncNet Outputs

```text
<data.train_output_dir>/train-YYYY_MM_DD-HH:MM:SS/
  checkpoints/checkpoint-STEP.pt
  loss_charts/loss_chart-STEP.png
  <copied syncnet config>
```

SyncNet training checkpoints store `state_dict`, `global_step`, and train/validation loss histories. Use `ckpt.resume_ckpt_path` only with checkpoints produced by `scripts.train_syncnet`, not with U-Net checkpoints or inference-only config paths.

## Post-Training Validation Notes

- U-Net validation video generation is part of `scripts.train_unet` at checkpoint intervals. Sync confidence charting uses the auxiliary SyncNet evaluation path, but deeper metric interpretation belongs to the evaluation sub-skill.
- SyncNet validation loss and loss charts are produced by `scripts.train_syncnet`. Accuracy evaluation on a held-out dataset belongs to the evaluation sub-skill.
- For smoke checks, prefer command rendering, config loading/import checks, and tiny fileslist fixtures. Do not start full training merely to verify this skill.
