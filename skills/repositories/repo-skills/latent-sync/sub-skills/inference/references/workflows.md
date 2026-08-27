# LatentSync inference workflows

This reference is self-contained for running LatentSync inference from a local runtime tree that contains the repository source, configs, assets, and checkpoints. Set `LATENTSYNC_REPO_ROOT` to that runtime tree or pass `--repo-root` explicitly.

## Prerequisites

Expected runtime assets:

- U-Net checkpoint: `checkpoints/latentsync_unet.pt` unless a custom checkpoint is supplied.
- Whisper checkpoint selected by config:
  - `configs/unet/stage2.yaml` and `configs/unet/stage2_512.yaml` set `model.cross_attention_dim: 384`, so they require `checkpoints/whisper/tiny.pt`.
  - A custom config with `model.cross_attention_dim: 768` requires `checkpoints/whisper/small.pt`.
- Mask image from the config: `latentsync/utils/mask.png` for the shipped configs.
- Scheduler config: `configs/scheduler_config.json` because `scripts.inference` loads the scheduler from `configs`.
- CUDA-capable PyTorch. The verified inspection environment used Python 3.10.13, torch 2.5.1+cu121, torchvision 0.20.1+cu121, diffusers 0.32.2, transformers 4.48.0, decord 0.6.0, mediapipe 0.10.11, gradio 5.24.0, onnxruntime-gpu 1.21.0, numpy 1.26.4, and ffmpeg 8.0.1.

The README states minimum inference VRAM of about 8 GB for LatentSync 1.5 and about 18 GB for LatentSync 1.6. The 512 config is therefore not a small CPU smoke test.

## Single-pair CLI flow

Use the bundled wrapper rather than calling the repo module directly. It checks input media and checkpoint paths before the denoising run.

```bash
python skills/disco/latent-sync/sub-skills/inference/scripts/run_inference.py \
  --repo-root "$LATENTSYNC_REPO_ROOT" \
  --config configs/unet/stage2_512.yaml \
  --checkpoint checkpoints/latentsync_unet.pt \
  --video-path assets/demo1_video.mp4 \
  --audio-path assets/demo1_audio.wav \
  --output video_out.mp4 \
  --steps 20 \
  --guidance-scale 1.5 \
  --enable-deepcache
```

For a quick prerequisite check without loading models or denoising:

```bash
python skills/disco/latent-sync/sub-skills/inference/scripts/run_inference.py \
  --repo-root "$LATENTSYNC_REPO_ROOT" \
  --preflight-only \
  --video-path assets/demo1_video.mp4 \
  --audio-path assets/demo1_audio.wav
```

The wrapper ultimately runs the same module shape as the demo shell script:

```bash
python -m scripts.inference \
  --unet_config_path configs/unet/stage2_512.yaml \
  --inference_ckpt_path checkpoints/latentsync_unet.pt \
  --video_path assets/demo1_video.mp4 \
  --audio_path assets/demo1_audio.wav \
  --video_out_path video_out.mp4 \
  --inference_steps 20 \
  --guidance_scale 1.5 \
  --enable_deepcache
```

Prefer simple paths without spaces or shell metacharacters. The wrapper rejects unsafe paths by default because the underlying pipeline uses shell-backed ffmpeg calls.

## Config and checkpoint choice

- `configs/unet/stage2_512.yaml`: released v1.6-style 512x512 inference, better sharpness for teeth/lips, higher VRAM demand.
- `configs/unet/stage2.yaml`: 256x256 inference compatible with v1.5-style checkpoints and lower VRAM demand.
- Both shipped configs keep `num_frames: 16`, `video_fps: 25`, `audio_sample_rate: 16000`, `audio_feat_length: [2, 2]`, `model.cross_attention_dim: 384`, and `model.add_audio_layer: true`.
- Match config resolution to the checkpoint lineage. The v1.6 changelog says model structure stayed compatible, but switching versions requires loading the matching checkpoint and changing the config `resolution`.
- If you are deciding which checkpoint/config should be produced or resumed, route to the training sub-skill when available. This inference sub-skill assumes the inference checkpoint already exists.

## Parameter tuning

- `--steps` / `--inference_steps`: README recommends 20-50. More steps can improve visual quality but slows generation.
- `--guidance-scale` / `--guidance_scale`: README recommends 1.0-3.0. Larger values can improve lip-sync accuracy but may increase distortion or jitter.
- `--seed`: deterministic seed when non-negative; `scripts.inference` calls `torch.seed()` when seed is `-1`.
- `--enable-deepcache`: mirrors `inference.sh` and the Gradio app. It creates a `DeepCacheSDHelper`, sets `cache_interval=3` and `cache_branch_id=0`, then enables it.
- `--temp-dir`: scratch location deleted and recreated by the pipeline, so never point it at valuable data.

## Small-batch flow

Use batch mode for a small number of videos, not for evaluation scoring. Batch generation is still one `scripts.inference` call per pair.

Pair-list format, one pair per line:

```text
# video<TAB>audio<TAB>optional_output
assets/demo1_video.mp4	assets/demo1_audio.wav	batch_outputs/demo1.mp4
assets/demo2_video.mp4	assets/demo2_audio.wav
```

Run:

```bash
python skills/disco/latent-sync/sub-skills/inference/scripts/run_inference.py \
  --repo-root "$LATENTSYNC_REPO_ROOT" \
  --pairs-file pairs.tsv \
  --output-dir batch_outputs \
  --config configs/unet/stage2_512.yaml \
  --checkpoint checkpoints/latentsync_unet.pt \
  --steps 20 \
  --guidance-scale 1.5 \
  --enable-deepcache
```

The wrapper also supports separate video and audio lists:

```bash
python skills/disco/latent-sync/sub-skills/inference/scripts/run_inference.py \
  --repo-root "$LATENTSYNC_REPO_ROOT" \
  --video-list video_files.txt \
  --audio-list audio_files.txt \
  --output-dir batch_outputs \
  --pairing zipped
```

Use `--pairing shuffled --seed 42` only when intentionally reproducing the evaluation helper's cross-pairing style. Route to `../evaluation/SKILL.md` if the next step is SyncNet confidence or FVD scoring.

## Gradio UI flow

The repo Gradio app builds the same inference arguments internally and enables DeepCache. The bundled launcher keeps public sharing and browser launch explicit.

Smoke import without serving:

```bash
python skills/disco/latent-sync/sub-skills/inference/scripts/launch_gradio.py \
  --repo-root "$LATENTSYNC_REPO_ROOT" \
  --smoke-import
```

Local-only launch:

```bash
python skills/disco/latent-sync/sub-skills/inference/scripts/launch_gradio.py \
  --repo-root "$LATENTSYNC_REPO_ROOT" \
  --server-name 127.0.0.1 \
  --server-port 7860 \
  --no-share \
  --no-browser
```

Only use `--share` when an explicit public Gradio tunnel is desired. Only use `--browser` when opening a local browser from this process is acceptable.

## Outputs and cleanup

- Single-pair default output is `video_out.mp4` relative to the runtime tree.
- Batch mode writes to `--output-dir` when a pair-list row does not provide an explicit output path.
- The pipeline writes temporary `video.mp4` and `audio.wav`, muxes them with ffmpeg, and then leaves the requested output path.
- The temp directory is deleted at the beginning of each pipeline call; isolate temp dirs for concurrent runs.
