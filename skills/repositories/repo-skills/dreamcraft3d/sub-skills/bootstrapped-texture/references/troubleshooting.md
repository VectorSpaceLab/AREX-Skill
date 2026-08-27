# Bootstrapped Texture Troubleshooting

## Janus or inconsistent multiview texture

**Symptoms**
- Multiple fronts, mirrored identities, inconsistent backs, or unstable object details after early stages.

**Likely causes**
- The 2D diffusion prior is not sufficiently view-consistent for the specific object.
- Input sidecars or prompt are ambiguous.
- Multiview images generated for DreamBooth are low quality or inconsistent.

**Recovery**
1. Confirm the input sidecars and prompt first.
2. Inspect stage outputs to decide if optional texture boosting is justified.
3. Generate and inspect multiview images before training LoRA.
4. Use a specific instance prompt with a rare token only when the multiview set is coherent.

## `local_files_only=True` model-cache failure

**Symptoms**
- Zero123++ or upscaler load fails without attempting a download.
- Errors mention missing snapshots, model index, scheduler, or cached files.

**Likely causes**
- The source helper expects `sudo-ai/zero123plus-v1.1` and optional upscaler to already be cached.
- The job runs in an isolated container or scheduler environment with a different cache path.

**Recovery**
- Check cache locations before running generation.
- Ask for approved model acquisition or a populated cache path.
- Avoid editing generated skill files or source commands to force network downloads without user approval.

## Hard-coded `cuda:1`

**Symptoms**
- `invalid device ordinal`, no device found, or the process uses an unintended GPU.

**Likely causes**
- `img_to_mv.py` moves models to `cuda:1` directly.
- The scheduler exposes only one visible device, often remapped to `cuda:0`.

**Recovery**
- Adapt the helper or wrapper to use the desired visible device.
- If using `CUDA_VISIBLE_DEVICES`, remember that visible device numbering starts from zero inside the process.
- Do not assume `--gpu 0` affects this helper; it is not launched through `launch.py`.

## DreamBooth/LoRA OOM or dependency failure

**Symptoms**
- CUDA OOM during `accelerate launch`.
- Import failures for `accelerate`, `diffusers`, `xformers`, `bitsandbytes`, `transformers`, or tokenizer components.
- Mixed-precision or TF32 warnings.

**Likely causes**
- The training environment lacks the optional DreamBooth/LoRA dependencies.
- The selected base model is too large for the current GPU or precision.
- xformers/bitsandbytes wheel is incompatible with the torch/CUDA stack.

**Recovery**
- Verify the dependency stack separately from the core DreamCraft3D stages.
- Reduce batch size or disable optional super-resolution before changing the core stage configs.
- Keep LoRA output directories separated by object and base model.

## LoRA weights do not affect generation

**Symptoms**
- Adding `system.guidance.lora_weights_path` has no visible effect or causes a config-key error.

**Likely causes**
- The active guidance implementation/config does not consume that key.
- The LoRA was trained against a different base model.
- The output directory points to an incomplete checkpoint.

**Recovery**
- Check the exact stage config and guidance type.
- Use the same base model family for LoRA training and guidance.
- Verify the LoRA output directory exists and contains expected model artifacts before launching expensive stages.
