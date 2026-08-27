# Installation and asset preparation

Use this reference before running MAGI-1 source inference or ComfyUI workflows. It distills the repository README, requirements file, example launch scripts, and runtime imports into a reproducible setup checklist.

## Runtime choices

MAGI-1 documents two broad runtime choices:

1. **Docker image**: the repository README recommends pulling and running the published `sandai/magi:latest` image with GPU access, host networking, large shared memory, IPC host mode, and relaxed memory/stack limits.
2. **Source-code environment**: create a Python 3.10 environment, install PyTorch 2.4.0 with CUDA 12.4, install MAGI requirements, install ffmpeg, and optionally install MagiAttention for Hopper-family acceleration.

For agent-guided work, prefer an isolated environment rather than mutating a user's shared Python. Do not install broad optional stacks unless the selected workflow needs them.

## Minimum source-code dependency set

The repository requirements include these notable runtime groups:

- PyTorch 2.4.0 / torchvision 0.19.0 / torchaudio 2.4.0 with CUDA 12.4.
- Attention/runtime acceleration: `flash-attn==2.4.2`, `flashinfer-python==0.2.0.post2` from the CUDA 12.4 / torch 2.4 wheel index, Triton, and optional MagiAttention for Hopper GPUs.
- Model/prompt dependencies: `transformers==4.42.3`, `diffusers==0.29.2`, `sentencepiece==0.2.0`, `ftfy`, BeautifulSoup, Hugging Face hub dependencies, and safetensors.
- Media and utility dependencies: `ffmpeg-python`, `imageio`, `imageio[ffmpeg]`, `Pillow`, `numpy==1.26.4`, `matplotlib`, `rich`, `gpustat`, `torchdiffeq`, `timm`, and protobuf.
- System/runtime tool: ffmpeg executable with MP4/H.264 encode/decode support.

Treat dependency installation as environment-specific. A compatible runtime should pass import checks for the documented Python/CUDA/PyTorch stack, attention libraries, media packages, ffmpeg, and a tiny CUDA tensor before any checkpoint-backed generation attempt.

## Asset checklist

Full generation requires local files for all of these assets:

| Asset | Where it is referenced | Notes |
| --- | --- | --- |
| MAGI DiT checkpoint | `runtime_config.load` | The loader appends `inference_weight`, `inference_weight.distill`, or `inference_weight.fp8` below this directory depending on config flags. |
| T5 checkpoint | `runtime_config.t5_pretrained` and ComfyUI `MagiTextEncoder.t5_pretrained_path` | Used to encode prompts. 4.5B release configs place T5 on CPU; 24B configs place it on CUDA. |
| VAE checkpoint | `runtime_config.vae_pretrained` | Used to encode image/video prefixes and decode generated chunks. |
| Special-token NPZ | `SPECIAL_TOKEN_PATH` or default `example/assets/special_tokens.npz` | Prompt processing loads this asset at module import time. |
| Optional input image/video | CLI `--image_path` or `--prefix_video_path`, or ComfyUI loader nodes | Required only for image-to-video or video continuation. |
| Output directory | CLI `--output_path` or ComfyUI `MagiSaveVideo.output_path` | Parent directory must exist and be writable. |

The README's model zoo points to Hugging Face hosted weights under the SandAI organization. Downloading weights can be large and network-dependent; ask before starting large downloads.

## Safe setup workflow

1. Choose a runtime surface: source CLI/API or ComfyUI.
2. Choose a model family from [model-and-config-overview.md](model-and-config-overview.md).
3. Create or enter an isolated Python 3.10 runtime.
4. Install PyTorch/CUDA first, then the rest of the requirements. For `flashinfer-python`, use the wheel index matching CUDA 12.4 and torch 2.4.
5. Install ffmpeg in the environment or on the host path visible to that environment.
6. Run the root preflight helper:

   ```bash
   python scripts/magi_runtime_preflight.py --run-cuda-smoke --source-root <magi-source-root>
   ```

7. Copy a release config and update `load`, `t5_pretrained`, and `vae_pretrained` to local asset paths.
8. Run the inference config checker for source-code runs:

   ```bash
   python sub-skills/inference/scripts/magi_config_check.py <config.json> --world-size <expected-ranks> --check-paths --repo-root <magi-source-root>
   ```

9. Only after preflight passes should you launch source inference or queue a ComfyUI graph.

## Hopper/MagiAttention note

The README recommends installing MagiAttention for Hopper architecture GPUs such as H100/H800 for acceleration. This is an optional acceleration layer for supported hardware, not a substitute for the required PyTorch/CUDA, `flash-attn`, and `flashinfer-python` compatibility checks. Do not install or build MagiAttention automatically unless the user selected a Hopper workflow and approved any source clone/build steps.
