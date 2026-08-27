# Evaluation workflows

This reference routes finished LatentSync artifacts to the right metric or helper. Use evaluation when the input is already a candidate video, a real/fake video set, a SyncNet checkpoint, or a finished training checkpoint with logged loss curves.

## Decision table

| Goal | Entry point | Use this because | Do not use when |
| --- | --- | --- | --- |
| Score one candidate mp4 | `run_evaluation.py sync-conf --video-path` | Reports SyncNet confidence and AV offset for a finished clip | You still need to generate the clip |
| Score a folder of generated mp4s | `run_evaluation.py sync-conf --videos-dir` | Produces per-video scores plus average confidence/offset | You need distributional visual quality instead of sync |
| Validate a SyncNet checkpoint | `run_evaluation.py syncnet-acc` | Tests matched vs mismatched audio/video classification on processed validation data | You are evaluating a generated video, not a SyncNet model |
| Compare real and generated sets | `run_evaluation.py fvd` | Computes lower-is-better FVD on MediaPipe face crops using an I3D checkpoint | You only have one debug clip or no visible face window |
| Plot SyncNet loss curves | `plot_syncnet_curves.py` | Reads `train_step_list`, `train_loss_list`, `val_step_list`, and `val_loss_list` from training checkpoints | You need a video metric |
| Produce candidate batches before scoring | `eval/inference_videos.py` pattern, routed through inference details | Creates many generated mp4s for later metric scoring | You need single-example inference or UI usage |
| Understand quality filtering | HyperIQA reference in `eval/hyper_iqa.py` | Explains the visual-quality gate used by preprocessing | You want to run raw preprocessing stages here |

## Bundled runner conventions

Run the bundled helper from this sub-skill directory, or pass its full path from another location:

```bash
python scripts/run_evaluation.py --repo-root /path/to/LatentSync sync-conf --video-path outputs/candidate.mp4
```

Rules:

- `--repo-root` is the LatentSync checkout to import and operate on; it defaults to the current directory.
- Relative media, config, checkpoint, temp, and output paths resolve against `--repo-root`.
- The helper validates important prerequisites before importing model checkpoints.
- The helper prints a JSON summary after the human-readable source output.
- Use `--max-videos` or `--max-batches` for smoke checks before expensive full runs.

## SyncNet confidence workflow

Use this for generated/candidate videos when the question is “how well does the mouth motion sync to the audio?”

Source behavior:

1. `eval/eval_sync_conf.py` chooses `cuda` when available, otherwise CPU.
2. `SyncNetDetector` in `eval/syncnet_detect.py` uses the S3FD detector, converts the input to 25 FPS, extracts frames/audio with `ffmpeg`, detects/ tracks faces, and writes cropped face-track mp4s.
3. `SyncNetEval.evaluate()` in `eval/syncnet/syncnet_eval.py` extracts 224×224 frames and 16 kHz MFCC audio, compares shifted audio/video embeddings, and returns `(av_offset, min_dist, confidence)`.
4. The wrapper averages confidence and AV offset across detected crops.

Prerequisites:

- Candidate mp4(s) with a visible face track.
- `ffmpeg` on `PATH`.
- `checkpoints/auxiliary/syncnet_v2.model`.
- `checkpoints/auxiliary/sfd_face.pth`.
- Python dependencies for Torch, OpenCV, SciPy, `python_speech_features`, and scene detection.

Single video:

```bash
python scripts/run_evaluation.py --repo-root /path/to/LatentSync sync-conf \
  --video-path outputs/candidate.mp4 \
  --temp-base-dir temp/eval-sync-conf
```

Batch folder:

```bash
python scripts/run_evaluation.py --repo-root /path/to/LatentSync sync-conf \
  --videos-dir outputs/candidates \
  --max-videos 25 \
  --temp-base-dir temp/eval-sync-conf
```

Use `--keep-temp` only when debugging detector crops. Do not share one temp root between active jobs unless the helper is creating per-run subdirectories inside it.

## SyncNet accuracy workflow

Use this for a trained SyncNet checkpoint, not for finished generated clips.

