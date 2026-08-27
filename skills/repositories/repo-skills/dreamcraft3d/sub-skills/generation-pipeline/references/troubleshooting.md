# Generation Pipeline Troubleshooting

## OmegaConf missing value (`???`)

**Symptoms**
- Config parsing or launch fails before training with a missing mandatory value.

**Likely causes**
- Missing `system.prompt_processor.prompt`.
- Missing `data.image_path`.
- Missing `system.weights` for coarse NeuS or missing `system.geometry_convert_from` for geometry/texture.

**Recovery**
- Build the command with the bundled command builder and check the required overrides for the selected stage.
- Quote prompt and path values so spaces do not break OmegaConf parsing.

## Image sidecar assertion

**Symptoms**
- Stage startup reports it cannot find the image, depth, or normal file.

**Likely causes**
- `data.image_path` does not point to a `_rgba.png` file.
- Sidecar names do not share the same stem.
- Required depth/normal files were not generated.

**Recovery**
- Route to `image-preparation` and validate the image family before relaunching.

## Checkpoint chaining error

**Symptoms**
- `torch.load` or conversion logic fails when a stage starts.
- Geometry/texture stage cannot initialize from prior work.

**Likely causes**
- The previous stage never produced `ckpts/last.ckpt`.
- The prompt tag or output root was guessed incorrectly.
- `system.weights` was used where `system.geometry_convert_from` is required, or vice versa.

**Recovery**
1. Inspect the previous stage output directory for `ckpts/last.ckpt` and `configs/parsed.yaml`.
2. Use absolute or correctly repo-relative checkpoint paths in overrides.
3. Keep the stage-specific override names distinct.

## CUDA, PyTorch, or compiled extension failure

**Symptoms**
- `torch.cuda.is_available()` false in a CUDA environment.
- Import errors for `nerfacc`, `tinycudann`, `nvdiffrast`, `xformers`, or `bitsandbytes`.
- Rasterizer context errors in headless or Docker environments.

**Likely causes**
- CPU-only torch wheel installed.
- Driver/toolkit/wheel mismatch.
- Compiled extensions were built for a different CUDA or compute capability.
- OpenGL rasterizer context is unavailable.

**Recovery**
- Use a CUDA torch wheel compatible with the host driver.
- Rebuild or reinstall GPU extensions in the same environment as torch.
- For nvdiffrast/OpenGL issues, prefer config overrides such as `system.renderer.context_type=cuda` or `system.exporter.context_type=cuda` when the renderer/exporter supports it.
- Use the installation/backend sub-skill for broader environment triage.

## Model artifact missing or offline cache failure

**Symptoms**
- DeepFloyd, Stable Diffusion, Stable Zero123, or Omnidata loads fail.
- `local_files_only=True` paths fail in optional scripts.

**Likely causes**
- Model checkpoints are absent from expected local paths or HF cache.
- The environment has no network permission and the model was not pre-cached.

**Recovery**
- Route to `bootstrapped-texture` for model-artifact planning.
- Do not start long training just to discover missing artifacts; check them first.

## Out-of-memory or extremely slow training

**Symptoms**
- CUDA OOM during guidance, DMTet, nvdiffrast, or texture refinement.
- Training makes no visible progress at full resolution.

**Likely causes**
- Defaults target large-memory GPUs.
- Resolution settings are too high for the available VRAM.
- Multiple GPUs/jobs share the same device.

**Recovery**
- Reduce `data.height`, `data.width`, and random-camera resolution overrides for diagnosis.
- Check `CUDA_VISIBLE_DEVICES` and `--gpu` behavior.
- Disable or postpone optional DreamBooth/texture boosting until the core stages run.
