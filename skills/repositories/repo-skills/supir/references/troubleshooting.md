# SUPIR Troubleshooting

Use this root troubleshooting file for install, import, checkpoint, and backend
failures shared across API, batch, and demo workflows. For workflow-specific
steps, continue to the nearest sub-skill reference.

## Common symptoms

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ValueError: Currently support CUDA only.` | The selected source workflow found no CUDA device. | Use a CUDA host, fix driver/PyTorch wheel mismatch, or restrict the task to source inspection and dry-run planning. CPU import is not end-to-end restoration proof. |
| `torch.cuda.is_available()` is false despite an NVIDIA GPU | CPU-only PyTorch wheel, incompatible driver/runtime, hidden GPUs, or container/device mapping issue. | Install a CUDA PyTorch wheel compatible with the host driver and check `CUDA_VISIBLE_DEVICES`, `nvidia-smi`, and a one-tensor CUDA allocation. |
| `ModuleNotFoundError: cv2` | OpenCV dependency missing. | Install `opencv-python` compatible with the Python version and rerun the import probe. |
| `ModuleNotFoundError: pkg_resources` | Some newer minimal setuptools builds omit legacy `pkg_resources`, but older Transformers/LLaVA code imports it. | Install or downgrade to a setuptools build that provides `pkg_resources` before importing LLaVA modules. |
| `ModuleNotFoundError: k_diffusion`, `omegaconf`, `open_clip`, `facexlib`, or `pytorch_lightning` | Core SUPIR dependency missing. | Install the package family listed in [checkpoints-and-environment.md](checkpoints-and-environment.md); use the API probe before model loading. |
| `ValueError: 'llava' is already used by a Transformers config` | A newer Transformers release already reserves the `llava` model type, conflicting with the repo's local `AutoConfig.register('llava', ...)`. | Use a repo-compatible Transformers 4.x stack (the inspected environment used 4.28.1) for LLaVA/SUPIR captioning. |
| `no module 'xformers'. Processing without...` during import | Optional xformers acceleration is missing. | This warning is not an import failure. Install xformers only when the selected workflow truly needs its memory/speed benefit and a compatible wheel exists. |
| model loading hangs or downloads unexpectedly | A CLIP or LLaVA path is `None` and the library is trying to download from Hugging Face. | Decide whether network download is allowed. Otherwise set explicit local paths and validate them with `scripts/check_supir_assets.py`. |
| `FileNotFoundError` for `SDXL_CKPT`, `SUPIR_CKPT_Q`, or `SUPIR_CKPT_F` | YAML checkpoint fields still point to placeholders or unavailable private paths. | Update the YAML or pass a copied config with user-local paths; validate before `create_SUPIR_model`. |
| NaNs or failed autoencoder dtype path | AE dtype set to `fp16` or unsupported mixed precision. | Use `bf16` or `fp32` for `ae_dtype`; source constructor explicitly rejects `fp16` for AE. |
| LLaVA out-of-memory | LLaVA v1.5 13B and SUPIR share one GPU or model is loaded at full precision. | Prefer two GPUs, try `--load_8bit_llava`, use `--no_llava` with manual prompts, or switch to local-prompt flows. |
| Gradio launch dependency failure | Optional UI dependencies are missing or a dependency resolver mixed incompatible web stack versions. | Treat UI dependencies as optional. Use the interactive demo preflight script to decide whether to install the UI stack in a separate environment. |
| Face detector import or model error | `facexlib` missing or its detector/parsing weights are unavailable. | Install `facexlib`, confirm detector model downloads/cache permissions, or use non-face restoration workflows. |

## Safe recovery order

1. Run a syntax/import probe, not a model run.
2. Confirm CUDA with a tiny tensor allocation.
3. Validate config/checkpoint paths.
4. Only then load SDXL/SUPIR/LLaVA checkpoints.
5. Use `--no_llava` or manual prompts to isolate caption-model failures.
6. Use tiled VAE or lower memory modes before assuming checkpoint corruption.

## Dependency-resolution notes

- The public `requirements.txt` includes both core and optional UI/service
  packages. Some exact pins conflict in modern resolvers. Prefer installing the
  smallest stack needed for the selected workflow rather than every listed
  package.
- Batch/API inspection does not require Gradio. Gradio launch does not need to
  prove SUPIR model quality.
- Keep LLaVA/Transformers compatibility stable. If upgrading Transformers,
  verify `import llava.llava_agent` before starting long runs.

## Checkpoint hygiene

- Never publish private absolute checkpoint paths.
- Keep one editable user-local config copy per checkpoint family so batch and
  demo runs use the same SDXL/SUPIR paths.
- Record the checkpoint family (`Q`, `F`, base SDXL, Juggernaut Lightning) when
  comparing results.
- Set CLIP paths to `None` only when online model download is allowed and the
  cache location is acceptable to the user.
