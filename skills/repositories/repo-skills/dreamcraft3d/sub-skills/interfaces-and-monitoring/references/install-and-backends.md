# Install and Backend Triage

This reference distills DreamCraft3D's operator-facing install evidence into a safe decision matrix. It is guidance for diagnosing a user's checkout and environment; do not perform installs or builds without explicit user approval.

## Backend and memory matrix

| Capability | Runtime backend | Minimum signal to check safely | Operational notes |
| --- | --- | --- | --- |
| Full DreamCraft3D default training stages | NVIDIA CUDA GPU | `nvidia-smi` shows at least one visible GPU; Python stack has a CUDA PyTorch wheel compatible with the driver | The DreamCraft3D README requires an NVIDIA GPU with at least 20GB VRAM for the documented path. Its memory tip says default configs were run on 40GB A100 GPUs. CPU is not a truthful substitute for generation quality or full training. |
| Lower-memory experimentation | NVIDIA CUDA GPU | Same as above, plus user accepts lower resolution/quality | The documented memory knobs are `data.height`, `data.width`, `data.random_camera.height`, and `data.random_camera.width`; use smaller values such as 128 only as a deliberate reduction. |
| Parser/config/static checks | CPU or any Python host | Python can read repo files; optional packages may be absent | Safe for diagnostics and command planning, but never claim that CUDA training was verified. |
| Gradio demo launch | CUDA for actual generation; CPU can only inspect syntax/files | `gradio`, `psutil`, `numpy`, and `trimesh` packages are discoverable; port is free; UI configs exist | The app launches a training subprocess with `--gpu 0 --gradio`; it is not a lightweight visualization-only UI. |
| Docker container route | Host Docker plus NVIDIA Container Toolkit | `docker` and `docker compose` are present; host can expose GPUs to containers | Building/running the image is host-mutating and long-running. Treat as a user-approved operator action, not an automatic diagnostic. |

## Python, CUDA, and PyTorch expectations

- Python: `>=3.8`.
- PyTorch: `>=1.12` with CUDA support for real runs.
- Upstream-tested wheels: `torch1.12.1+cu113` / `torchvision0.13.1+cu113`, and `torch2.0.0+cu118`.
- Container recipe wheel: `torch2.0.1+cu118` / `torchvision0.15.2+cu118`.
- CUDA driver/toolkit: the NVIDIA driver must meet or exceed the minimum driver version for the CUDA toolkit or wheel family in use. A working `nvidia-smi` only proves driver visibility, not PyTorch wheel compatibility.
- `launch.py --gpu` is ignored when `CUDA_VISIBLE_DEVICES` is already set; in that case all devices visible through the environment are used by PyTorch Lightning.

## Dependency families from the repo recipe

The repo's dependency surface is broad. Group failures by family instead of treating every import error as a single `pip install -r requirements.txt` problem:

| Family | Examples in the repo dependency set | Why it matters |
| --- | --- | --- |
| Core orchestration/config | `lightning==2.0.0`, `omegaconf==2.3.0`, `jaxtyping`, `typeguard` | Required by `launch.py`, config loading, trainer setup, and optional runtime type checking. |
| Diffusion/model stack | `diffusers<=0.23.0`, `transformers`, `accelerate`, `xformers`, `bitsandbytes`, `sentencepiece`, `safetensors`, `huggingface_hub` | Required for DeepFloyd IF, Stable Diffusion, DreamBooth/LoRA, and guidance modules. Version drift can break scheduler/model APIs. |
| Image/video/UI | `opencv-python`, `imageio>=2.28.0`, `imageio[ffmpeg]`, `matplotlib`, `gradio`, `tensorboard` | Used by preprocessing, validation media, Gradio UI, logs, and visualization outputs. |
| Geometry/rendering | `libigl`, `xatlas`, `trimesh[easy]`, `networkx`, `pysdf`, `PyMCubes`, `nvdiffrast` usage in source | Used for DMTet, mesh export, rasterization, and geometry processing. Some packages require native build prerequisites. |
| CUDA extensions | `nerfacc`, `tiny-cuda-nn`, nvdiffrast CUDA/OpenGL contexts, optional `ninja` | Common failure points because they compile or select GPU-specific kernels. `ninja` is optional but recommended to speed extension builds. |
| Zero123/ControlNet support | `einops`, `kornia`, `taming-transformers-rom1504`, `controlnet_aux` | Needed by Stable Zero123 guidance and adjacent conditioning utilities. |

## Docker image recipe distilled

The bundled container recipe uses:

- Base image: `nvidia/cuda:11.8.0-devel-ubuntu22.04`.
- Non-root user defaults: `dreamer` / `dreamers` with configurable UID/GID build args.
- CUDA environment: `CUDA_HOME=/usr/local/cuda` plus CUDA `bin`, `lib64`, and stub library paths.
- Build prerequisites: compiler, Python 3.10 development headers, `pip`, Git/curl/wget, and Mesa/EGL/GL libraries.
- Python wheels/extensions installed in this order: upgraded `pip setuptools ninja`, `torch==2.0.1+cu118` and `torchvision==0.15.2+cu118`, `nerfacc` from the v0.5.2 Git ref, `tiny-cuda-nn` torch bindings, then `requirements.txt`.
- Architecture environment defaults: `TORCH_CUDA_ARCH_LIST="6.0 6.1 7.0 7.5 8.0 8.6 8.9 9.0+PTX"` and `TCNN_CUDA_ARCHITECTURES=90;89;86;80;75;70;61;60`. The recipe comments indicate narrowing these for RTX 30xx (`8.6`) or RTX 40xx (`8.9`) can speed builds.

## Docker host prerequisites distilled

A Docker route requires these host-side conditions before the compose commands are useful:

1. Docker Engine installed and reachable by the current user.
2. Current user either belongs to the `docker` group or uses `sudo docker` according to local policy.
3. NVIDIA Container Toolkit installed and configured so containers can reserve GPUs.
4. On WSL2, systemd enabled if required by the Docker Engine setup.
5. Host driver supports the CUDA 11.8 container stack or an adjusted container recipe.

The compose recipe mounts the repository into the container, reserves an NVIDIA GPU, sets `shm_size` to `4gb`, and sets `NVIDIA_DISABLE_REQUIRE=1` to avoid certain `nvidia-container-cli: requirement error` failures. This can hide a strict container requirement mismatch; still verify CUDA inside the container before starting long runs.

## nvdiffrast context guidance

The Docker install notes warn that the current Dockerfile can fail with the OpenGL-based nvdiffrast rasterizer. Prefer CUDA context overrides in containerized runs:

- Training/rasterizer: `system.renderer.context_type=cuda`.
- Mesh export: `system.exporter.context_type=cuda`.

The DreamCraft3D geometry and texture configs already set `system.renderer.context_type: cuda`. Mesh export is different: the mesh exporter code defaults to `context_type: gl`, so export commands in Docker or headless servers should include `system.exporter.context_type=cuda`.
