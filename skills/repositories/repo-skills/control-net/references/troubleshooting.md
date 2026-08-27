# ControlNet Troubleshooting

Use this root guide for failures that affect multiple ControlNet workflows. For workflow-specific issues, route to the nearest sub-skill troubleshooting file.

## Cross-Cutting Failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `pip install control-net` or distribution metadata lookup fails | This repository has no package metadata and is used as a source checkout. | Add the checkout to `PYTHONPATH`, run scripts from the checkout when intentionally using source scripts, or use bundled skill helpers that accept `--repo-root`. Do not claim there is a public `control-net` package unless the user provides one. |
| `ModuleNotFoundError: cldm`, `ldm`, or `annotator` | Python is not pointed at the ControlNet source checkout. | Use the root checkout diagnostic with `--repo-root`, or set the source root on `PYTHONPATH` in the user's working environment. |
| `ModuleNotFoundError` for `torch`, `cv2`, `gradio`, `omegaconf`, `pytorch_lightning`, `einops`, `transformers`, or `open_clip` | The environment is missing dependencies from the documented environment family. | Use the repository's dependency guidance as a starting point, but install only the packages needed for the selected workflow. Do not install broad GPU stacks for static parsing or dataset validation. |
| Hugging Face or model URL errors in an offline environment | Model/tokenizer/checkpoint code attempted a network download. | Stop and ask for local files or network approval. Prefer static inspection, dry-run mapping, or dataset validation when downloads are not allowed. |
| CUDA errors, `torch.cuda.is_available()` false, or OOM | App, detector, training, or conversion code expects compatible GPU/Torch/CUDA or more memory. | Use CPU-safe diagnostics first. For inference, consider low-VRAM mode only when CUDA exists. For training, reduce batch size and use gradient accumulation only after data/checkpoints validate. |
| `No module 'xformers'. Proceeding without it.` | xformers is optional and absent. | Treat as a performance/memory warning unless the user explicitly selected an xformers attention path. Use sliced attention/low-VRAM guidance when appropriate. |
| Missing `.pth`, `.pt`, `.ckpt`, or `.safetensors` files | ControlNet model, Stable Diffusion base checkpoint, or detector weights are external assets. | Identify which workflow owns the file: detector weights route to annotators, Gradio model files route to inference apps, base/checkpoint conversion route to model utilities, training init checkpoints route to training plus model utilities. |
| A source script starts a server or loads a huge model when imported | Many repo scripts execute work at module top level. | Do not import source launch scripts for inspection. Use bundled AST/static helpers or read distilled references. |
| Generated image output is nondeterministic | Seed `-1` triggers random seed selection; CUDA kernels and model differences can also vary. | Set an explicit seed and record prompt, negative prompt, sampler steps, scale, eta, control strength, checkpoint, detector parameters, and app family. |
| Checkpoint/config mismatch produces tensor shape or missing-key errors | SD1.5/SD2.1 config, text encoder, context dimension, or state-dict prefixes do not match. | Route to `sub-skills/model-and-weight-utilities/`; dry-run config/key mapping before writing or training. |
| Training starts but fails before first batch | Dataset schema, checkpoint path, CLIP/OpenCLIP model access, Lightning version, or CUDA memory is wrong. | Validate data with the bundled Fill50K validator, verify initial checkpoint creation, then address runtime dependencies/hardware. |

## Safe Diagnostic Order

1. Run the root checkout diagnostic to confirm expected files, configs, and safe imports.
2. Use sub-skill helper scripts for static signatures, data validation, and dry-run mappings.
3. Only after static checks pass, decide whether model execution, checkpoint loading, CUDA, Gradio servers, downloads, or training are safe and authorized.
4. Record skipped unsafe checks explicitly instead of treating them as passing.

## When To Ask The User

Ask for clarification or approval when a requested next step would:

- download model/tokenizer/checkpoint files;
- install or upgrade a large GPU/Torch dependency set;
- launch a server bound to a network interface;
- run long training, generation, or checkpoint conversion;
- overwrite checkpoint outputs;
- require credentials, private datasets, or hardware unavailable on the machine.
