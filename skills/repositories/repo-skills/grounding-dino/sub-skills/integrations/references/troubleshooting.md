# Integrations Troubleshooting

## Quick Diagnosis Matrix

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Source Gradio demo starts installing packages or building the repo | The original demo used `os.system` setup/install calls | Use `scripts/grounding_dino_gradio_app.py`; install dependencies outside the app process. |
| `ModuleNotFoundError: gradio` | Optional UI dependency is missing | Install Gradio in the chosen app environment, then rerun. `--help` does not require it. |
| `ModuleNotFoundError: huggingface_hub` | Hugging Face download was requested without the optional package | Install `huggingface_hub` or provide an already-downloaded `--checkpoint`. |
| Hugging Face download fails | Network, authentication, repo id, filename, proxy, or cache issue | Verify `--hf-repo-id`, `--hf-filename`, connectivity, and access. Retry with a local checkpoint for offline deployments. |
| Missing checkpoint error before launch | `--checkpoint` path does not exist and no HF download args were supplied | Download the checkpoint separately or provide both HF args to let the wrapper fetch it. |
| CUDA selected but app fails or OOMs | GPU unavailable, wrong CUDA stack, or model/editor memory pressure | Use `--device cpu` for web smoke tests, lower concurrent requests, or isolate heavy diffusion/SAM stages. |
| CPU app works but is slow | GroundingDINO inference on CPU is latency-heavy | Use CPU for correctness demos only; use GPU for interactive demos when available. |
| Annotated output has swapped colors | `annotate` returns BGR, while PIL/Gradio expect RGB | Convert with `cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB)` before creating a PIL image. |
| SAM masks are shifted or wrong size | Boxes are still normalized `cxcywh` or were scaled to the wrong image | Convert boxes to pixel `xyxy` using the original image width/height before calling SAM. |
| GLIGEN boxes are rejected or edits happen in wrong places | Box format mismatch or phrase count mismatch | Use normalized `xyxy` boxes and ensure one phrase per box after filtering. |
| Stable Diffusion edit affects the wrong area | Mask convention or resize mismatch | Resize image and mask together; confirm white pixels mean edit for the selected pipeline. |

## Unsafe Source Demo Behavior

Do not import or run source demo code that mutates the Python environment from inside the app. A web process should not execute setup/build commands or install packages while serving requests. Safer pattern:

1. Create or choose an environment outside the app.
2. Install GroundingDINO and optional UI/download packages explicitly.
3. Run the bundled wrapper with explicit config/checkpoint paths.
4. Keep downloads opt-in via `--hf-repo-id` and `--hf-filename`.

## Optional Dependency Checks

The bundled wrapper delays optional imports until they are needed:

- `gradio` is checked only when launching the web UI.
- `huggingface_hub` is checked only when HF download arguments are present.
- `--help` avoids all optional imports and model loading.

Install guidance should be short and environment-neutral, for example:

```bash
python -m pip install gradio huggingface_hub
```

Pin versions only when the target deployment has a known compatibility requirement.

## Network And Cache Failures

For reproducible apps, prefer a local checkpoint path. Hugging Face downloads are useful for demos but can fail because of offline hosts, rate limits, authentication, proxies, wrong filenames, or changed repository contents.

Validation steps:

- Confirm the repo id and filename exactly match the checkpoint entry.
- Try the app with an already-downloaded checkpoint to isolate network from model-loading issues.
- Keep the local checkpoint file after a successful download so future runs do not require network.
- Avoid downloading from inside request handlers; download before model loading.

## Device, Latency, And Memory

- CPU mode is portable and useful for smoke tests, but expect slow predictions and a less interactive UI.
- GPU mode improves latency but can fail if PyTorch/CUDA, custom ops, or driver versions are mismatched.
- Diffusion, GLIGEN, and SAM can consume far more memory than GroundingDINO alone. Treat them as separate services or separate environments when practical.
- For public Gradio demos, use queued requests and conservative concurrency to avoid memory spikes.

## RGB/BGR And Box Formats

GroundingDINO integration bugs often come from implicit conversions.

- PIL and Gradio images are RGB.
- `load_image` returns an RGB ndarray plus a transformed tensor.
- OpenCV file reads are BGR.
- The `Model` wrapper's `preprocess_image` path expects BGR input.
- `annotate` returns BGR.
- `predict` returns normalized `cxcywh` boxes.
- SAM-style segmentation generally expects pixel `xyxy` boxes.
- GLIGEN-style generation often expects normalized `xyxy` boxes.

When debugging, log image shape, color-space assumption, box min/max values, and box format at every handoff.

## External Model Separation

Stable Diffusion, GLIGEN, SAM, Grounded-SAM, and other notebook ecosystems are not part of GroundingDINO's base runtime. Common failure causes include huge downloads, pinned `diffusers` versions, CUDA-only code paths, model-license gates, and incompatible dependency constraints. Build those integrations as staged pipelines: first verify GroundingDINO detections and converted boxes, then invoke the external model stack.
