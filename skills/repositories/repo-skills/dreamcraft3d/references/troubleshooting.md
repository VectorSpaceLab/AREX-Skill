# DreamCraft3D Cross-Cutting Troubleshooting

## How to triage

1. Identify the failing surface: image sidecars, config/override parsing, CUDA/dependencies, model artifacts, stage checkpoint chaining, export, metrics, Docker, or Gradio.
2. Use the root static checker for cheap path/config checks.
3. Route to the nearest sub-skill for detailed recovery.
4. Do not run long GPU jobs, Docker builds, downloads, or checkpoint conversions as diagnostics unless the user explicitly approves them.

## Install/import and dependency failures

**Symptoms**
- Import errors for `pytorch_lightning`, `torch`, `diffusers`, `transformers`, `nerfacc`, `tinycudann`, `nvdiffrast`, `xformers`, `bitsandbytes`, `carvekit`, or `controlnet_aux`.

**Likely causes**
- DreamCraft3D is a checkout-run project rather than a packaged distribution.
- The environment installed only a CPU or minimal subset.
- CUDA/torch/extension variants do not match.

**Recovery**
- Use the installation/backend sub-skill to inspect environment state.
- Follow the repository's CUDA/PyTorch version guidance or Docker route rather than mixing arbitrary wheels.
- Install compiled extensions in the same environment and CUDA variant as torch.

## CUDA or GPU memory failures

**Symptoms**
- `torch.cuda.is_available()` false, invalid device, CUDA OOM, slow/no progress, or rasterizer context failures.

**Likely causes**
- CPU-only torch, insufficient VRAM, wrong visible device mapping, or headless OpenGL context.

**Recovery**
- Check `CUDA_VISIBLE_DEVICES` and `--gpu` behavior.
- Reduce resolution overrides for diagnosis.
- Prefer `context_type=cuda` for renderer/exporter paths when OpenGL is unavailable.
- Do not treat static command generation as proof of CUDA readiness.

## Model artifact failures

**Symptoms**
- Stable Zero123, DeepFloyd, Stable Diffusion, Omnidata, Zero123++, or upscaler loading fails.

**Likely causes**
- Missing local checkpoint, absent Hugging Face cache, no network approval, or filename mismatch.

**Recovery**
- Route to `bootstrapped-texture` for artifact planning.
- Verify exact config paths, especially `stable_zero123.ckpt` versus `stable-zero123.ckpt`.
- Ask for approved model acquisition before running network commands.

## Image/config failures

**Symptoms**
- Missing image/depth/normal assertions, OmegaConf mandatory-value errors, or broken prompt/path parsing.

**Recovery**
- Route to `image-preparation` for sidecars.
- Route to `generation-pipeline` for `???` overrides and command construction.
- Quote prompts and paths with spaces.

## Output/export failures

**Symptoms**
- Missing `last.ckpt`, missing `parsed.yaml`, no OBJ/MTL output, texture maps absent, or metrics scripts fail.

**Recovery**
- Route to `export-and-evaluation` and summarize the trial directory.
- Export only from a compatible completed checkpoint and parsed config.
- Treat CLIP/LPIPS/CX metrics as optional model-heavy evaluation.

## Gradio/Docker operator failures

**Symptoms**
- Gradio app cannot find demo configs, watcher kills the process, Docker cannot see GPUs, or nvdiffrast fails in a container.

**Recovery**
- Route to `interfaces-and-monitoring`.
- Verify Docker Engine, NVIDIA Container Toolkit, volume mount, and GPU reservation.
- Treat the generic Gradio UI as reference/monitoring unless the needed `configs/gradio/*.yaml` files exist in the checkout.