Source behavior:

1. `eval/eval_syncnet_acc.py` loads a `configs/syncnet/*.yaml` file.
2. `SyncNetDataset` reads either `data.val_fileslist` or `data.val_data_dir`, samples true and false audio/video windows, caches mels under `data.audio_mel_cache_dir`, and returns 16- or 25-frame examples depending on the config.
3. `StableSyncNet` embeds frames and audio; cosine similarity above `0.5` is classified as matching.
4. Accuracy is `correct / total * 100` over the requested validation batches.

Prerequisites:

- Processed validation videos from the LatentSync data-preparation pipeline. The README explicitly warns that released SyncNet expects affine-transformed, AV-adjusted pipeline data.
- A config matching the checkpoint architecture and resolution.
- `config.ckpt.inference_ckpt_path` or `--inference-ckpt-path` pointing at a checkpoint such as `checkpoints/stable_syncnet.pt`.
- CUDA for faithful/realistic execution; the runner intentionally fails early instead of pretending a CPU-only half-precision validation is a good substitute.

Smoke run with overrides:

```bash
python scripts/run_evaluation.py --repo-root /path/to/LatentSync syncnet-acc \
  --config-path configs/syncnet/syncnet_16_pixel_attn.yaml \
  --inference-ckpt-path checkpoints/stable_syncnet.pt \
  --val-data-dir data/processed/val \
  --audio-mel-cache-dir temp/syncnet-mel-cache \
  --batch-size 8 \
  --num-workers 2 \
  --max-batches 2
```

Do not run the shipped config unedited if it still contains maintainer-local validation paths.

## FVD workflow

Use this for batch-level distributional comparison between real and generated videos.

Source behavior:

1. `eval/eval_fvd.py` uses MediaPipe face detection.
2. For each mp4, it samples frames `20:36`, detects one face per frame, and resizes crops to 224×224.
3. `eval/fvd.py` extracts I3D features from `(batch, frames, height, width, channels)` tensors and computes Fréchet distance.
4. The source forces the final feature model to CPU in `eval_fvd()`. The bundled runner also keeps I3D inference on CPU for a safe alternative path.

Prerequisites:

- `checkpoints/auxiliary/i3d_torchscript.pt`.
- `mediapipe`, `decord`, `opencv`, `torch`, and CPU memory for I3D feature extraction.
- Clips with at least 36 frames and a visible face in frames 20 through 35.
- Prefer at least two videos per side for covariance; singleton FVD is only a smoke check.

Example:

```bash
python scripts/run_evaluation.py --repo-root /path/to/LatentSync fvd \
  --real-dir data/real_eval \
  --fake-dir outputs/generated_eval \
  --max-videos 50
```

For a tiny smoke fixture with one video per side, add `--allow-singleton-fvd` and treat the numeric result as a backend check, not a publishable metric.

## Batch candidate generation support

`eval/inference_videos.py` is included as evidence because it shows how maintainers create randomized video/audio pairs before evaluation. Its `__main__` block contains maintainer-local file lists and output paths, so do not run it directly.

Safe use pattern:

- Route checkpoint/config/media details through the inference sub-skill.
- If you import `inference_video_from_fileslist()` manually, provide explicit `video_fileslist`, `audio_fileslist`, `output_dir`, `unet_config_path`, `ckpt_path`, `guidance_scale`, and `seed` arguments.
- Score the generated output folder afterward with SyncNet confidence and/or FVD.

## SyncNet curve plotting workflow

Use this after SyncNet training when the user wants loss curves rather than metric evaluation.

```bash
python scripts/plot_syncnet_curves.py --repo-root /path/to/LatentSync \
  output/syncnet/run-a/checkpoints/checkpoint-20000.pt \
  output/syncnet/run-b/checkpoints/checkpoint-20000.pt \
  --labels baseline stable-syncnet \
  --output reports/syncnet_curve_comparison.png
```

The checkpoint must contain the curve keys saved by the SyncNet training script. If validation keys are absent, use `--no-val` or plot only checkpoints that include validation lists.
