# Deployment notes for Cog and Replicate

This context is reference-only. Use it when adapting LatentSync inference to a service interface; do not run deployment helpers as ordinary local inference.

## Cog configuration shape

The Cog config declares:

- GPU build enabled.
- CUDA version `12.1`.
- System packages: `ffmpeg` and `libgl1`.
- Python version `3.10.13`.
- Python requirements from `requirements.txt`.
- A build step that installs `pget`.
- Predictor entry point: `predict.py:Predictor`.

Operational caveats:

- The build and setup path is network-bound.
- The Cog environment is intended to own dependency installation; it is not a substitute for a local, already-prepared runtime tree.
- Keep ffmpeg and OpenCV system dependencies explicit in any derived container.

## Predictor behavior

`Predictor.setup()`:

- Downloads a model tarball to `checkpoints` when that directory does not exist.
- Creates `~/.cache/torch/hub/checkpoints`.
- Creates a symlink for `vgg16-397923af.pth` from `checkpoints/auxiliary/` into the torch hub cache.

`Predictor.predict(...)` inputs:

```text
video: Path                     Input video.
audio: Path                     Input audio.
guidance_scale: float           1 to 3, default 2.0.
inference_steps: int            20 to 50, default 20.
seed: int                       0 chooses a random seed; positive values are used directly.
```

Predictor command choices:

- Config path: `configs/unet/stage2.yaml`.
- Checkpoint: `checkpoints/latentsync_unet.pt`.
- Output: `/tmp/video_out.mp4`.
- It calls `python -m scripts.inference` through a shell string.
- It does not pass `--enable_deepcache`.

## Adaptation guidance

- For v1.6 512 inference, change the predictor config to `configs/unet/stage2_512.yaml` and confirm the checkpoint was trained for 512 resolution.
- Replace shell-string command assembly with an argument-list subprocess in any new deployment wrapper.
- Validate video/audio paths, checkpoint existence, config existence, ffmpeg availability, and CUDA before calling the model.
- Keep public API ranges aligned with README guidance: `guidance_scale` 1.0-3.0 and `inference_steps` 20-50.
- Return a unique output path per request if serving concurrent predictions; the reference predictor writes `/tmp/video_out.mp4` and is therefore not concurrency-safe without adaptation.
- Do not rely on Cog setup for ordinary local inference, because it downloads weights and mutates cache/symlink locations.
