# AdelaiDet compatibility and installation

AdelaiDet is legacy Detectron2-era code. Treat dependency selection as part of the task, not as a routine `pip install -e .`.

## Verified stack shape

Use this stack when you need the unmodified CUDA extension to build and run:

| Component | Verified family | Why |
| --- | --- | --- |
| Python | 3.9 | Compatible with PyTorch 1.10 and Detectron2 0.6 wheels. |
| PyTorch | 1.10.x CUDA 11.3 | Still ships THC headers required by `adet/layers/csrc/ml_nms/ml_nms.cu`; supports A100/SM80. |
| TorchVision | 0.11.x | Matching PyTorch 1.10 release. |
| Detectron2 | 0.6 `cu113` / `torch1.10` wheel | Matches the PyTorch/CUDA ABI and AdelaiDet registry APIs. |
| CUDA toolkit dev | 11.3 | Needed for `cuda_runtime.h` and NVCC extension compilation. |
| Compiler | GCC/G++ 9.x | Safe compiler family for CUDA 11.3 and PyTorch 1.10 extension builds. |
| Pillow | `<10` | Detectron2 0.6 references removed `PIL.Image.LINEAR` constants. |
| rapidfuzz | `<3` | AdelaiDet text evaluation imports the removed `rapidfuzz.string_metric` API. |
| NumPy | `1.23.x` | Avoids NumPy-2 risk with this old PyTorch stack. |
| OpenCV | headless 4.8.x | Provides `cv2` for SOLOv2/demo/data visualization without pulling GUI libs. |

## Reproducible install skeleton

Adapt environment names and paths to your machine:

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

export CUDA_HOME="$CONDA_PREFIX"
export CC="$CONDA_PREFIX/bin/x86_64-conda-linux-gnu-gcc"
export CXX="$CONDA_PREFIX/bin/x86_64-conda-linux-gnu-g++"
export CUDAHOSTCXX="$CXX"
export TORCH_CUDA_ARCH_LIST="8.0"   # add more architectures if needed
export MAX_JOBS=4
python -m pip install --no-build-isolation -e /path/to/AdelaiDet
```

Then from this skill directory run:

```bash
python scripts/check_install.py --cuda-ops
```

## Why modern PyTorch is risky

A modern PyTorch 2.x + CUDA 12.x stack can build Detectron2, but unmodified AdelaiDet CUDA extension compilation fails because `ml_nms.cu` includes legacy THC headers:

```text
fatal error: THC/THC.h: No such file or directory
```

Do not work around this by silently installing a CPU-only AdelaiDet extension if the task needs real FCOS/BAText/DefROIAlign CUDA behavior. Either use the legacy stack above, patch the extension source intentionally, or narrow the task to import/config-only diagnostics.

## CPU-only limitations

A CPU-only build can import some config and BezierAlign surfaces, but it does not validate the CUDA-only custom operators. The source `DefROIAlign` and `ml_nms` headers raise CPU-not-supported/not-implemented errors. For training/inference tasks that exercise those operators, require a CUDA build and run `scripts/check_install.py --cuda-ops`.

## Optional export/runtime dependencies

ONNX export and comparison workflows may additionally need `onnx`, `onnxruntime`, Caffe2, TensorRT, Caffe, NCNN, or model-specific weights. They were not part of the minimum verified setup. Install them only for a concrete export/deployment task and keep failures scoped to `export-convert`.
