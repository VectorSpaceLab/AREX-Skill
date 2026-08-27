# Cross-cutting Troubleshooting

Use this root troubleshooting page for install/import/backend/model-placement problems that affect several workflow families. Use sub-skill troubleshooting for workflow-specific sampler, prompt, IC-LoRA, HDR, mask, sparse-track, Q8, or STG issues.

## Nodes do not appear in ComfyUI

Symptoms:

- The LTXVideo category is absent after installing the custom nodes.
- ComfyUI logs an import failure for this custom-node folder.
- Static inspection fails before `NODE_CLASS_MAPPINGS` is available.

Likely causes and fixes:

1. **ComfyUI runtime is missing or not on the Python path.** This repo imports `comfy`, `comfy_extras`, `nodes`, and `comfy_api.latest`; a plain Python environment without ComfyUI cannot import it.
2. **The custom-node folder is not loadable.** Install through ComfyUI Manager or place the checkout under ComfyUI `custom_nodes`, then restart ComfyUI.
3. **Dependencies were installed into the wrong Python.** Install this repo's `requirements.txt` in the same Python/venv used by ComfyUI.
4. **Use the static helper.** Run `../scripts/inspect_custom_node_package.py --repo-root <ComfyUI-LTXVideo-folder> --comfyui-root <ComfyUI-root> --json` to confirm that the package loads and reports node mappings.

## CUDA or torch backend is wrong

Symptoms:

- `torch.cuda.is_available()` is false in the ComfyUI environment.
- ComfyUI or PyTorch reports a CUDA wheel/driver mismatch.
- Native generation starts but immediately OOMs or falls back to CPU.

Recovery:

- Install a CUDA-enabled torch build that matches the GPU driver and current ComfyUI release; do not rely on a CPU-only wheel for native generation.
- The README expects CUDA and recommends 32GB+ VRAM. If the user's GPU has less headroom, reduce resolution/frames, use two-stage or tiled decode carefully, and route graph changes to `core-generation`.
- If ComfyUI logs a warning recommending cu130+ for optimized CUDA operations on modern NVIDIA GPUs, follow current ComfyUI release guidance when native generation or optimized operations fail. The warning is distinct from a basic CUDA allocation failure.

## `comfy_kitchen` or torch custom-op schema import errors

Symptom examples:

- Import fails inside `comfy_kitchen` while registering a custom op.
- Error text mentions `torch.library.custom_op`, `infer_schema`, or unsupported typed parameters.

Recovery:

- Use a newer CUDA-enabled torch build compatible with the installed ComfyUI requirements. During construction, an older CUDA torch build failed this way and a newer CUDA torch build resolved the import path.
- Re-run `python -m pip check` in the ComfyUI environment after changing torch/ComfyUI packages.

## Kornia pyramid import error

Symptom:

```text
ImportError: cannot import name 'pad' from 'kornia.geometry.transform.pyramid'
```

Cause:

- `pyramid_blending.py` imports `pad` from Kornia's pyramid module. Newer Kornia releases may move/remove that symbol.

Recovery:

- Use a Kornia version compatible with the current ComfyUI-LTXVideo source. `kornia==0.7.1` was verified during skill construction.
- After changing Kornia, restart ComfyUI and rerun a static node import check.

## Missing model files or wrong folders

Symptoms:

- Checkpoint/LoRA/upscaler/text encoder combo boxes are empty.
- Gemma loader reports no `config.json` in the selected folder.
- Two-stage or IC-LoRA workflows fail only after asset loading begins.

Recovery:

- Check [model and backend requirements](model-and-backend-requirements.md) for the model-folder table.
- Put LTX checkpoints under `models/checkpoints`, latent upscalers under `models/latent_upscale_models`, LoRAs under `models/loras`, and complete Gemma folders under `models/text_encoders`.
- Route local/API Gemma details to `prompt-conditioning`; route sampler/upscaler wiring to `core-generation`; route IC-LoRA/HDR/T2A assets to `specialized-workflows`.

## Guide frame-index and latent-shape confusion

Symptoms:

- Conditioning frames appear at the wrong time.
- A guide video fails with a frame-index assertion or rounded index.
- Latent shape or frame count mismatches appear when adding guides/masks.

Recovery:

- Distinguish pixel frames from latent frames. Video VAE temporal scaling means pixel-frame count and latent-frame count are not identical.
- Classic guide nodes and IC-LoRA guide nodes use different frame-index conventions for multi-frame guidance. Check `core-generation` for ordinary guide/keyframe rules and `specialized-workflows` for IC-LoRA guide rules.
- Ensure latent spatial sizes are divisible by any IC-LoRA `latent_downscale_factor`.

## HDR EXR output fails

Symptoms:

- HDR preview works but EXR frames are not written.
- Error says `OPENCV_IO_ENABLE_OPENEXR` is not enabled.
- `cv2` imports but cannot write `.exr`.

Recovery:

- Use `../sub-skills/specialized-workflows/scripts/hdr_exr_preflight.py` before enabling `save_exr`.
- Set `OPENCV_IO_ENABLE_OPENEXR=1` before starting ComfyUI and before `cv2` imports.
- Install an OpenCV build with EXR writer support if EXR constants/writer checks fail.

## Q8 nodes fail

Symptoms:

- `ImportError` mentions `q8_kernels`.
- `LTXVQ8LoraModelLoader` says the Q8 patcher is not applied.

Recovery:

- Q8 is optional. Skip Q8 nodes unless the user specifically needs that path.
- Install compatible `q8_kernels` only after checking CUDA/torch compatibility.
- In the graph, apply `LTXQ8Patch` before `LTXVQ8LoraModelLoader`.
- Use `../sub-skills/advanced-control/scripts/q8_preflight.py` to check torch CUDA and `q8_kernels` importability without loading models.

## Conditioning or sparse-track artifacts are malformed

Symptoms:

- Saved conditioning cannot load, or `conditioning_data_*` keys are missing.
- Sparse motion-track workflows reject or ignore track JSON.

Recovery:

- Use `../sub-skills/prompt-conditioning/scripts/validate_conditioning_safetensors.py` for conditioning safetensors files.
- Use `../sub-skills/specialized-workflows/scripts/validate_sparse_tracks.py` for track JSON, expected frame counts, and bounds checks.
- Do not run full ComfyUI generation until these static artifacts validate.
