# Evaluation troubleshooting

Use this reference before rerunning an evaluation job. Most failures are missing prerequisites, face-detection assumptions, temp-directory collisions, or backend mismatches.

## Quick triage

| Symptom | Likely cause | First action |
| --- | --- | --- |
| `Face not detected` during SyncNet confidence | S3FD found no usable face track, the face is too small/occluded, or the clip is too short | Inspect the clip and rerun with `--keep-temp` to review detector crops |
| `Real video failed FVD face extraction` or `Fake video failed FVD face extraction` | MediaPipe could not find a face in frames `20:36` | Use longer clips with a stable visible face in the sampled window |
| Missing checkpoint path | Required model file is absent or config path is empty | Stop and acquire/fix the checkpoint path before loading models |
| Accuracy uses maintainer-local `/mnt/...` paths | Shipped config was not edited for the current dataset | Override validation paths in the runner or copy/edit the YAML |
| Accuracy fails on CPU or is extremely slow | The source evaluation runs half-precision model validation and expects CUDA for realistic use | Run on CUDA or treat CPU-only as unsupported for accuracy |
| FVD returns unstable/NaN values on tiny sets | Covariance is ill-conditioned with too few samples | Use at least two videos per side, preferably many more; singleton mode is smoke-only |
| Temp files disappear or runs clobber each other | Source detector deletes `crop`, `video`, `frames`, and `temp` subdirs | Use unique `--temp-base-dir` values or the bundled runner's per-run temp roots |
| `pkg_resources` or audio import error | Incomplete setuptools/librosa audio stack | Ensure setuptools still provides `pkg_resources`; the verified inspection stack used setuptools 80.9.0 |
| `ffmpeg: not found` or silent conversion failure | FFmpeg is missing or not visible on `PATH` | Install/activate ffmpeg before metric execution |

## Checkpoint prerequisites

Treat these files as prerequisites, not optional runtime details:

| Capability | Required checkpoint/config | Why |
| --- | --- | --- |
| SyncNet confidence | `checkpoints/auxiliary/syncnet_v2.model` | Loaded by `SyncNetEval.loadParameters()` |
| SyncNet confidence face detector | `checkpoints/auxiliary/sfd_face.pth` | Loaded by S3FD detector internals |
| SyncNet accuracy | `config.ckpt.inference_ckpt_path` or `--inference-ckpt-path`, commonly `checkpoints/stable_syncnet.pt` | Loaded into `StableSyncNet` |
| FVD | `checkpoints/auxiliary/i3d_torchscript.pt` | TorchScript I3D feature extractor |
| HyperIQA visual-quality reference | `checkpoints/auxiliary/koniq_pretrained.pkl` | Loaded by preprocessing visual-quality filtering |
| Latent-space SyncNet accuracy | Stable Diffusion inpainting VAE cache or network access | Needed only when `config.data.latent_space: true` |

The source utility may try to download some missing auxiliary files. For reproducible evaluation, prefer an explicit preflight: either the file exists, or the user has approved download/network access.

## Face-detection failures

SyncNet confidence and FVD use different detectors and assumptions:

- SyncNet confidence uses S3FD in `eval/syncnet_detect.py`, scene detection, track filtering, and `min_track=50` by default.
- FVD uses MediaPipe face detection on a fixed 16-frame window from frames 20 through 35.
- HyperIQA does not detect faces, but it assumes decodable first/middle/last frames.

Actionable fixes:

- Prefer frontal, stable, well-lit clips.
- Avoid very short clips; FVD needs at least 36 frames and SyncNet confidence needs a track long enough to crop.
- For animated, profile, tiny, or occluded faces, expect detector failures even when the generated video looks acceptable.
- Use `--keep-temp` for SyncNet confidence and inspect the crop/detect output before changing metrics.
- Do not hide failed videos when reporting averages; include the failed count and representative error.

## Temporary directory handling

The source scripts aggressively recreate temp folders:

- `SyncNetEval.evaluate()` removes and recreates its `temp_dir`.
- `SyncNetDetector.__call__()` removes and recreates `crop`, `video`, `frames`, and `temp` under its `detect_results_dir`.
- The preprocessing AV-sync path creates per-process temp roots; mirror that pattern for parallel evaluation.

Safe practice:

```bash
python scripts/run_evaluation.py --repo-root /path/to/LatentSync sync-conf \
  --videos-dir outputs/candidates \
  --temp-base-dir temp/eval-run-001
```

Use one temp base per active job. Delete it after success unless the user explicitly needs detector artifacts.

## Backend and dependency checks

Verified inspection facts for the production environment included:

- Python 3.10.13.
- Torch 2.5.1+cu121 and torchvision 0.20.1+cu121 with CUDA allocation working.
- Diffusers 0.32.2, transformers 4.48.0, decord 0.6.0, mediapipe 0.10.11, onnxruntime-gpu 1.21.0, gradio 5.24.0, numpy 1.26.4.
- `librosa` 0.10.1 and `python_speech_features` available.
- Setuptools 80.9.0 restored `pkg_resources` imports.
- FFmpeg executable available.

For a new environment, check at least:

```bash
python - <<'PY'
import cv2, decord, mediapipe, torch, python_speech_features
import librosa
print(torch.__version__, torch.cuda.is_available())
PY
ffmpeg -version
```

Backend expectations by metric:

- SyncNet confidence can choose CPU when CUDA is missing, but CUDA is preferred and closer to the production path.
- SyncNet accuracy should be treated as CUDA-required for useful validation because the source path uses float16 model/data tensors.
- FVD is intentionally CPU-backed in the bundled runner after face extraction.
- HyperIQA visual-quality filtering is a preprocessing GPU path and raises `No GPUs found` when CUDA is absent.

## Config and data pitfalls

- The shipped `configs/syncnet/*.yaml` files include maintainer-local train/validation/cache paths; replace them before evaluation.
- `SyncNetDataset` requires either `data.val_fileslist` or `data.val_data_dir`.
- Validation clips should already be processed by the LatentSync data pipeline: FPS/audio resampling, face alignment, AV sync, and visual-quality filtering.
- If `data.latent_space: true`, the runner must load the Stable Diffusion inpainting VAE; use a pixel config for a simpler accuracy smoke check.
- If the dataset is empty, stop and fix the fileslist/directory instead of letting the dataloader loop indefinitely.

## When to stop early

Stop and surface a prerequisite/blocker when:

- A required checkpoint path is empty or missing.
- No mp4 files are present in the requested folder.
- Face extraction fails for every video.
- The chosen metric's backend is unavailable.
- The user asks for generation, training, or preprocessing rather than evaluation.
