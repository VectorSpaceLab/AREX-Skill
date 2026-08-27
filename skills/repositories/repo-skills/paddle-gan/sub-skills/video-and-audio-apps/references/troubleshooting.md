# Troubleshooting

## Stack readiness

| Symptom | Likely cause | What to do |
| --- | --- | --- |
| ffmpeg missing | The video helper layer cannot read or write frames | Run the bundled stack checker, then fix PATH or install ffmpeg before retrying. |
| imageio missing | Video read/write helpers cannot open clips | Install the missing dependency and rerun the stack checker. |
| librosa missing | Wav2Lip audio decode is not ready | Install the missing dependency and rerun the stack checker. |
| predictor import fails | A required dependency for that workflow is still absent | Fix the import error first; do not start inference from a partially loaded stack. |

## Motion and lip-sync failures

- `Face not detected!` in Wav2Lip: lower `resize_factor`, tighten `crop`, provide `box`, rotate the clip if needed, or switch detectors.
- `Mel contains nan!`: re-encode the audio, verify the file is not silent or broken, and retry with a clean waveform.
- `find_best_frame` errors: disable best-frame search unless face-alignment support is installed.
- Wav2Lip face-detection OOM: lower `face_det_batch_size` and `wav2lip_batch_size`, or shrink the input clip.
- First Order Motion OOM: lower `batch_size`, reduce `image_size`, or use `slice_size` to split the driving video.
- Multi-face First Order Motion looks misaligned: reduce `ratio` if faces are close together.

## Video restoration and SR failures

- Missing weights: keep `weight_path` explicit and stop if the stage is not available offline.
- `process_order` too large for CUDA memory: shorten the chain, lower resolution, and reduce `num_frames` before switching to a larger model family.
- Recurrent VSR memory pressure: prefer fewer frames per chunk and a lighter family such as `EDVR` or `RealSR`.
- DAIN-specific issues: treat DAIN as a static-graph workflow and only use it when interpolation is required.
- ffmpeg composition errors: check the input codec, confirm the clip is readable, and remove partial outputs before retrying.

## Boundary routing

- Single-image-only requests belong in image-and-face-apps.
- Exporting or consuming static `.pdmodel` / `.pdiparams` artifacts belongs in deployment-export.
- Dataset layout and preprocessing problems for LRS2, REDS, Vimeo90K, or similar corpora belong in data-preparation.

## Recommended first diagnostic

Run `scripts/check_video_stack.py` before any heavy media run. It is intentionally safe and does not run model inference or download weights.
