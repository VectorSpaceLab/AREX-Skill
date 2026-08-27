# Troubleshooting

Use this reference to diagnose model/config/checkpoint utility issues without writing output checkpoints or running image generation.

## Checkpoint and Path Failures

| Symptom | Likely cause | Action |
| --- | --- | --- |
| `Input model does not exist.` | Add-control input checkpoint path is wrong or missing. | Ask the user for the local SD checkpoint path. Do not download automatically. |
| `Output filename already exists.` | Original add-control script refuses to overwrite. | Pick a new output name or implement an explicit `--overwrite` guard in a custom writer. Dry-run tools should not write at all. |
| `Output path is not valid.` / output folder missing | The destination directory does not exist. | Create or select an existing output directory before writing. |
| Transfer script fails before loading | The original transfer script used hard-coded paths that are absent. | Replace hard-coded constants with explicit parameters and run a dry-run key check first. |
| Hugging Face/model downloads unavailable | External checkpoint files were assumed but not present. | Distinguish required external checkpoint prerequisites from bundled skill files; the skill contains guidance/scripts, not model weights. |

## Config and Checkpoint Mismatch

| Symptom | Likely cause | Action |
| --- | --- | --- |
| Cross-attention/context shape mismatch | SD2.1 checkpoint paired with `cldm_v15`, or SD1.5 checkpoint paired with `cldm_v21`. | SD1.x uses `context_dim: 768` and `FrozenCLIPEmbedder`; SD2.1 uses `context_dim: 1024` and `FrozenOpenCLIPEmbedder`. Switch config/tool family. |
| Many missing or unexpected keys in `load_state_dict` | Wrong checkpoint type, nested state dict not unwrapped, or key prefixes differ. | Load with `cldm.model.load_state_dict(..., location="cpu")`, inspect keys, then dry-run mapping with the bundled inspector. |
| `control_...` keys do not map to source checkpoint | Base SD checkpoint lacks matching `model.diffusion_...` keys or prefixes differ. | Check whether the source is a converted/diffusers/non-original checkpoint; map prefixes explicitly before writing. |
| `first_stage_model` or `cond_stage_model` missing during transfer | Target community checkpoint does not contain expected VAE/text encoder keys. | Do not save transfer output until those missing keys are explained or supplied from a compatible source. |
| `strict=True` load fails after add-control mapping | Tensor shapes differ even when key names exist. | Confirm SD family and config match, then compare tensor shapes for failing keys. The dry-run inspector can report names but does not validate every tensor shape unless real tensors are loaded. |

## `.ckpt` vs `.safetensors`

| Symptom | Likely cause | Action |
| --- | --- | --- |
| `ModuleNotFoundError: safetensors` | Loading a `.safetensors` file without the package installed. | Install `safetensors` in the working environment or use a PyTorch checkpoint format that does not require it. |
| CUDA device error while loading `.safetensors` | `location="cuda"` requested when CUDA is unavailable or not initialized. | Use `location="cpu"` for inspection. Only load to CUDA when generation/training actually needs it and CUDA is available. |
| PyTorch pickle/security concern | `.ckpt`/`.pth` uses `torch.load`, which can execute pickle payloads. | Prefer trusted checkpoint sources. For untrusted sources, prefer `.safetensors` and key-only inspection where possible. |

## CUDA, xformers, and Memory

| Symptom | Likely cause | Action |
| --- | --- | --- |
| `No module 'xformers'. Proceeding without it.` | Optional xformers package is not installed. | Treat as non-fatal unless the user selected xformers-only attention. Use vanilla or sliced attention when supported. |
| CUDA unavailable despite `location="cuda"` | Environment has no usable CUDA device or PyTorch CUDA build. | Load checkpoints on CPU for inspection. Do not call `low_vram_shift` or CUDA-only generation paths. |
| Out of memory during app or training | Full attention, large batch size, or all modules resident on GPU. | For app usage route to Gradio app guidance. For training route to training guidance. Relevant knobs include low-VRAM shifting, sliced attention, xformers, smaller batch size, and gradient accumulation. |
| Sliced attention is unexpectedly slow | It trades speed for memory by chunking attention. | Explain the speed/memory trade-off; do not treat slowdown as correctness failure. |

## Dry-Run Inspector Issues

| Symptom | Likely cause | Action |
| --- | --- | --- |
| Inspector uses `parser: line-scan` | PyYAML is not installed, so the script fell back to lightweight YAML line scanning. | This is enough for common target/context/head summaries; install PyYAML if full structured parsing is needed. |
| Inspector cannot parse config | Wrong `--repo-root`, missing `models/cldm_v15.yaml`/`cldm_v21.yaml`, or nonstandard config path. | Pass `--config-path` explicitly or point `--repo-root` at a checkout containing the config files. |
| Inspector reports `checkpoint_error` | Unsupported checkpoint format, missing dependency, or failed safe load. | Re-run with `--checkpoint-key-list` when only key names are needed, or fix the checkpoint dependency. |
| Inspector reports many newly initialized keys | Expected for ControlNet-only zero-conv/hint layers, but suspicious for ordinary SD keys. | Compare the report: `control_` keys map to `model.diffusion_` keys; non-control keys should often exist directly in the base checkpoint. |

## External Prerequisites vs Bundled Skill Files

This sub-skill bundles documentation and a non-destructive key-mapping inspector. It does not bundle Stable Diffusion checkpoints, ControlNet checkpoints, detector weights, or model-download code. When a user asks to initialize or transfer weights, first gather the required local checkpoint paths and confirm the config family before proposing any save operation.
