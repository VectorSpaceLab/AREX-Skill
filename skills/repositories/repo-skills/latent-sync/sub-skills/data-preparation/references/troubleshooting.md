# LatentSync data-preparation troubleshooting

Use the preflight checker first:

```bash
python skills/disco/latent-sync/sub-skills/data-preparation/scripts/check_data_prep_inputs.py \
  --repo-root <latentsync-checkout> \
  --input-dir <workspace>/raw
```

Add `--check-imports --require-gpu` only inside the prepared Python environment.

## 1. Install and import failures

### Common symptoms

- `ModuleNotFoundError` for `decord`, `mediapipe`, `onnxruntime`, `insightface`, `kornia`, `scenedetect`, `python_speech_features`, or `eval`/`latentsync` modules.
- `torch` imports, but `torch.cuda.is_available()` is false.
- NumPy ABI errors after upgrading packages.
- `setuptools`/package metadata errors in an environment that otherwise imports Python.

### Verified baseline

This sub-skill was drafted against an inspection environment where these imports and versions were verified:

| Component | Verified fact |
| --- | --- |
| Python | `3.10.13` |
| PyTorch | `torch 2.5.1+cu121`, CUDA tensor allocation on `cuda:0` passed |
| TorchVision | `0.20.1+cu121` |
| Diffusers | `0.32.2` |
| Transformers | `4.48.0` |
| Decord | `0.6.0` |
| MediaPipe | `0.10.11` |
| ONNX Runtime GPU | `1.21.0` |
| Gradio | `5.24.0` |
| NumPy | `1.26.4` |
| Setuptools | `80.9.0` |
| FFmpeg | `8.0.1` |

The repo has no `pyproject.toml`, `setup.py`, or `setup.cfg`; helper scripts therefore accept `--repo-root` and add the checkout to `sys.path` when they need to call repo modules.

### Fixes

- Recreate the private environment or restore the verified `numpy`/`setuptools` baseline if ABI/import drift appears.
- Run from the environment that can import CUDA PyTorch, `decord`, `mediapipe`, and `onnxruntime-gpu`.
- Pass `--repo-root` to bundled helpers when the checkout is not the current working directory.
- Verify both Python packages and CLIs: `scenedetect` must be executable, and `ffmpeg` must be on `PATH`.

## 2. Codec, audio, and scene-detection failures

### Common symptoms

- `ffmpeg: command not found`.
- `scenedetect` exits immediately or creates no shot splits.
- Resampled outputs are empty or missing audio.
- SyncNet detection fails during frame/audio extraction.
- `remove_broken_videos` deletes many more clips than expected.

### What to check

- `ffmpeg -version` succeeds from the same shell used for preprocessing.
- `scenedetect --help` succeeds.
- Raw clips contain both video and audio streams.
- Raw clips are not zero-byte placeholders or partially downloaded files.
- The first stage is running on a disposable copy because it deletes unreadable clips in place.

### Fixes

- Install/expose `ffmpeg` and PySceneDetect in the active environment.
- Run `remove_broken_videos` on a tiny sample before the full corpus.
- Keep problematic files in a quarantine copy if you need to investigate codec issues later.
- For extremely short clips, expect little or no useful output after shot detection and segmentation.

## 3. Missing auxiliary checkpoints

### Common symptoms

- The runner refuses to start GPU stages and names missing prerequisites.
- Source code tries to run `huggingface-cli download` for auxiliary files.
- Worker pools crash while loading SyncNet, S3FD, InsightFace, or HyperIQA.

### Required files

```text
checkpoints/auxiliary/syncnet_v2.model
checkpoints/auxiliary/sfd_face.pth
checkpoints/auxiliary/koniq_pretrained.pkl
```

### Fixes

- Prefer manual placement of these files in offline or restricted environments.
- Run the preflight checker before GPU work; do not wait for a worker traceback.
- Use the runner's `--allow-downloads` only when network downloads are allowed by the task and environment.
- If HyperIQA fails while constructing its ResNet-50 backbone, ensure the ImageNet ResNet-50 weights are already cached for Torch model-zoo or temporarily allow that controlled download.

## 4. Face detection and affine-alignment failures

### Common symptoms

- `Face not detected` in alignment.
- Many clips are skipped in `affine_transform`.
- `remove_incorrect_affined` deletes most aligned clips.
- ONNX Runtime reports provider errors.
- Alignment succeeds for some GPUs but not others.

### What the code does

