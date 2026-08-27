# Metric semantics

Use this reference to interpret LatentSync evaluation numbers and decide whether a score is a real metric, a smoke check, or a preprocessing gate.

## SyncNet confidence and AV offset

Primary sources: `eval/eval_sync_conf.py`, `eval/syncnet_detect.py`, `eval/syncnet/syncnet_eval.py`, and `eval/detectors/`.

What happens:

1. S3FD detects and tracks faces after `ffmpeg` normalizes the video to 25 FPS and 16 kHz mono audio.
2. Each face track is cropped to a 224×224 face-track mp4.
3. `SyncNetEval.evaluate()` extracts visual features from 5-frame windows and audio features from matching MFCC windows.
4. It evaluates shifted audio/video distances across a window and reports:
   - `av_offset = vshift - minidx`
   - `confidence = median(mean_dists) - min_dist`
5. `syncnet_eval()` averages offsets and confidence across all detected face tracks in the input video.

Interpretation:

- Higher confidence is better.
- AV offset is an estimated frame shift at 25 FPS; inspect the sign in the source path before applying manual audio correction.
- The preprocessing `sync_av.py` gate keeps clips when `confidence >= 3` and `abs(av_offset) <= 6`.
- Generated-video ranking is usually relative: compare candidates produced with the same detector checkpoint, crop settings, and input duration.

What it is not:

- It is not a full perceptual quality metric.
- It is not a SyncNet checkpoint-validation accuracy number.
- It should not be treated as reliable when no face track or only a very short track is found.

## SyncNet accuracy

Primary sources: `eval/eval_syncnet_acc.py`, `latentsync/data/syncnet_dataset.py`, `latentsync/models/stable_syncnet.py`, and `configs/syncnet/*.yaml`.

What happens:

1. A SyncNet config defines audio/visual encoder channels, downsample factors, attention blocks, data resolution, frame count, batch size, and validation paths.
2. `SyncNetDataset` samples a video window and randomly chooses either the matching audio window (`y=1`) or a mismatched window from the same video (`y=0`).
3. The model returns normalized visual and audio embeddings.
4. Cosine similarity greater than `0.5` is classified as matching.
5. Accuracy is `correct / total * 100`.

Interpretation:

- Higher accuracy is better.
- This validates a SyncNet checkpoint on a processed validation split; it does not score a generated mp4 directly.
- The checkpoint and YAML architecture must match. A pixel checkpoint should not be evaluated with a latent config, and a 16-frame checkpoint should not be evaluated with a 25-frame config.
- The README says the released SyncNet reached about 94% accuracy on VoxCeleb2 and HDTF after data-pipeline processing; do not compare unprocessed data to that claim.

Config guide:

| Config | Meaning | Notes |
| --- | --- | --- |
| `syncnet_16_pixel_attn.yaml` | 16-frame pixel-space SyncNet with attention | Shipped accuracy script default and `checkpoints/stable_syncnet.pt` path |
| `syncnet_16_pixel.yaml` | 16-frame pixel-space SyncNet without attention | Useful for architecture comparison |
| `syncnet_16_latent.yaml` | 16-frame latent-space SyncNet | Requires Stable Diffusion VAE access/cache |
| `syncnet_25_pixel.yaml` | 25-frame pixel-space SyncNet | Architecture/data must match checkpoint |

## FVD

Primary sources: `eval/eval_fvd.py` and `eval/fvd.py`.

What happens:

1. MediaPipe detects a face in frames `20:36` of each mp4.
2. Each face crop is resized to 224×224.
3. The resulting tensors have shape `(batch, 16, 224, 224, 3)` and values in `[0, 1]`.
4. I3D features are extracted from real and fake batches.
5. Fréchet distance is computed from feature means and covariance matrices.

Interpretation:

- Lower FVD is better.
- FVD is a set-level comparison, not a single-video score.
- Use the same frame window, face detector, clip type, and sampling policy across compared runs.
- Very small sets can confirm that the CPU/backend path works, but they are not statistically meaningful. Prefer multiple videos per side; one video per side can produce unstable or NaN covariance.

Failure-sensitive assumptions:

- Each clip must be long enough for frames 20 through 35.
- A visible face must be detected in all sampled frames.
- The I3D TorchScript checkpoint must be available before metric execution.

## HyperIQA visual-quality score

Primary sources: `eval/hyper_iqa.py` and `preprocess/filter_visual_quality.py`.

What happens in preprocessing:

1. The filter reads the first, middle, and last frames of each video.
2. It normalizes and center-crops frames before running the HyperIQA-style model.
3. It uses `checkpoints/auxiliary/koniq_pretrained.pkl`.
4. It copies videos whose mean quality score is at least `40`.

Interpretation:

- Higher is better, with scores intended to be in a 0-100 visual-quality range.
- The LatentSync data pipeline treats `40` as the keep threshold.
- This is a visual cleanliness gate for data preparation, not a lip-sync metric and not an FVD substitute.

## SyncNet training curves

Primary sources: `eval/draw_syncnet_lines.py` and bundled `scripts/plot_syncnet_curves.py`.

The plot helper reads these keys from SyncNet training checkpoints:

- `train_step_list`
- `train_loss_list`
- `val_step_list`
- `val_loss_list`

Interpretation:

- Lower loss is better when comparing checkpoints from the same training setup.
- Curves explain training behavior; they do not replace SyncNet confidence, SyncNet accuracy, or FVD.

## Reporting checklist

When reporting evaluation results, include:

- Metric name and entry point.
- Repo/config/checkpoint names, without local private paths.
- Number of videos or validation batches scored.
- Any failed videos and the first actionable error.
- Backend used (`cuda`, `cpu`, or CPU-backed FVD).
- Whether the run was a smoke check or a meaningful full evaluation.
