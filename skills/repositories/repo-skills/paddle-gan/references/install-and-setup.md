# Install and setup

This reference covers the shared environment used by all PaddleGAN leaves. The distribution and import name are both `ppgan`; Paddle itself is a separate prerequisite.

## Choose the Paddle backend first

- **CPU:** install the CPU Paddle package when the task is config parsing, import checks, dataset preparation, or a deliberately CPU-only run. CPU readiness does not prove that a CUDA media workload will run.
- **GPU:** install the CUDA-enabled Paddle package matching the machine's Python, operating system, CUDA toolkit/driver, and cuDNN. Verify `paddle.is_compiled_with_cuda()` and a visible device before claiming GPU readiness.
- Install one Paddle variant per environment; remove a conflicting variant before switching. Do not mix a CPU wheel with CUDA runtime assumptions, or a CUDA wheel with an unsupported driver.
- Let the environment's approved package source select a compatible version rather than copying a version from an unrelated machine.

From the environment that will execute the work, check the backend before installing application extras:

```bash
python -c "import paddle; print(paddle.__version__, paddle.is_compiled_with_cuda())"
```

## Install `ppgan`

Use a clean virtual environment and install Paddle before `ppgan` so dependency resolution does not silently replace the chosen backend:

```bash
python -m pip install --upgrade pip
python -m pip install ppgan
python scripts/check_install.py
```

For a local source checkout, `python -m pip install -e .` creates an editable install: imports resolve to the working tree, code edits are immediately visible, and package metadata/dependencies are installed. It is useful for development, but an incomplete checkout or changed working tree can make results non-reproducible. A regular `python -m pip install .` (or a package install from the configured index) copies/builds a normal installation and is preferable for a stable runtime. Re-run the checker after switching modes and confirm `python` and `pip` belong to the same environment.

The legacy `paddlegan` console entry point is not a readiness signal in this snapshot. Prefer `python` with the bundled helpers or direct `ppgan` imports; do not repair the entry point as part of routine setup.

## ffmpeg and optional modules

- Video, audio, motion, and lip-sync tasks need an `ffmpeg` executable on `PATH`; verify with `ffmpeg -version` and [the install checker](../scripts/check_install.py). The Python `imageio-ffmpeg` package can provide Python-side support but does not guarantee that the executable required by every workflow is discoverable.
- The declared baseline includes YAML, OpenCV, image/video I/O, SciPy, scikit-image, librosa, numba, natsort, matplotlib, and related utility packages. Install the package's declared requirements, then add only task-specific extras.
- Face workflows may additionally need `dlib` and an available face backend. CLIP is needed only for CLIP-guided latent/style operations. Missing optional modules should be reported as a scoped limitation, not treated as proof that every image workflow is broken.
- Audio imports can fail through old `librosa`/new `setuptools` combinations (for example, missing `pkg_resources`). Resolve that compatibility issue in the environment, then re-run the checker.

## Readiness sequence

1. Run [the install checker](../scripts/check_install.py); add `--require-gpu`, `--require-ffmpeg`, `--require-face`, or `--require-clip` only for requirements of the requested task.
2. For YAML workflows, run [the config checker](../scripts/check_config.py) with the config and intended dotted overrides.
3. Route to the appropriate leaf using [the workflow map](workflow-map.md).
4. Keep weights, datasets, and output directories explicit. Do not assume auto-downloads, writable cache directories, or available GPU memory.

The checker is a diagnostic gate, not a substitute for a small, user-authorized runtime smoke test.
