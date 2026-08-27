# Model and Backend Requirements

ComfyUI-LTXVideo is a **ComfyUI custom-node package**. Treat it as node-graph tooling for LTX-2 video/audio workflows, not as a standalone Python package with a normal import name.

## Runtime baseline

| Requirement | Practical guidance |
| --- | --- |
| ComfyUI | Use ComfyUI Manager install flow or place the custom-node checkout under ComfyUI's `custom_nodes` directory. Restart ComfyUI after install or dependency changes. |
| Python | Use the Python version supported by the user's ComfyUI build. Current ComfyUI metadata requires Python `>=3.10`; Python 3.11 was used for inspection. |
| PyTorch/CUDA | Native generation needs CUDA-capable PyTorch, not a CPU-only torch build. Match torch CUDA wheels to the NVIDIA driver and ComfyUI release. |
| GPU/VRAM | README prerequisites call for a CUDA-compatible GPU with 32GB+ VRAM for LTX-2 workflows. Larger/two-stage/HDR/DubIt/long-video graphs may need more headroom. |
| Disk/cache | README prerequisites call for 100GB+ free disk for models and cache. Do not trigger downloads unless the user approves. |
| Package dependencies | Install this repo's `requirements.txt` inside the ComfyUI environment: `diffusers`, `einops`, `huggingface_hub>=0.25.2`, `kornia`, `ninja`, `transformers[timm]>=4.50.0`. |

## ComfyUI model-folder layout

Use public ComfyUI model folders; do not hard-code one user's local paths.

| Folder under ComfyUI models | Needed for | Files or families mentioned by repo evidence |
| --- | --- | --- |
| `models/checkpoints` | LTX-2 diffusion checkpoints, some audio VAE loader paths | LTX-2.3 22B dev or distilled checkpoints; older LTX-2.0 checkpoints for older workflow families. |
| `models/latent_upscale_models` | Two-stage spatial/temporal upsampling workflows | LTX-2.3 spatial upscaler x2/x1.5 and temporal upscaler x2 models. |
| `models/loras` | Distilled LoRA and IC-LoRA families | Distilled LoRA, union control, motion track, HDR, DubIt, pixel spatial upscaler, ingredients, in/outpaint, camera/control LoRAs. |
| `models/text_encoders` | Local Gemma conditioning | Gemma 3 folder containing `config.json`, tokenizer, processor, and model files. The README names a Gemma 3 12B QAT folder. |
| `models/embeddings` | Saved conditioning artifacts | `LTXVSaveConditioning` writes safetensors files here; `LTXVLoadConditioning` reads them back. |
| ComfyUI output directory | HDR EXR sequences and generated media | `LTXVHDRDecodePostprocess` can write EXR sequences under an output subdirectory when optional OpenEXR support is enabled. |

## Required versus optional dependencies

| Feature | Dependency/backing asset | Required? | Notes |
| --- | --- | --- | --- |
| Ordinary T2V/I2V/V2V generation | ComfyUI, CUDA torch, LTX checkpoint, text conditioning, VAE/decode path | Required for generation | Static graph planning can be done without models, but native execution cannot. |
| Two-stage generation | Latent spatial/temporal upscaler models and often distilled LoRA | Required for two-stage recipes | Route graph details to `core-generation`. |
| Gemma local encoder | Complete Gemma model folder plus LTX checkpoint metadata/projections | Required for local Gemma path | Missing `config.json` is a folder-placement problem; read `prompt-conditioning`. |
| Gemma API encoder | API credentials and model/checkpoint metadata | Optional alternative | Ask before sending prompts to external APIs. |
| Prompt enhancer | Hugging Face LLM and image-captioner models | Optional | Loader can download/cache models; ask before triggering downloads. |
| HDR EXR export | `opencv-python`/cv2 EXR support plus `OPENCV_IO_ENABLE_OPENEXR=1` before ComfyUI starts | Optional | HDR tonemapped/linear tensors can exist without writing EXR files. |
| Q8 model path | `q8_kernels` from Lightricks' Q8 kernels project | Optional advanced path | `LTXQ8Patch` and `LTXVQ8LoraModelLoader` fail until q8 kernels are importable and patch order is correct. |
| Sparse track editor | ComfyUI frontend web assets from this custom-node package | Required for interactive editor | Python fallback still validates/renders tracks; frontend widget gives interactive drawing. |

## Compatibility notes from inspection

- The repo loaded successfully as a ComfyUI custom-node package with 78 node mappings and `WEB_DIRECTORY = "./web"`.
- A CUDA-enabled torch build is necessary for backend-native generation. Static package import and JSON workflow inspection do not prove generation quality.
- If ComfyUI prints a warning recommending cu130+ for optimized CUDA operations on modern NVIDIA GPUs, treat it as a compatibility/performance signal. Use a torch wheel recommended by the current ComfyUI release if native generation or optimized operations fail.
- If import fails with `cannot import name 'pad' from kornia.geometry.transform.pyramid`, use a Kornia build compatible with this repo's `pyramid_blending.py` implementation; `kornia==0.7.1` was verified during construction.
- If ComfyUI import fails inside `comfy_kitchen` custom-op registration with a torch schema error, upgrade to a newer CUDA-enabled torch build compatible with the current ComfyUI requirement set.

## Safe checks before native runs

1. Confirm ComfyUI sees the custom node package after restart.
2. Run `../scripts/inspect_custom_node_package.py --repo-root <custom-node-folder> --comfyui-root <ComfyUI-root> --json` from a Python environment with ComfyUI dependencies installed.
3. Run `../scripts/summarize_workflow_json.py <workflow.json>` on user-supplied workflow exports to identify node names/families before editing them.
4. For conditioning artifacts, sparse-track JSON, HDR EXR support, and Q8 support, use the sub-skill-specific bundled scripts before running generation.
5. Only run native ComfyUI generation after confirming model files, CUDA, optional dependencies, user authorization for downloads/API calls, and output location expectations.
