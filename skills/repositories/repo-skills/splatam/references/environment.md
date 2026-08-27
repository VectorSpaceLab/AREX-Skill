# Environment and Backend Reference

## Purpose

Read this before installing, repairing, or verifying a SplaTAM runtime. SplaTAM has no package metadata (`pyproject.toml`/`setup.py`); the repo scripts are normally run from a checkout root and add that root to `sys.path` themselves.

## Backend requirements

- Primary workflows require NVIDIA CUDA. The code uses `.cuda()` calls, CUDA tensors, and the `diff_gaussian_rasterization` extension in SLAM, Gaussian splatting, evaluation, visualization, and live capture paths.
- There is no full CPU substitute for the selected reconstruction or capture workflows.
- A visible GPU is not enough: PyTorch, the CUDA compiler/toolkit used to build the custom rasterizer, and the loaded CUDA runtime libraries must match closely enough for the extension to import.

## Evidence-backed install profile

The README recommends this baseline:

```bash
conda create -n splatam python=3.10
conda activate splatam
conda install -c "nvidia/label/cuda-11.6.0" cuda-toolkit
conda install pytorch==1.12.1 torchvision==0.13.1 torchaudio==0.12.1 cudatoolkit=11.6 -c pytorch -c conda-forge
pip install -r requirements.txt
```

The README also notes that SplaTAM has been tested outside the original stack, including Torch 2.3.0 with CUDA 12.1. Treat this as compatibility evidence, not permission to freely mix arbitrary Torch/CUDA/compiler versions.

## Dependency hazards

The repository requirements are mostly unpinned. On modern package indexes, a naive `pip install -r requirements.txt` can upgrade core packages beyond the documented stack. Watch for these hazards:

- `kornia` may pull a modern `torch>=2` wheel and overwrite a conda-installed Torch 1.12 runtime.
- New `torch` wheels may pull CUDA 13 Python packages while the system/compiler toolkit is CUDA 11.x or 12.x.
- `numpy>=2` can break older compiled packages; prefer `numpy<2` for the README-era Torch 1.12 environment.
- `torchmetrics` and `torchvision` should be version-compatible; import failures in `torchmetrics.image.lpip` often mean the pair is mismatched.
- The custom rasterizer should be installed after the final Torch/CUDA/compiler selection, usually with build isolation disabled so it can see the active Torch headers:

  ```bash
  python -m pip install --no-build-isolation --force-reinstall \
    'git+https://github.com/JonathonLuiten/diff-gaussian-rasterization-w-depth.git@cb65e4b86bc3bd8ed42174b72a62e8d3a3a71110'
  ```

If the active CUDA toolkit is provided by conda, ensure `nvcc --version`, `torch.version.cuda`, and `torch.cuda.is_available()` agree with the intended backend before compiling.

## Safe import/backend check

Run the bundled check from a checkout root after installation or repair:

```bash
python scripts/check_env.py --require-cuda --require-rasterizer
```

A minimal manual check is:

```bash
python - <<'PY'
import torch
print('torch', torch.__version__, 'torch CUDA', torch.version.cuda)
print('cuda available', torch.cuda.is_available(), 'device count', torch.cuda.device_count())
if torch.cuda.is_available():
    x = torch.ones(1, device='cuda')
    print('device', torch.cuda.get_device_name(0), 'tensor', float(x.item()))
from diff_gaussian_rasterization import GaussianRasterizer, GaussianRasterizationSettings
print('rasterizer import ok')
PY
```

Do not treat imports of `torch`, `open3d`, or `cv2` alone as proof that SplaTAM can run; the rasterizer import is the gate for the selected workflows.

## Expected modules

A complete selected-scope environment should import:

- `torch`, `torchvision`
- `diff_gaussian_rasterization`
- `open3d`
- `cv2`
- `wandb`
- `pytorch_msssim`
- `torchmetrics.image.lpip`
- `plyfile`
- `cyclonedds` for capture workflows

`faiss-gpu` appears in `environment.yml` and helper code, but it is not required for the selected reconstruction/capture operating scope unless a future task explicitly uses neighbor-search utilities.

## What to record during repair

When fixing an environment for a future verification run, record private setup evidence outside the runtime skill:

- Python version and environment manager.
- Torch, TorchVision, CUDA compiler, CUDA runtime, GPU names, and driver compatibility.
- Exact rasterizer installation command and whether it built or imported.
- `pip check` output.
- Any unverified required backend block.

Do not copy local environment paths, activation commands, or cache paths into public runtime skill files.
