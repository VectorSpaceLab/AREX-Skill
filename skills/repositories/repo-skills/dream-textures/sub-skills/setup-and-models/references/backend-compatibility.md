# Backend Compatibility, Dependency Variants, and Model Types

Dream Textures has separate dependency requirement files for local backend variants. Choose one variant for the user's platform/backend rather than mixing all requirements together.

## Dependency variant matrix

| Variant file | Intended platform/backend | Key backend packages | Use when | Avoid when |
| --- | --- | --- | --- | --- |
| `requirements/win-linux-cuda.txt` | Linux or Windows with NVIDIA CUDA | `torch==2.3.1` from PyTorch `cu118` index; `diffusers==0.27.2`; `transformers`; `accelerate`; `huggingface_hub`; `controlnet-aux==0.0.7`; checkpoint conversion dependencies | User has a supported NVIDIA GPU and wants local Diffusers inference | User is on AMD ROCm, Apple Silicon, Windows DirectML-only hardware, or cloud-only DreamStudio |
| `requirements/linux-rocm.txt` | Linux with AMD ROCm | `torch==2.3.1` from PyTorch ROCm 6.1 index; same Diffusers/controlnet/checkpoint stack | User has Linux + AMD GPU + compatible ROCm runtime | User is on Windows AMD without ROCm, NVIDIA CUDA, or Apple Silicon |
| `requirements/mac-mps-cpu.txt` | macOS Apple Silicon MPS and CPU fallback | `torch==2.3.1`; `diffusers==0.27.2`; `huggingface_hub>=0.19.3`; same control/checkpoint stack | User is on macOS/Apple Silicon or needs CPU-only local testing | User expects CUDA, ROCm, or DirectML acceleration |
| `requirements/win-dml.txt` | Windows DirectML | `torch-directml`; `torch==2.3.1`; same Diffusers/controlnet/checkpoint stack | User has Windows with a DirectX 12 GPU and no CUDA path | User has NVIDIA CUDA and can use the CUDA build, or is on Linux/macOS |

Shared packages across variants include Diffusers, Transformers, Accelerate, Hugging Face Hub, `controlnet-aux`, checkpoint conversion helpers (`pytorch-lightning`, `tensorboard`, `omegaconf`), `scipy` for schedulers, `opencolorio` for color management, and `matplotlib` for OpenPose/control tooling.

The add-on source also advertises a DreamStudio dependency option in Blender registration. In the inspected source snapshot, a matching `requirements/dreamstudio.txt` file was not present. For cloud-only release builds, trust the release contents and release notes over the source dependency matrix.

## Backend selection guidance

- Local generation requires Blender, the add-on dependencies in `.python_dependencies`, a compatible torch/backend install, sufficient RAM/VRAM, and model weights.
- The public compatibility guidance says Dream Textures has been tested with CUDA and Apple Silicon GPUs and recommends more than 4 GB VRAM.
- CUDA is the best-supported local path when an NVIDIA GPU is available.
- Apple Silicon uses the macOS MPS/CPU requirement variant; CPU fallback can be slow and should not be treated as proof that accelerator performance is acceptable.
- ROCm and DirectML are separate backend variants and should be diagnosed as platform-specific alternatives, not as interchangeable CUDA installs.
- DreamStudio cloud processing is the fallback for unsupported local hardware or users who do not want local inference; it requires an API key rather than local model weights.

## Task and model type matrix

Dream Textures infers model type mainly from Diffusers metadata such as U-Net `in_channels`, and it uses model type checks to prevent task/model mismatches.

