# Environment and installation

## Purpose

Read this before creating a runtime environment or diagnosing import failures. MimicMotion is CUDA-first and depends on a narrow set of package versions that work together.

## Verified runtime stack

The verified CUDA setup used:

- Python 3.11
- PyTorch 2.5.1 + cu124
- torchvision 0.20.1 + cu124
- diffusers 0.27.0
- transformers 4.32.1
- huggingface-hub 0.20.2
- decord 0.6.0 from conda-forge
- onnxruntime-gpu 1.29.0
- omegaconf 2.3.0
- einops 0.8.0
- opencv-python 4.10.0.84
- matplotlib 3.9.1
- av 12.2.0
- cog 0.22.0
- ffmpeg available on PATH

The verified host had an NVIDIA A100-SXM4-40GB GPU and a CUDA-compatible driver.

## Recommended install shape

A practical installation sequence is:

1. Create a private Python 3.11 environment.
2. Install the CUDA PyTorch wheel pair first.
3. Install the rest of the Python packages.
4. Install `decord` from conda-forge or another verified platform-specific build.
5. Confirm `ffmpeg` is available.
6. Run `scripts/check_runtime.py --repo-root <checkout>`.

## Example install commands

```bash
python -m pip install torch==2.5.1 torchvision==0.20.1 --index-url https://download.pytorch.org/whl/cu124
python -m pip install diffusers==0.27.0 transformers==4.32.1 einops==0.8.0 omegaconf==2.3.0 \
  opencv-python==4.10.0.84 matplotlib==3.9.1 onnxruntime-gpu==1.29.0 av==12.2.0 cog==0.22.0 \
  huggingface-hub==0.20.2
```

If you use Conda, install `decord=0.6.0` from `conda-forge` in the same prefix or another verified prefix that still satisfies the final CUDA checks.

## Why the version pin matters

- `diffusers 0.27.0` is not compatible with the newest `huggingface-hub` releases in this repository's import path; `huggingface-hub==0.20.2` was the verified pairing.
- The PyPI `decord` wheel can be misleading on this host; the conda-forge build provided the clean verified path.
- The source pipeline calls `torch.cuda.device(...)`, so CPU-only installs are not a real substitute for the runtime path.

## Container/deployment notes

The `cog.yaml` file also expects these system packages when building a containerized runtime:

- `libgl1-mesa-glx`
- `libglib2.0-0`

## Required backend checks

Before attempting the local inference workflow, make sure these pass:

- `torch.cuda.is_available() == True`
- `torch.cuda.get_device_name(0)` is available
- `onnxruntime.get_available_providers()` includes `CUDAExecutionProvider`
- `ffmpeg -version` works
- the runtime imports listed above succeed
