# LatentSync configuration and checkpoint map

Use this reference when choosing between configs or checking which checkpoints a workflow expects.

## Common constants

LatentSync workflows share a few media assumptions:

- `num_frames: 16` is the dominant frame window across inference, SyncNet, and most training/evaluation code.
- `video_fps: 25` and `audio_sample_rate: 16000` are the shared media assumptions.
- `configs/audio.yaml` and `configs/scheduler_config.json` are shared runtime files.
- `latentsync/utils/mask.png` is the fixed mask image used by inference.

## Workflow map

| Workflow | Main configs | Primary checkpoint/assets | Notes |
| --- | --- | --- | --- |
| Inference | `configs/unet/stage2_512.yaml`, `configs/unet/stage2.yaml` | `checkpoints/latentsync_unet.pt`, `checkpoints/whisper/tiny.pt` or `small.pt` | 512/v1.6 vs 256/v1.5 choice; prefer `stage2_512` only when VRAM is available. |
| Data preparation | `configs/syncnet/syncnet_16_pixel.yaml`, `syncnet_16_pixel_attn.yaml`, `syncnet_16_latent.yaml`, `syncnet_25_pixel.yaml` | `checkpoints/auxiliary/syncnet_v2.model`, `sfd_face.pth`, `koniq_pretrained.pkl` | Uses SyncNet, detector, and HyperIQA gates; see the data-preparation sub-skill for stage order. |
| U-Net training | `configs/unet/stage1.yaml`, `stage1_512.yaml`, `stage2.yaml`, `stage2_efficient.yaml`, `stage2_512.yaml` | `checkpoints/latentsync_unet.pt`, `checkpoints/stable_syncnet.pt`, Whisper checkpoint, optional TREPA weights | Stage 2 uses SyncNet supervision; `stage2_512` is high-VRAM. |
| SyncNet training | `configs/syncnet/syncnet_16_pixel.yaml`, `syncnet_16_pixel_attn.yaml`, `syncnet_16_latent.yaml` | processed `.mp4` files, `audio_mel_cache_dir` | Fileslists take precedence over directory fallbacks. |
| Evaluation | `configs/syncnet/*.yaml` for accuracy, `eval/fvd.py` data layout for FVD | `syncnet_v2.model`, `sfd_face.pth`, `i3d_torchscript.pt`, `stable_syncnet.pt` | Sync confidence and FVD use different detectors and temp-dir behavior. |

## Checkpoint selection cheat sheet

- `cross_attention_dim: 384` -> `checkpoints/whisper/tiny.pt`
- `cross_attention_dim: 768` -> `checkpoints/whisper/small.pt`
- `sync_av` keeps clips when `confidence >= 3` and `abs(offset) <= 6`
- `filter_visual_quality` keeps clips when HyperIQA score `>= 40`

## U-Net VRAM guide

| Config | Approximate VRAM per GPU |
| --- | ---: |
| `configs/unet/stage1.yaml` | 23 GB |
| `configs/unet/stage2.yaml` | 30 GB |
| `configs/unet/stage2_efficient.yaml` | 20 GB |
| `configs/unet/stage1_512.yaml` | 30 GB |
| `configs/unet/stage2_512.yaml` | 55 GB |

## When to read

- Before choosing an inference checkpoint/config pair.
- Before editing `configs/unet/*.yaml` or `configs/syncnet/*.yaml`.
- Before deciding whether a missing file is a bug or a prerequisite.
