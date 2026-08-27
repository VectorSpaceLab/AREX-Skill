# Setup and build recipe

AdelaiDet's native extension is the main setup constraint. The unmodified source is best treated as a PyTorch 1.x / Detectron2 0.6 project.

## Environment recipe

```bash
conda create -y -n adelaidet-cu113 -c pytorch -c nvidia \
  python=3.9 pytorch=1.10.2 torchvision=0.11.3 cudatoolkit=11.3 cuda-nvcc=11.3 \
  numpy=1.23 'mkl=2023.1.0' 'intel-openmp=2023.1.0' \
  'gcc_linux-64=9.*' 'gxx_linux-64=9.*' ninja pip setuptools wheel
conda activate adelaidet-cu113
conda install -y -c conda-forge cudatoolkit-dev=11.3.1
python -m pip install 'detectron2==0.6' \
  -f https://dl.fbaipublicfiles.com/detectron2/wheels/cu113/torch1.10/index.html
python -m pip install 'Pillow<10' 'numpy==1.23.5' \
  'opencv-python-headless==4.8.1.78' 'rapidfuzz<3'
```

Then build AdelaiDet:

```bash
export CUDA_HOME="$CONDA_PREFIX"
export CC="$CONDA_PREFIX/bin/x86_64-conda-linux-gnu-gcc"
export CXX="$CONDA_PREFIX/bin/x86_64-conda-linux-gnu-g++"
export CUDAHOSTCXX="$CXX"
export TORCH_CUDA_ARCH_LIST="8.0"     # add architectures for non-A100 hosts
export MAX_JOBS=4
python -m pip install --no-build-isolation -e /path/to/AdelaiDet
```

## Why each pin matters

- `--no-build-isolation`: `setup.py` imports `torch`; build isolation can hide it.
- `torch==1.10.2`: includes legacy THC headers used by `ml_nms.cu`.
- `cudatoolkit-dev=11.3.1`: supplies `cuda_runtime.h`; `cuda-nvcc` alone may not.
- `detectron2==0.6` `cu113/torch1.10` wheel: avoids compiling Detectron2 and matches ABI.
- `Pillow<10`: preserves constants used by Detectron2 0.6.
- `rapidfuzz<3`: preserves `rapidfuzz.string_metric` for text evaluation.
- `opencv-python-headless==4.8.1.78`: supplies `cv2` while avoiding NumPy 2-only OpenCV wheels.

## Build outputs to check

```bash
python - <<'PY'
import adet, torch
import adet._C as C
print('adet', getattr(adet, '__version__', None))
print('torch', torch.__version__, torch.version.cuda, torch.cuda.is_available())
print([name for name in dir(C) if name in {'ml_nms','bezier_align_forward','def_roi_align_forward'}])
PY
```

The source distribution version is `0.2.0`; the import package version reports `0.1.1` in this snapshot. Treat that mismatch as source metadata, not as an install failure.

## Modern-stack escape hatches

If a task intentionally requires modern PyTorch, choose one explicitly:

1. Patch AdelaiDet's native C++/CUDA code to remove THC dependencies and rebuild.
2. Use a CPU/import-only install for config inspection, but do not claim CUDA operators are verified.
3. Use a container or archived environment matching the source-era dependencies.

Do not silently mix PyTorch 2.x with unmodified source for CUDA training/inference tasks.
