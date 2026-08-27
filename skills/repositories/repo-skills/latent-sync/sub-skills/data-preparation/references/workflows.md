# LatentSync data-preparation workflow

LatentSync expects training/evaluation clips to pass through the same preprocessing path before they are used by U-Net or SyncNet training. The pipeline converts a raw `.mp4` tree into face-aligned, AV-synced, quality-filtered clips in `high_visual_quality/`.

Use [`../scripts/check_data_prep_inputs.py`](../scripts/check_data_prep_inputs.py) before running anything heavy, then use [`../scripts/run_data_pipeline.py`](../scripts/run_data_pipeline.py) to render or execute a parameterized plan.

## Default end-to-end order

The repository-level shell wrapper calls `preprocess.data_processing_pipeline` with:

- `total_num_workers=96`
- `per_gpu_num_workers=12`
- `resolution=256`
- `sync_conf_threshold=3`
- `temp_dir=temp`

The active stage order is:

1. Remove broken videos.
2. Resample video FPS to 25 and audio to 16 kHz.
3. Detect scene/shot boundaries.
4. Split shots into short segments.
5. Affine-transform faces and resize aligned crops.
6. Filter by SyncNet confidence and correct AV offset.
7. Filter by HyperIQA visual quality.

Two repo stages are useful but commented out of the default pipeline:

- `filter_high_resolution` before alignment, to reduce a large/noisy corpus by face-size.
- `remove_incorrect_affined` after alignment, to prune clips whose aligned outputs no longer contain exactly one face.

## Quick commands

Plan only, with no mutation:

```bash
python skills/disco/latent-sync/sub-skills/data-preparation/scripts/run_data_pipeline.py \
  --repo-root <latentsync-checkout> \
  --input-dir <workspace>/raw
```

Safe preflight with checkpoint and binary checks:

```bash
python skills/disco/latent-sync/sub-skills/data-preparation/scripts/check_data_prep_inputs.py \
  --repo-root <latentsync-checkout> \
  --input-dir <workspace>/raw
```

Stricter GPU/import preflight after entering the prepared environment:

```bash
python skills/disco/latent-sync/sub-skills/data-preparation/scripts/check_data_prep_inputs.py \
  --repo-root <latentsync-checkout> \
  --input-dir <workspace>/raw \
  --check-imports \
  --require-gpu
```

Execute the full pipeline only after the raw tree is disposable, because the first stage deletes corrupt files in place:

```bash
python skills/disco/latent-sync/sub-skills/data-preparation/scripts/run_data_pipeline.py \
  --repo-root <latentsync-checkout> \
  --input-dir <workspace>/raw \
  --temp-dir <fast-scratch>/latentsync-preprocess \
  --total-num-workers 96 \
  --per-gpu-num-workers 12 \
  --allow-destructive-inputs \
  --execute
```

CPU-only fixture run through segmentation:

```bash
python skills/disco/latent-sync/sub-skills/data-preparation/scripts/run_data_pipeline.py \
  --repo-root <latentsync-checkout> \
  --input-dir <workspace>/raw \
  --stop-after segment_videos \
  --allow-destructive-inputs \
  --execute
```

## Stage-by-stage flow

| Order | Stage key | Module/function | Input | Output | Compute | Mutation and gate behavior |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | `remove_broken_videos` | `preprocess/remove_broken_videos.py` → `remove_broken_videos_multiprocessing(input_dir, total_num_workers)` | raw input tree | raw input tree | CPU multiprocessing + `decord` | Destructive: tries `AVReader(video_path)` and deletes unreadable files. Run only on a copy of raw data. |
| 2 | `resample_fps_hz` | `preprocess/resample_fps_hz.py` → `resample_fps_hz_multiprocessing(input_dir, resampled_dir, total_num_workers)` | raw tree after prune | `resampled/` | CPU multiprocessing + `ffmpeg` | Rewrites clips to 25 FPS and audio to 16 kHz. If FPS already equals 25, video is stream-copied while audio is resampled. |
| 3 | `detect_shot` | `preprocess/detect_shot.py` → `detect_shot_multiprocessing(resampled_dir, shot_dir, total_num_workers)` | `resampled/` | `shot/` | CPU multiprocessing + `scenedetect` CLI | Uses adaptive detection with threshold `2`, then writes per-shot split videos. |
| 4 | `segment_videos` | `preprocess/segment_videos.py` → `segment_videos_multiprocessing(shot_dir, segmented_dir, total_num_workers)` | `shot/` | `segmented/` | CPU multiprocessing + `ffmpeg` | Splits each shot at roughly 5-second intervals with reset timestamps. |
| 5a | `filter_high_resolution` optional | `preprocess/filter_high_resolution.py` → `filter_high_resolution_multiprocessing(segmented_dir, high_resolution_dir, resolution, total_num_workers)` | `segmented/` | `high_resolution/` | CPU multiprocessing + MediaPipe + decode | Copies only clips whose detected face box is at least `resolution` pixels in width and height. Useful before GPU work on web-scale data. |
| 5 | `affine_transform` | `preprocess/affine_transform.py` → `affine_transform_multi_gpus(alignment_input_dir, affine_dir, temp_dir, resolution, per_gpu_workers_for_align)` | `segmented/` or `high_resolution/` | `affine_transformed/` | CUDA multiprocessing + InsightFace + ONNX Runtime GPU | Detects 106 face landmarks, aligns/warps each frame, resizes to `resolution`, writes video, extracts original audio, and muxes audio back. Clips with detection failures are skipped. |
| 5b | `remove_incorrect_affined` optional | `preprocess/remove_incorrect_affined.py` → `remove_incorrect_affined_multiprocessing(affine_dir, total_num_workers)` | `affine_transformed/` | `affine_transformed/` | CPU multiprocessing + MediaPipe | Destructive cleanup: deletes aligned clips unless every decoded frame has exactly one face. |
| 6 | `sync_av` | `preprocess/sync_av.py` → `sync_av_multi_gpus(affine_dir, av_synced_dir, temp_dir, per_gpu_num_workers, sync_conf_threshold)` | `affine_transformed/` | `av_synced_<threshold>/` | CUDA multiprocessing + S3FD + SyncNet + `ffmpeg` | Crops face tracks, evaluates SyncNet offset/confidence, keeps clips with `confidence >= threshold` and `abs(offset) <= 6`, then shifts audio when offset is non-zero. |
| 7 | `filter_visual_quality` | `preprocess/filter_visual_quality.py` → `filter_visual_quality_multi_gpus(av_synced_dir, high_visual_quality_dir, per_gpu_num_workers)` | `av_synced_<threshold>/` | `high_visual_quality/` | CUDA multiprocessing + HyperIQA + `torchvision` | Samples first/middle/last frames, predicts quality, and copies clips with score `>= 40`. |

