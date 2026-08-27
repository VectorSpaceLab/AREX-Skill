# Make-It-3D Dependency Map

## Core Runtime

The README documents a PyTorch 1.10/cu113-era stack plus several GitHub packages. Treat it as historical evidence and adapt to the user's host carefully.

```bash
pip install torch==1.10.0+cu113 torchvision==0.11.1+cu113 torchaudio==0.10.0+cu113 -f https://download.pytorch.org/whl/cu113/torch_stable.html
pip install git+https://github.com/NVlabs/tiny-cuda-nn/#subdirectory=bindings/torch
pip install git+https://github.com/openai/CLIP.git
pip install git+https://github.com/huggingface/diffusers.git git+https://github.com/huggingface/huggingface_hub.git
pip install git+https://github.com/facebookresearch/pytorch3d.git
pip install git+https://github.com/S-aiueo32/contextual_loss_pytorch.git
pip install -r requirements.txt
pip install ./raymarching
```

Important requirements from `requirements.txt`: `ninja`, `trimesh`, `opencv-python`, `tensorboardX`, `numpy`, `pandas`, `tqdm`, `matplotlib`, `PyMCubes`, `rich`, `dearpygui`, `scipy`, `xatlas`, `scikit-learn`, `imageio`, `imageio-ffmpeg`, `timm`, `einops`, `open3d==0.9.0.0`, `torchmetrics`, `tensorboard`, and `torch-ema`.

## Dependency-to-Workflow Mapping

| Dependency | Needed for | Failure if missing |
| --- | --- | --- |
| CUDA-enabled torch/torchvision | all realistic training/rendering | CPU-only run cannot verify main workflow. |
| `tinycudann` | default `--backbone tcnn` | default model construction fails. |
| `raymarching` / `_raymarching` | renderer when `opt.cuda_ray=True` | train/test ray marching calls fail; source forces this flag. |
| `DPT` + `timm` + DPT weights | reference depth estimation | run fails before Trainer setup or produces no depth prior. |
| `diffusers`, `transformers`, HF cache/token | Stable Diffusion guidance and BLIP2 captioning | download/auth/import failures. |
| OpenAI `clip` | CLIP guidance and loss terms | import/training failures in `nerf.utils`, `nerf.clip`, or `nerf.sd`. |
| `pytorch3d` | refinement point rasterization/compositing | import-time failure through `nerf.refine_utils`. |
| `contextual_loss` | refine texture loss | import-time or refine-stage failure. |
| `open3d` | point-cloud output | point-cloud write/export failure. |
| `xatlas`, `nvdiffrast` | textured mesh export | `--save_mesh` failure. |

## Version Pitfalls

- `open3d==0.9.0.0` is an old pin and may not have wheels for modern Python. If a modern environment is needed, test a newer Open3D version explicitly and record the deviation.
- PyTorch3D wheels are tightly coupled to Python, PyTorch, CUDA, and platform. Install it after torch is fixed.
- tiny-cuda-nn may build from source or require a compatible wheel. Avoid changing torch after installing it.
- `raymarching/setup.py` uses `torch.utils.cpp_extension.CUDAExtension`; building requires a compatible CUDA toolkit/compiler, not just a driver.
- `main.py` imports many training/refine dependencies at module import time, so a missing optional-looking module can prevent even argument help.
