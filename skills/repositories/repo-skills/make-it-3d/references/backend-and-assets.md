# Backend, Dependency, and Asset Map

## Dependency Families

| Area | Evidence | Purpose | Notes |
| --- | --- | --- | --- |
| PyTorch + torchvision + torchaudio CUDA | README install block; all model code | tensor training, DPT, rendering, CUDA kernels | README pins torch 1.10.0/cu113 era. Modern hosts may need a compatible newer torch plus matching extension builds. |
| tiny-cuda-nn (`tinycudann`) | README; `nerf/network_tcnn.py` | default `--backbone tcnn` hash-grid encoder | Missing module prevents default backbone construction. Use `--backbone vanilla` only to avoid tcnn; it does not avoid raymarching CUDA because `main.py` forces `opt.cuda_ray = True`. |
| OpenAI CLIP (`clip`) | README; `nerf/clip.py`; `nerf/utils.py`; `nerf/sd.py` | CLIP guidance and CLIP losses inside Stable Diffusion training | Install from OpenAI GitHub as documented. |
| diffusers + transformers + Hugging Face hub | README; `nerf/sd.py`; `main.py` BLIP2 imports | Stable Diffusion prior, CLIP text/image encoders, optional BLIP2 captioning | May require network/cache/token. Passing `--text` avoids BLIP2 captioning but not Stable Diffusion guidance unless `--guidance clip` is used. |
| PyTorch3D | README; `nerf/refine_utils.py` | point-cloud rasterization/compositing during refinement | Wheels are Python/Torch/CUDA-version sensitive; install before attempting refine. |
| contextual_loss_pytorch | README; `nerf/utils.py` | refine stage contextual texture loss | Missing module can break broad imports before refinement actually starts. |
| DPT + timm | README; `DPT/` | single-view depth estimation for reference image | Main expects `dpt_weights/dpt_hybrid-midas-501f0c75.pt`; DPT scripts have their own CLI defaults under `weights/`. |
| raymarching CUDA extension | README; `raymarching/setup.py`; `raymarching/backend.py` | accelerated ray marching kernels | Requires CUDA-capable torch and usually `nvcc`/toolkit for build. `raymarching/backend.py` also lazily builds if installed `_raymarching` is absent. |
| xatlas + nvdiffrast | `nerf/renderer.py` mesh export path | UV unwrap and rasterization for textured mesh export | Needed for `--save_mesh`, not for command generation. |
| open3d | `requirements.txt`; `nerf/renderer.py` | point-cloud writing | README pins `open3d==0.9.0.0`; that old pin is often unavailable for newer Python. |

## Backend Criticality

- **CUDA is required for practical selected workflows.** The training loop, raymarching extension, Stable Diffusion guidance, BLIP2 captioning, PyTorch3D refine utilities, and mesh export are GPU-oriented. CPU-only checks can validate command generation and source syntax but do not verify the main workflow.
- **Network/model-cache access is required unless assets are already cached.** Stable Diffusion, CLIP, BLIP2, and DPT weights can all trigger downloads if missing.
- **A compiler/toolkit may be required.** The raymarching extension has CUDA source files and the lazy backend loads/builds `_raymarching` when imported. A host with visible GPUs but no `nvcc` can still fail source extension installation.

## Asset Checklist

Before long runs, confirm:

```text
[ ] Reference image is RGBA or has an alpha mask.
[ ] DPT hybrid model exists at dpt_weights/dpt_hybrid-midas-501f0c75.pt or source path is adjusted.
[ ] Hugging Face login/token/cache is ready for the chosen Stable Diffusion model.
[ ] If --text is omitted, BLIP2 cache/memory/network are acceptable.
[ ] CUDA torch is importable and can allocate a tiny tensor.
[ ] tinycudann is installed when using --backbone tcnn.
[ ] raymarching imports or can build with the selected torch/CUDA/toolkit.
[ ] PyTorch3D/contextual_loss/open3d are available before refinement/export.
[ ] xatlas and nvdiffrast are available before textured mesh export.
```

## Version Strategy

The README's exact torch 1.10/cu113 stack is a historical baseline, not a guarantee for all modern machines. Prefer one coherent stack:

1. Choose a Python version with wheels for torch, torchvision, PyTorch3D, tiny-cuda-nn, and open3d if needed.
2. Install torch/torchvision first.
3. Install CUDA extension packages against that torch ABI.
4. Build/install `./raymarching` last and test a tiny raymarching import/device operation.
5. Only then download large model assets and run long optimization.