## Multiprocessing and GPU model

### CPU stages

The CPU stages use `multiprocessing.Pool` with `total_num_workers`. They are safe to plan without CUDA, but they still need the relevant native tools and Python packages:

- `ffmpeg` for resampling and segmentation.
- `scenedetect` CLI for shot detection.
- `decord` for broken-video probing.
- MediaPipe for optional face-size and post-affine checks.

Do not set `total_num_workers` higher than the host can support for simultaneous video decodes and `ffmpeg` subprocesses. On small fixtures, a low value such as `1` or `2` is easier to debug.

### GPU stages

The GPU stages inspect `torch.cuda.device_count()` and spawn `num_devices * per_gpu_workers` processes. The source wrapper halves the alignment worker count by calling alignment with `per_gpu_num_workers // 2`; the bundled runner preserves that behavior while clamping the value to at least one worker.

Practical tuning:

- Start with `--per-gpu-num-workers 1` for tiny fixtures or debugging.
- Raise the worker count only after checkpoint loading, temp directory writes, and one or two clips pass.
- `affine_transform` is usually the most memory-sensitive stage because it repeatedly runs face detection and frame alignment.
- `sync_av` and `filter_visual_quality` also need CUDA and model checkpoints but are primarily gate/scoring stages.

## Checkpoints and model-side prerequisites

The data-prep pipeline expects these auxiliary files relative to the LatentSync checkout root:

```text
checkpoints/auxiliary/syncnet_v2.model
checkpoints/auxiliary/sfd_face.pth
checkpoints/auxiliary/koniq_pretrained.pkl
```

The source `preprocess.data_processing_pipeline` calls `check_model_and_download()` for those three files before the default run. The bundled runner refuses to start GPU-backed stages when they are missing unless the caller explicitly passes `--allow-downloads`. In offline or locked-down environments, place the checkpoints manually and keep `--allow-downloads` unset.

HyperIQA also constructs a ResNet-50 backbone with pretrained ImageNet weights before loading the KonIQ checkpoint. If the torch model cache is empty and network access is blocked, the visual-quality stage can fail before it reaches the KonIQ weights. Treat this as an environment/cache prerequisite and resolve it before worker pools start.

## Recovery and reruns

Every non-destructive transformation writes a new sibling directory. A failed run usually does not require starting over from raw videos.

Recommended recovery pattern:

1. Identify the last complete sibling directory by checking non-empty `.mp4` counts.
2. Remove only the partial downstream directory and stale scratch tree for the failed stage.
3. Re-render the plan with the same parameters.
4. Use `--start-at <stage>` when the upstream stage directories are already complete, or use `--stop-after <stage>` for fixture verification.

Examples:

```bash
# Resume from already-complete segmentation into GPU alignment and later gates.
python skills/disco/latent-sync/sub-skills/data-preparation/scripts/run_data_pipeline.py \
  --repo-root <latentsync-checkout> \
  --input-dir <workspace>/raw \
  --start-at affine_transform \
  --allow-destructive-inputs \
  --execute
```

```bash
# Re-run only through sync filtering after aligned clips are complete.
python skills/disco/latent-sync/sub-skills/data-preparation/scripts/run_data_pipeline.py \
  --repo-root <latentsync-checkout> \
  --input-dir <workspace>/raw \
  --start-at sync_av \
  --stop-after sync_av \
  --allow-destructive-inputs \
  --execute
```

`temp_dir` is scratch. Do not put important data there; alignment and SyncNet routines create and delete temporary audio/video/frame files during processing.

## Explicitly excluded helper

`tools/download_web_videos.py` is not bundled as a runnable helper. It is network-bound, depends on external video services and downloader tools, and is unsafe for reproducible runtime use. Acquire raw videos outside this sub-skill, then run the pipeline on an explicit local `.mp4` tree.
