# Installation and runtime readiness

FFCV builds a native `_libffcv` extension from C++ source. A usable installation
needs Python package dependencies **and** the native libraries used by the
extension: OpenCV, TurboJPEG/libjpeg-turbo, pthreads on Unix-like systems, and
a working C/C++ compiler toolchain for source builds.

## Public installation shape

For a published wheel, start with the package's documented install path and a
compatible PyTorch/torchvision pair:

```bash
python -m pip install ffcv
python -c "import ffcv, ffcv._libffcv; print(ffcv.__version__)"
```

For a source checkout, install the native libraries with the operating system
or Conda package manager first, make sure `pkg-config` can resolve `opencv4`
(or `opencv`) and `libturbojpeg`, then install the package:

```bash
python -m pip install -e .
python -m pip check
python -c "import ffcv, ffcv._libffcv; print(ffcv.__version__)"
```

Do not treat `pip install` success as proof that the extension loaded. The
import check is the gate that catches missing shared libraries, incompatible
C++ ABI, and wrong `pkg-config` paths.

## Dependency roles

- `torch` supplies tensors, devices, distributed sampling, and optional CUDA
  execution.
- `numpy` and `numba` support field storage and the compiled CPU pipeline.
- OpenCV and TurboJPEG support RGB encoding, resizing, and JPEG decode.
- `pytorch_pfn_extras` and CuPy are needed by the GPU implementation of
  `NormalizeImage`.
- `fastargs`, torchvision, and WebDataset are used by selected examples or
  optional conversion/training integrations, not every minimal loader.
- `pandas` and `terminaltables` support the optional micro-benchmark CLI.

Choose a torch wheel that matches the host driver and Python version. FFCV's
CPU paths can be inspected without CUDA, but `ToDevice`, GPU normalization,
nonblocking-transfer tests, and GPU training recipes require a real compatible
CUDA runtime. A visible GPU alone does not make every wheel or extension
compatible.

## Verification sequence

Run these checks from the environment that will execute the task:

```bash
python -m pip check
python -c "import ffcv, ffcv._libffcv"
python -c "from ffcv.writer import DatasetWriter; from ffcv.loader import Loader"
python -m ffcv.benchmarks --help
```

For CUDA-specific work, additionally run a tiny allocation and report the torch
CUDA version, device name, and capability. Reserve a device before testing;
shared GPU memory pressure can produce an OOM unrelated to package correctness.
For CPU-only work on a host with CUDA visible, hiding CUDA for the process can
avoid FFCV's stream setup and makes the intended baseline explicit.

## Version/provenance caution

This source snapshot's packaging metadata reports `ffcv` 1.0.1 while its
`ffcv.__version__` constant reports 1.0.2. Treat the source commit and file
format compatibility as authoritative, and validate a `.beton` file with the
same build that wrote it. Do not use version labels alone to establish format
compatibility.
