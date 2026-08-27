# Backends and Assets

## When to read

Read this when you need to understand what hardware or assets MASt3R-SLAM
actually needs, which pieces are optional, and which ones block a real run.

## Required backend

The primary MASt3R-SLAM workflow requires CUDA.

Why:

- `main.py` hard-codes `device = "cuda:0"`.
- `mast3r_slam.global_opt` and `mast3r_slam.matching` call the compiled
  `mast3r_slam_backends` extension.
- `mast3r_slam.setup.py` only defines the extension when `torch.cuda.is_available()`
  is true.
- `tictoc.Timer` uses CUDA events.
- The verified host used NVIDIA A100-SXM4-40GB GPUs with driver 580.126.20 and
  compute capability 8.0.

CPU-only import checks are useful, but they do not prove the selected runtime.

## Minimum asset set for real runs

Before a real run on a benchmark or live input, stage these checkpoint files in
`checkpoints/`:

| File | Purpose |
| --- | --- |
| `MASt3R_ViTLarge_BaseDecoder_512_catmlpdpt_metric.pth` | MASt3R backbone weights used by `load_mast3r()` |
| `MASt3R_ViTLarge_BaseDecoder_512_catmlpdpt_metric_retrieval_trainingfree.pth` | Retrieval database backbone used by `load_retriever()` |
| `MASt3R_ViTLarge_BaseDecoder_512_catmlpdpt_metric_retrieval_codebook.pkl` | Retrieval codebook used by the ASMK/IVF machinery |

The skill does not auto-download these files. Use the bundled checkpoint
manifest or the repo README URLs when the user approves network access.

## Optional components

| Component | Why it exists | When to install |
| --- | --- | --- |
| `pyrealsense2` | RealSense live camera input | Only for `--dataset realsense` |
| `torchcodec` | Faster MP4 decoding | Optional speed-up for video input |
| `in3d`, `moderngl`, `glfw`, `imgui` | Visualization/UI | Needed for the default visualization path |

## Verified backend facts from the inspection environment

- `torch 2.5.1` with CUDA 12.4 imported successfully.
- `torch.cuda.is_available()` was true and a tiny CUDA tensor allocation worked.
- `nvcc` was not on the host PATH, so the conda `cuda-nvcc` package and CUDA
  headers had to be installed into the private prefix.
- `opencv-python==4.10.0.84` was required to stay compatible with
  `numpy==1.26.4`.

## Signs of backend trouble

- `CUDA not found, cannot compile backend!` from the root `setup.py` means the
  build toolchain is incomplete.
- `cuda_runtime.h: No such file or directory` means headers are missing, even if
  `torch.cuda.is_available()` is already true.
- `undefined symbol: iJIT_NotifyEvent` means the torch/MKL/OpenMP stack needs a
  compatibility repair.
- `ModuleNotFoundError: dust3r` from a custom snippet usually means the Dust3R
  path hook was not imported first.
