# Troubleshooting

Use this reference when MonoGS setup, native imports, or GUI/backend checks fail.

## 1) CUDA is invisible
### Symptoms
- `torch.cuda.is_available()` is `False`
- `device="cuda"` allocations fail
- `gaussian_splatting.scene.gaussian_model` or the renderer crash during import

### Likely causes
- CPU-only PyTorch build
- NVIDIA driver not loaded or GPU not exposed to the session
- container or remote environment does not pass through the GPU

### Fix
1. Verify the GPU driver with `nvidia-smi`.
2. Reinstall the reference PyTorch / CUDA 11.6 stack.
3. Re-run the core CUDA smoke before rebuilding extensions.
4. Do not try any SLAM workflow until CUDA is visible.

## 2) `nvcc` is missing
### Symptoms
- `nvcc: command not found`
- extension builds stop before compilation
- `CUDA_HOME` is unset or points to a runtime-only install

### Likely causes
- only the CUDA runtime libraries are installed
- the compiler toolkit is not on `PATH`

### Fix
1. Install a CUDA toolkit that includes `nvcc`, or add a toolkit-dev package.
2. Export `CUDA_HOME` to that toolkit root.
3. Confirm `nvcc --version` before retrying the build.
4. Rebuild `simple_knn` and `diff_gaussian_rasterization`.

## 3) Submodules are missing
### Symptoms
- `submodules/simple-knn/setup.py` cannot be found
- `submodules/diff-gaussian-rasterization/setup.py` cannot be found
- editable installs fail because source files are absent

### Fix
1. Run `git submodule update --init --recursive`.
2. Check `git submodule status` again.
3. Re-run the editable installs once the sources are present.

## 4) Extension ABI or compiler failures
### Symptoms
- `torch.utils.cpp_extension` build errors
- `undefined symbol` at import time
- `_GLIBCXX_USE_CXX11_ABI` mismatch messages
- missing host headers such as `crypt.h`

### Likely causes
- compiler version does not match the installed PyTorch/CUDA toolchain
- cached build artifacts came from a different environment
- host development headers are hidden from the build search path

### Fix
1. Use a compiler pair that matches the local PyTorch / CUDA stack.
2. If the current conda compiler is too new, try a GCC 10 toolchain.
3. Clear the extension build artifacts and rebuild.
4. If host headers are hidden, expose them with `CPATH` or install the host development headers.

## 5) Pillow or libtiff-style import failure
### Symptoms
- `from PIL import Image` fails
- `libtiff.so.5` or a similar shared-library error appears
- dataset helpers fail before any data is loaded

### Fix
1. Reinstall Pillow from a compatible wheel or pip build.
2. Re-run the PIL import smoke.
3. If the conda package keeps the wrong shared library, replace it with a pip wheel and retry.

Known fallback:
```bash
python -m pip install --force-reinstall --no-deps Pillow==9.4.0
```

## 6) `pyrealsense2` is missing
### Symptoms
- `import pyrealsense2` fails

### Meaning
- expected unless you are preparing the live RealSense path
- offline SLAM, evaluation, and the base GUI stack can still be prepared without it

### Fix
- install `pyrealsense2` only when you need the Intel RealSense workflow
- otherwise treat it as optional and continue

## 7) GUI optional dependencies are missing
### Symptoms
- `import open3d.visualization.gui`, `from OpenGL import GL`, `import glfw`, or `import imgviz` fails
- the GUI window does not open
- headless sessions fail to create an OpenGL context

### Likely causes
- GUI packages were not installed from the manifest
- the session has no display server or usable OpenGL driver

### Fix
1. Keep the manifest GUI packages installed.
2. Ensure a display server, X11 forwarding, or other valid windowing path is available.
3. Verify the graphics driver stack.
4. Re-run the GUI import smoke.

Core GUI packages to expect:
- `open3d==0.17.0`
- `PyOpenGL`
- `glfw`
- `PyGLM`
- `imgviz`

## 8) Use the checker
When the failure is unclear, run the environment checker from this sub-skill directory:

```bash
python ../../scripts/check_monogs_environment.py
```

If the checker passes, the environment is ready for the other MonoGS sub-skills.