| Intended task/workflow | Required model type | Recommended model | Why |
| --- | --- | --- | --- |
| Prompt-to-image | `PROMPT_TO_IMAGE` | `stabilityai/stable-diffusion-2-1` or `stabilityai/stable-diffusion-2-1-base` | Standard Stable Diffusion pipeline for text prompts |
| Image-to-image without depth | `PROMPT_TO_IMAGE` | `stabilityai/stable-diffusion-2-1` or compatible prompt model | Image-to-image reuses prompt/image pipeline behavior |
| Inpainting | `INPAINTING` | `stabilityai/stable-diffusion-2-inpainting` | Inpainting needs the expanded inpainting U-Net input shape |
| Outpainting | `INPAINTING` | `stabilityai/stable-diffusion-2-inpainting` | Outpainting is implemented as an inpainting task around an expanded canvas |
| Depth-to-image / texture projection with depth | `DEPTH` | `stabilityai/stable-diffusion-2-depth` | Depth guidance needs a depth-capable pipeline/model |
| AI upscaling | `UPSCALING` | `stabilityai/stable-diffusion-x4-upscaler` | Upscaling uses an upscaler-specific model |
| ControlNet conditioning | `CONTROL_NET` for the ControlNet side model plus a compatible base generation model | Use a ControlNet model matching the base model family and conditioning type | ControlNet is loaded separately from the main generation pipeline |
| SDXL base generation | Prompt model loaded with `XL (base)` config when importing a checkpoint | SDXL base checkpoint or Diffusers model | SDXL base uses a different pipeline family than SD v1/v2 |
| SDXL refiner | Refiner model loaded with `XL (refiner)` config | SDXL refiner checkpoint/model | Refiner is used as an optional second model for SDXL image refinement |

If the add-on says the selected model is not appropriate for the task, do not tune prompt parameters first. Select or import a model whose type matches the workflow.

## Checkpoint config matrix

When importing or linking original checkpoints, choose a config that matches the model family. The choice selects the original config/pipeline used during conversion or loading.

| Config label in Dream Textures | Use for | Resulting model type guidance |
| --- | --- | --- |
| `auto-detect` | First attempt only when the exact checkpoint family is unknown | Treated as an unspecified checkpoint; may defer mismatch until load/generation time |
| `v1` | Original CompVis Stable Diffusion v1.x checkpoints | Prompt/image-to-image model |
| `v2 (512, epsilon)` | Stable Diffusion v2 512x512 checkpoints using epsilon prediction | Prompt/image-to-image model |
| `v2 (768, v_prediction)` | Stable Diffusion v2 768x768 checkpoints using v-prediction | Prompt/image-to-image model |
| `v2 (depth)` | Stable Diffusion v2 depth checkpoints | Depth model |
| `v2 (inpainting)` | Stable Diffusion v2 inpainting checkpoints | Inpainting/outpainting model |
| `XL (base)` | SDXL base checkpoints | Prompt model using SDXL base pipeline |
| `XL (refiner)` | SDXL refiner checkpoints | Refiner model; not a substitute for inpainting/depth/upscaler |
| `1.5 (ControlNet)` | ControlNet checkpoint trained for SD 1.5-compatible bases | ControlNet model |
| `2.1 (ControlNet)` | ControlNet checkpoint trained for SD 2.1-compatible bases | ControlNet model |

## Precision and cache implications

- **Prefer Half Precision Weights** asks Dream Textures to download or save fp16 weights when available. This reduces size and memory pressure but should align with the user's precision/optimization settings.
- When half precision is disabled and only fp16 weights are available, the backend may warn and fall back to fp16.
- Hugging Face pipeline models are expected to have `model_index.json`; individual model repos such as ControlNet may expose `config.json` plus a compatible weight file.
- Converted checkpoints are saved to the Hugging Face cache under a name derived from the checkpoint basename. Avoid ambiguous duplicate checkpoint basenames when linking many folders.
- If a model appears in a filesystem path, Dream Textures can open the folder/file from preferences rather than downloading it again.

## Dependency validation checklist

1. Match platform and accelerator to exactly one requirement variant.
2. Confirm dependencies were installed into `.python_dependencies`, not only into a separate virtualenv.
3. Confirm `torch`, `diffusers`, `huggingface_hub`, `transformers`, `accelerate`, and `controlnet_aux` are visible from Blender's Python environment when local generation is expected.
4. Confirm the intended model appears in the installed model list or linked checkpoint list.
5. Confirm the task/model type row matches the user's workflow.
6. Only after these checks should you diagnose generation parameters, backend internals, or scene workflow details.