- `latentsync/utils/face_detector.py` uses InsightFace `FaceAnalysis` with `providers=["CUDAExecutionProvider"]` and `root="checkpoints/auxiliary"`.
- `latentsync/utils/image_processor.py` refuses CPU face detection for affine transformation.
- Face candidates are rejected if too small, oddly shaped, low confidence, or absent.
- The affine path computes eyebrow/nose landmark centers, aligns/warps the face, resizes to `resolution`, then muxes the original audio back.
- Optional `remove_incorrect_affined.py` uses MediaPipe to require exactly one detected face in every decoded frame.

### Fixes

- Confirm `onnxruntime-gpu` is installed and can use CUDA.
- Use clips with a single clear frontal or near-frontal talking face.
- Enable `--include-high-resolution` when source videos include tiny faces.
- Lower `--per-gpu-num-workers` to isolate OOM or temp-file races.
- Debug a single short clip first, then scale workers.

## 5. SyncNet confidence and AV-offset gate failures

### Common symptoms

- `Face not detected` during SyncNet crop extraction.
- Few or no clips appear under `av_synced_<threshold>/`.
- Logs show low confidence or offsets outside the accepted range.
- `syncnet_v2.model` load fails.

### Gate logic

`sync_av` keeps a clip only when:

- SyncNet confidence is greater than or equal to `sync_conf_threshold` (default `3`).
- Absolute AV offset is at most `6` frames.

For non-zero offsets inside the allowed range, audio is shifted by `offset / 25` seconds.

### Fixes

- Verify `checkpoints/auxiliary/syncnet_v2.model` and `checkpoints/auxiliary/sfd_face.pth` are present.
- Check that aligned clips still show a clear mouth region.
- Lower the threshold only when recall is more important than strict filtering.
- Keep the default threshold for training-quality corpora unless you have an explicit reason to change it.

## 6. HyperIQA visual-quality failures

### Common symptoms

- Missing `koniq_pretrained.pkl`.
- Torch model-zoo attempts an unexpected ResNet-50 download.
- Many clips are rejected after AV sync.
- CUDA OOM during quality scoring.

### Gate logic

`filter_visual_quality` samples the first, middle, and last frames, applies center crop and ImageNet normalization, builds HyperIQA's target network from hypernetwork outputs, and copies only clips whose mean quality score is at least `40`.

### Fixes

- Ensure `koniq_pretrained.pkl` is present before launching worker pools.
- Pre-cache ResNet-50 weights if the environment is offline.
- Lower `--per-gpu-num-workers` if the scoring workers OOM.
- Treat poor source resolution, motion blur, and compression artifacts as data issues, not pipeline bugs.

## 7. GPU and multiprocessing failures

### Common symptoms

- `RuntimeError: No GPUs found`.
- CUDA allocation fails in a worker process.
- Worker output is sparse and the parent process appears stuck.
- Temporary audio/video files collide or disappear.

### What to check

- `CUDA_VISIBLE_DEVICES` exposes intended GPUs.
- `torch.cuda.device_count()` is greater than zero.
- `torch.tensor([1.0], device="cuda:0")` can allocate.
- `--per-gpu-num-workers` is conservative for available VRAM.
- `temp_dir` is unique for this run and not shared with another pipeline.

### Fixes

- Start with `--per-gpu-num-workers 1`.
- Increase workers only after a tiny fixture passes.
- Use a fast local scratch directory, not a slow network mount.
- If alignment temp-file collisions are suspected, keep one worker per GPU for the alignment pass.

## 8. Temp-dir and rerun failures

### Common symptoms

- Old `crop/`, `video/`, `frames/`, or `syncnet_eval_results/` files affect a rerun.
- `temp_dir` is not writable.
- A partial downstream tree blocks expected output because the source stages skip files whose output already exists.
- Unrelated code deletes `temp/` while preprocessing is still running.

### Fixes

- Assign a run-specific `--temp-dir` on fast local disk.
- Delete stale scratch directories before retrying failed GPU stages.
- Delete only the partial downstream output tree; preserve complete upstream stage trees.
- Use `--start-at` and `--stop-after` in the runner to resume from a known complete stage.
- Do not run multiple LatentSync pipelines with the same `temp_dir`.

## 9. Threshold and data-retention tuning

| Gate | Default | Effect of raising | Effect of lowering |
| --- | --- | --- | --- |
| Face-size resolution | `256` | Keeps fewer but larger-face clips | Keeps more clips but may degrade alignment/training quality |
| Sync confidence | `3` | Stricter AV-sync quality | More clips, potentially worse lip-sync supervision |
| AV offset limit | `6` frames | Hard-coded in source `sync_av`; not exposed by default runner | Requires source edit/wrapper extension |
| HyperIQA quality | `40` | Stricter visual quality | More low-quality clips enter training |

When the goal is high-quality training data, prefer fixing source quality before weakening gates.
