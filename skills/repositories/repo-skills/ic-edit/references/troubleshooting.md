# Troubleshooting

## Cross-cutting failures

| Symptom | Likely cause | What to do |
| --- | --- | --- |
| `torch.cuda.is_available()` is false | The environment has a CPU-only torch wheel or no visible GPU | Install a CUDA build of torch and rerun `scripts/check_icedit_env.py`. The primary ICEdit workflows are GPU-first and do not have a truthful CPU substitute. |
| `FluxFillPipeline` or `GGUFQuantizationConfig` import failures | `diffusers` is too old, broken, or not installed | Reinstall the base editing stack from `references/installation.md` and rerun the environment checker. |
| Model download or authentication failures | Hugging Face access is blocked or the weights are not cached locally | Log in to Hugging Face or download the base model and LoRA weights locally, then pass filesystem paths to the bundled helpers. |
| `ModuleNotFoundError` for the vendored `icedit/` path | The MoE or training route needs a checkout root, but none was supplied | Pass `--repo-root <ICEdit checkout>` to the bundled helper or switch to the normal LoRA path. |
| The input image is resized | The source width is not 512 pixels | This is expected. The helpers normalize width to 512 and round the new height down to a multiple of 8. |
| CUDA out of memory | The GPU is too small for the full pipeline | Retry with CPU offload, reduce other GPU usage, or use smaller source imagery. |
| `spaces` import complaints | The source demo script assumes the Hugging Face Spaces package | Use the bundled Gradio helper, which falls back to a no-op decorator outside Spaces. |
| The user wants to run training but only has the demo stack | Training support libraries are missing | Install the training libraries in `references/installation.md` before using the training route. |

## Recovery order

1. Run `scripts/check_icedit_env.py`.
2. Verify the model ids or local weight paths.
3. Check whether the request is really normal inference, Gradio, or training.
4. Use the sub-skill-specific troubleshooting page for the selected route if the failure remains.

## Route-specific pages

- `sub-skills/inference/references/troubleshooting.md`
- `sub-skills/gradio/references/troubleshooting.md`
- `sub-skills/training/references/troubleshooting.md`
