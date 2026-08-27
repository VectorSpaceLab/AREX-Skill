# Safe Gradio Web Demo

GroundingDINO web integrations should use the package APIs directly and keep environment setup outside the app process. The original Gradio demo pattern is useful for UI shape and Hugging Face checkpoint loading, but it also ran package build and `pip install` commands at import/run time. Do not preserve those side effects in production or reusable demos.

## Safe Wrapper

Use the bundled wrapper:

```bash
python sub-skills/integrations/scripts/grounding_dino_gradio_app.py --help
```

Local checkpoint, no network download:

```bash
python sub-skills/integrations/scripts/grounding_dino_gradio_app.py \
  --config /path/to/GroundingDINO_SwinT_OGC.py \
  --checkpoint /path/to/groundingdino_swint_ogc.pth \
  --device cpu \
  --server-name 127.0.0.1 \
  --server-port 7579
```

Explicit Hugging Face download when the user wants the script to fetch weights:

```bash
python sub-skills/integrations/scripts/grounding_dino_gradio_app.py \
  --config /path/to/GroundingDINO_SwinT_OGC.py \
  --checkpoint /path/to/groundingdino_swint_ogc.pth \
  --hf-repo-id ShilongLiu/GroundingDINO \
  --hf-filename groundingdino_swint_ogc.pth \
  --device cpu
```

The `--checkpoint` path is still required when using Hugging Face arguments; it is the local target path where the downloaded or cached file is copied for repeatable later launches. Use the actual config and checkpoint paths from the user's installed or deployed GroundingDINO environment; do not assume a repository checkout is present.

## CLI Options

| Option | Required | Meaning |
| --- | --- | --- |
| `--config PATH` | yes | GroundingDINO model config, commonly named `GroundingDINO_SwinT_OGC.py` or `GroundingDINO_SwinB_cfg.py`. |
| `--checkpoint PATH` | yes | Local checkpoint file to load, or local target path when paired with Hugging Face download options. |
| `--hf-repo-id ID` | no | Hugging Face repository to download from; no download occurs unless this and `--hf-filename` are both set. |
| `--hf-filename NAME` | no | Checkpoint filename inside the Hugging Face repo. |
| `--device DEVICE` | no | `cpu`, `cuda`, or a CUDA device string. CPU is safer but slower. |
| `--server-name HOST` | no | Gradio bind host. Use `127.0.0.1` for local-only demos; use `0.0.0.0` only when exposing on a trusted network. |
| `--server-port PORT` | no | Gradio port. |
| `--share` | no | Requests a public Gradio share URL; use only when the user accepts the exposure. |

`--help` works without importing Gradio, downloading weights, importing Hugging Face Hub, or touching a model checkpoint.

## App Flow

1. Parse arguments and validate `--config`.
2. If `--hf-repo-id` and `--hf-filename` are provided, import `huggingface_hub`, call `hf_hub_download`, and copy the cached checkpoint to `--checkpoint`.
3. If no Hugging Face args are provided, require that `--checkpoint` already exists.
4. Import `gradio` only after argument validation, then load the model with `groundingdino.util.inference.load_model`.
5. Build a Gradio UI with a PIL image upload, text prompt, box-threshold slider, text-threshold slider, and annotated PIL output.
6. On each prediction, convert the uploaded image to RGB, apply the same resize/tensor/normalize transform used by GroundingDINO inference, run `predict`, annotate with `annotate`, convert BGR annotation output back to RGB, and return a PIL image.

## UI Defaults

| UI field | Recommended default | Notes |
| --- | --- | --- |
| Detection prompt | Empty text box | Encourage prompts like `cat . dog .` or lowercase phrases ending in periods. |
| Box threshold | `0.25` | Lower values show more boxes and more false positives. |
| Text threshold | `0.25` | Lower values attach more phrases; too low can produce noisy labels. |
| Image type | PIL/RGB | Gradio should pass `type="pil"`; convert to `.convert("RGB")` before inference. |
| Output type | PIL/RGB | `annotate` returns BGR ndarray, so convert with `cv2.COLOR_BGR2RGB` before creating the output image. |

## Integration Checklist

- Install optional UI packages outside the app process: `gradio` for the UI and `huggingface_hub` only if the app downloads checkpoints.
- Keep model config and checkpoint paths explicit. Do not hard-code repository checkout paths into a reusable app.
- Prefer local-only launch for development: `--server-name 127.0.0.1` and no `--share`.
- Use `--device cpu` for portable demos and `--device cuda` only after checking GPU availability and memory.
- Normalize image color contracts: Gradio/PIL is RGB, OpenCV is BGR, and `annotate` returns BGR.
- Route deeper inference behavior, token spans, class prompts, and model API details to `../inference/`.

## Validation Signals

- `python sub-skills/integrations/scripts/grounding_dino_gradio_app.py --help` exits successfully without optional dependencies.
- Launch without `gradio` installed fails with a short install hint rather than a stack trace.
- Launch with `--hf-repo-id` but missing `--hf-filename` fails before any network call.
- Launch with a missing local checkpoint and no Hugging Face args fails before importing Gradio or loading the model.
- A successful prediction returns a PIL RGB image with boxes and labels, not a BGR-tinted output.
