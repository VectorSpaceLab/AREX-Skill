# Inference troubleshooting

Run `scripts/run_inference.py --preflight-only` before expensive inference. Most common failures can be found before model load.

## Missing checkpoint or wrong config

Symptoms:

- `checkpoint not found` from the wrapper.
- `FileNotFoundError` or `torch.load` failure for `checkpoints/latentsync_unet.pt`.
- Poor quality, blurred output, or shape/key warnings after mixing a checkpoint with the wrong resolution config.

Fixes:

1. Confirm the U-Net checkpoint path exists and is readable.
2. Confirm the Whisper checkpoint required by `model.cross_attention_dim` exists:
   - `384`: `checkpoints/whisper/tiny.pt`.
   - `768`: `checkpoints/whisper/small.pt`.
3. Use `configs/unet/stage2_512.yaml` for v1.6-style 512 inference and `configs/unet/stage2.yaml` for v1.5-style 256 inference.
4. Confirm `configs/scheduler_config.json` exists because the scheduler is loaded from `configs`.
5. If the task is to train or select a new checkpoint lineage, route to the training sub-skill instead of guessing here.

## CUDA or GPU memory failure

Symptoms:

- `torch.cuda.is_available() == False`.
- `CUDAExecutionProvider` failures from face detection.
- CUDA out-of-memory during VAE, U-Net, or chunk denoising.
- 512 inference starts but fails after model load.

Fixes:

1. Use a CUDA-enabled torch build and verify a small CUDA tensor allocation before the run.
2. Use `configs/unet/stage2.yaml` with a matching 256 checkpoint when the GPU cannot handle 512 inference.
3. Keep `--steps` near 20 for smoke runs.
4. Close other GPU processes or select a less busy device via the environment before launch.
5. Do not attempt CPU face detection; `ImageProcessor.affine_transform` explicitly raises `NotImplementedError` when face detection is CPU-only.

## ffmpeg and codec errors

Symptoms:

- `ffmpeg not found`.
- Empty video frames or `Error: Could not open video.`
- ffmpeg muxing fails at the end of a long run.
- Paths with spaces or special characters fail even though the files exist.

Fixes:

1. Put a working `ffmpeg` binary on `PATH`; the verified inspection environment used ffmpeg 8.0.1.
2. Preflight media paths with the bundled wrapper.
3. Avoid spaces, quotes, semicolons, shell variables, parentheses, and other shell-sensitive characters in input, output, and temp paths. The underlying reader and muxer use shell-backed ffmpeg calls.
4. Use short local mp4/wav files for smoke tests.
5. Keep `--temp-dir` disposable because the pipeline deletes and recreates it.

## Face detection and alignment failures

Symptoms:

- No face is detected, or later code fails because a face/landmark is `None`.
- InsightFace or ONNX Runtime provider errors.
- `libGL` / OpenCV import errors.
- Output has badly placed or warped mouth region.

Fixes:

1. Use videos with a clear, frontal, sufficiently large face. The detector filters tiny, extreme-aspect, low-confidence faces.
2. Confirm auxiliary detector assets exist under `checkpoints/auxiliary/`; `FaceAnalysis` is initialized with that root and `CUDAExecutionProvider`.
3. Confirm `onnxruntime-gpu` is installed and CUDA is visible.
4. Install system OpenCV dependencies such as `libgl1` in container deployments.
5. For no-face or occluded videos, fail or choose a better input rather than treating it as a model-quality issue.

## Path and working-directory errors

Symptoms:

- `ModuleNotFoundError: latentsync` or `No module named scripts.inference`.
- Config paths exist from one directory but not another.
- Mask path fails despite the file being present in the runtime tree.

Fixes:

1. Pass `--repo-root` to bundled helpers.
2. Run helper scripts from any directory; they set the child process working directory to `--repo-root`.
3. Keep config-relative assets, especially `latentsync/utils/mask.png`, available under the runtime root.
4. Remember the repository has no packaging metadata, so editable install assumptions are weaker than running from the runtime root.

## DeepCache errors

Symptoms:

- Import failure for `DeepCache` before argparse or before inference starts.
- Output differences when comparing DeepCache and non-DeepCache runs.

Fixes:

1. Ensure the `DeepCache` package is installed in the inference Python. The repo module imports it at top level even when `--enable_deepcache` is not passed.
2. Disable `--enable-deepcache` for a comparison run, but do not expect that to bypass a missing package import.
3. Keep `--seed` fixed when comparing outputs.

## Gradio launch issues

Symptoms:

- The UI starts a public tunnel unexpectedly.
- Browser opens on a headless host.
- Uploads fail only after pressing the process button.

Fixes:

1. Use `scripts/launch_gradio.py --no-share --no-browser` for local-only serving.
2. Use `--smoke-import` before serving to verify the app imports.
3. Keep `--share` opt-in and document who can access the tunnel.
4. Preflight the checkpoint/config/demo assets first with `scripts/run_inference.py --preflight-only`.

## Offline model-cache failures

Symptoms:

- `AutoencoderKL.from_pretrained("stabilityai/sd-vae-ft-mse")` tries to reach the network.
- Cog setup attempts remote weight download.

Fixes:

1. Populate the Hugging Face cache for the Stable Diffusion VAE before offline inference.
2. Treat Cog/Replicate setup as deployment-specific and network-bound; see `references/deployment.md`.
3. For local inference, make model assets available before launch rather than relying on runtime downloads.
