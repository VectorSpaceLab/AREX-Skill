# Model Loading Troubleshooting

Use this checklist to separate path/config issues from backend, model-family, optional dependency, and workflow graph issues.

## Missing Checkpoint, LoRA, VAE, or ControlNet

1. Confirm the loader node's category:
   - checkpoint loader: `checkpoints`
   - LoRA loader: `loras`
   - VAE loader: `vae`
   - ControlNet/T2I adapter loader: `controlnet`
   - standalone diffusion/UNet loader: `diffusion_models`
   - standalone CLIP/T5/text encoder loader: `text_encoders`
2. Confirm file extension support. Most model-weight categories accept checkpoint-like extensions such as `.safetensors`, `.ckpt`, `.pt`, `.pth`, `.bin`, `.pkl`, and `.sft`; `configs` expects `.yaml`; `diffusers` expects folders.
3. If using `extra_model_paths.yaml`, run the bundled validator:

```bash
python ../scripts/validate_extra_model_paths.py extra_model_paths.yaml --strict
```

4. Restart or refresh ComfyUI after changing paths.
5. If the graph references an old filename, route prompt JSON edits to `../../workflow-execution/SKILL.md`.

## YAML Syntax and Base Path Errors

Symptoms:

- ComfyUI does not add any paths from an extra config.
- Only some categories appear.
- Relative paths resolve somewhere unexpected.

Checks:

- Use spaces, not tabs.
- Keep category values as strings. For multiple folders, use a block scalar with `|`.
- Put `base_path` under the top-level profile, not at the document root.
- Remember that relative `base_path` is resolved relative to the YAML file location.
- Without `base_path`, each relative category path is resolved relative to the YAML file location.
- Environment variables and `~` are expanded by ComfyUI; the bundled validator mirrors this behavior for reporting.

Bad shape:

```yaml
base_path: /models
checkpoints: checkpoints
```

Good shape:

```yaml
shared:
  base_path: /models
  checkpoints: checkpoints
```

## Unknown or Duplicate Category

Unknown category:

- Built-in categories are listed in `model-paths.md`.
- Custom nodes can register additional categories at runtime. If the category belongs to a documented custom node, it can be intentional.
- New configs should prefer `text_encoders` over legacy `clip`, and `diffusion_models` over legacy `unet`.

Duplicate path:

- Adding the same path twice is usually harmless because ComfyUI avoids duplicate category entries.
- If `is_default: true` is used, a duplicated path can move to the front of search order.
- Remove duplicates to make diagnostics easier unless ordering is intentional.

## Backend and Torch Errors

Common classes of errors:

- `Torch not compiled with CUDA enabled`: the installed torch build does not support CUDA. Install a torch build for the intended backend or run with `--cpu` for diagnosis.
- ROCm/XPU/MPS/DirectML errors: the torch backend or driver stack is missing, unsupported, or incompatible.
- Optional acceleration import failures: packages such as attention, offload, quantization, or custom-node dependencies may be missing even when model paths are correct.
- CPU fallback is slow and may still fail if a package assumes GPU-only behavior; describe this generically and recommend matching the environment to the requested backend.

Do not solve backend errors by moving model files unless the error also says a model path is missing.

## VRAM Pressure and Out-of-Memory

If the user has limited VRAM and no confirmed backend:

1. Keep default dynamic VRAM first.
2. Add `--vram-headroom` or `--reserve-vram` when other applications need memory.
3. Try `--lowvram` for constrained GPUs; use `--novram` only when low VRAM mode is still insufficient.
4. Try `--cpu-vae` if VAE decode causes OOM.
5. Try `--cache-none` when cached intermediate results are the pressure source.
6. Avoid `--highvram` and `--gpu-only` on constrained machines.
7. For black images or VAE instability, try `--fp32-vae` or attention upcasting before changing model folders.

## Quantized Model Failures

Quantized checkpoint issues can look like dtype, layout, or unsupported operation errors.

Check:

- The checkpoint has compatible quantization metadata and layout names.
- The backend supports the requested low-precision dtype.
- FP8 launch flags are not being forced on unsupported hardware.
- A non-quantized or fp16/fp32 variant runs, which helps distinguish path issues from quantization issues.
- Mixed precision models may require specific layer metadata; missing scale tensors or malformed metadata means the file itself is incompatible.

## Model Family or Component Mismatch

Examples:

- A standalone diffusion model placed in `checkpoints` but used by a split-model loader.
- A text encoder placed in `diffusion_models`.
- A Flux/SD3/Qwen/Wan workflow missing one of its separate text encoders or VAE.
- A ControlNet file selected in a normal checkpoint loader.
- A model family newer than the installed ComfyUI version.

Fix by matching the loader node to the category and model component. If the issue is the graph's node inputs or filename references, cross-link to `../../workflow-execution/SKILL.md`.

## Optional Dependency and Custom Node Failures

Model paths can be correct while execution still fails because a custom node or optional backend dependency is missing.

Response pattern:

- Separate the first missing-file error from the first import/backend error.
- If the traceback mentions a custom node module, route implementation/packaging details to `../../custom-nodes/SKILL.md`.
- If the traceback mentions server launch or CLI binding, route launch details to `../../server-api/SKILL.md`.
- If the traceback occurs only after graph submission, route prompt graph validation to `../../workflow-execution/SKILL.md`.
- Avoid asking users to install unrelated model files when the error is an import or backend capability error.

## Fast Diagnostic Questions

Ask only what is needed:

- Which loader node is missing the file?
- What category did you put the file under?
- Are you using `extra_model_paths.yaml` or `--extra-model-paths-config`?
- Does the validator report missing paths or unknown categories?
- Which backend do you intend to use: CPU, CUDA/NVIDIA, ROCm/AMD, XPU/Intel, MPS/Apple, DirectML, or something else?
- Is the model all-in-one, split diffusion/text/VAE, Diffusers-folder, or quantized?
