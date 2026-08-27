# Dream Textures Cross-Cutting Troubleshooting

## When to read this

Use this root guide when the symptom is not clearly owned by setup, image generation, scene integration, or backend implementation. For workflow-specific issues, route to the nearest sub-skill troubleshooting file after the initial triage.

## First triage

1. **Identify the surface**:
   - Add-on does not enable, dependency UI missing, model list empty, Hugging Face token, DreamStudio, checkpoint import: `sub-skills/setup-and-models/`.
   - Dream panel Generate, source image, inpaint/outpaint, ControlNet image, history JSON, AI upscaling: `sub-skills/generation-workflows/`.
   - Project Dream Texture, Cycles Dream Textures pass, compositor, render-engine nodes, annotation maps: `sub-skills/scene-integration/`.
   - Custom backend, API signatures, DiffusersBackend internals, scheduler/model-type/debugging source code: `sub-skills/backend-and-api/`.
2. **Get logs**: on Windows/Linux, open Blender's system console from the Window menu. On macOS, start Blender from Terminal to capture stdout/stderr because the system console menu is not available.
3. **Run the safe diagnostic only for visibility questions**:

```bash
python scripts/check_dream_textures_environment.py --addon-dir /path/to/dream_textures
```

This helper reports package layout and optional Python modules. It does not prove that Blender, model weights, or generation backends can run.

## Common root symptoms

### Add-on installed from source but dependencies are missing

Symptoms:

- Add-on preferences show missing dependencies.
- `.python_dependencies` is empty or absent.
- Imports such as `diffusers`, `torch`, or `transformers` fail inside Blender.

Likely causes:

- A source checkout was installed instead of an official prebuilt release.
- Dependencies were installed into the wrong Python instead of Blender's Python or the add-on `.python_dependencies` target.
- The add-on folder name is not `dream_textures`, so relative imports fail in Blender.

Recovery:

- Ordinary users should install an official Dream Textures release archive matching their platform/backend.
- Source/developer installs should follow the setup sub-skill and use one matching requirement variant, not all variants.
- Do not run repo release packaging scripts as troubleshooting.

### Model exists but the selected task still fails

Symptoms:

- Validation says the selected model is the wrong type.
- Depth, inpaint/outpaint, or upscaling actions are disabled or fail even though another Stable Diffusion model is installed.

Likely causes:

- Prompt-to-image models do not satisfy depth, inpaint/outpaint, or upscaling task validation.
- Imported checkpoints were linked with the wrong model config.
- ControlNet models are separate from the base generation model.

Recovery:

- Map task to model family in `setup-and-models/references/backend-compatibility.md`.
- For inpaint/outpaint, select an inpainting model.
- For depth-to-image/projection/render-pass depth input, select a depth model.
- For AI upscaling, use the Stable Diffusion x4 upscaler model.

### Runtime crashes only when generating

Symptoms:

- The add-on enables and models appear, but generation fails with CUDA/MPS/DirectML/CPU errors, memory errors, or missing optional dependency errors.

Likely causes:

- Wrong dependency variant for the platform/backend.
- VRAM is insufficient for current size, batch, preview, upscaling tile, render pass, or CPU-offload settings.
- Backend optional packages such as `controlnet-aux`, `torch-directml`, or model conversion packages are missing.
- Model weights are gated/private or incomplete in cache.

Recovery:

- Re-check variant and model acquisition in `setup-and-models`.
- Reduce generation size, iterations, batch size, preview accuracy, upscaling tile size, or render resolution.
- Use CPU-offload or attention/vae memory settings where available.
- For ControlNet or prompt-mask inpainting, confirm the required processor/model packages and downloaded weights.

### Guidance claims need runtime verification

This generated skill was verified with safe source/API/static checks, not by running full Blender Stable Diffusion generation. Treat CUDA, ROCm, MPS, DirectML, DreamStudio, model downloads, and full scene rendering as documented operational surfaces that still need the user's actual Blender/runtime/model environment for final proof.
