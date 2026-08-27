# Installation and backend reference

Use this before running Kaolin workflows or diagnosing import/backend failures.

## Recommended wheel pattern

Kaolin publishes wheels matched to PyTorch and CUDA versions. A typical CUDA install is:

```bash
pip install torch==<supported-torch-version> --index-url <matching-pytorch-cuda-wheel-index>
pip install kaolin==<kaolin-version> -f https://nvidia-kaolin.s3.us-east-2.amazonaws.com/torch-<torch-version>_cu<cuda-tag>.html
```

Then verify:

```bash
python -c "import torch, kaolin; import kaolin._C; print(torch.__version__, torch.version.cuda, torch.cuda.is_available(), getattr(kaolin, '__version__', None))"
```

Use the root `scripts/check_kaolin_environment.py` helper for a safer structured report.

## Source build pattern

A source build needs PyTorch and NumPy before setup runs. Full CUDA functionality also needs a CUDA toolkit with `nvcc` visible when compiling from source. Useful environment variables:

- `IGNORE_TORCH_VER=1` can bypass the setup-time PyTorch version guard when deliberately testing an unsupported PyTorch version.
- `FORCE_CUDA=1` asks setup to build CUDA extensions even when PyTorch does not detect a GPU; use only for cross-compilation with a valid CUDA toolkit.
- `TORCH_CUDA_ARCH_LIST` limits CUDA architectures for source builds.
- `CUB_HOME` points to CUB headers if the bundled/installed CUB selection conflicts.

Do not use a source checkout imported from the current directory as proof of a successful install. If `_C` is absent, many imports and operations will fail.

## CPU-only installs

CPU-only installs can be useful for:

- Inspecting pure Python APIs and docs.
- Basic data I/O and tensor-container workflows.
- Quaternion math, packed/padded batching, and some metrics.
- CLI/help and optional dependency probes.

CPU-only installs are **not** full verification for CUDA-extension workflows, including SPC kernels/convolution/ray tracing, DIB-R/rasterization, many conversions, and full physics simulation.

## Optional dependency surfaces

| Surface | Dependency signal | Typical owner |
|---|---|---|
| USD I/O and Timelapse USD outputs | `import pxr` or `usd-core` distribution | geometry / visualization |
| GLTF import | `pygltflib` | geometry |
| PLY Gaussian import | `plyfile` | geometry |
| Browser/server visualizer | Flask, Tornado, port availability, browser/WebGL | visualization |
| Jupyter widgets | IPython, ipycanvas, ipyevents, ipywidgets, comm | visualization |
| nvdiffrast rendering | `import nvdiffrast` and compatible GPU/GL/CUDA context | rendering |
| Simplicits/Warp/Newton | `warp-lang`, optional `newton`, CUDA device | physics |
| Downloads/examples | `wget`, network, dataset licenses | root / geometry |

## Validation ladder

1. Import package: `import kaolin`.
2. Import compiled extension: `import kaolin._C`.
3. Probe framework backend: `torch.cuda.is_available()` and a tiny CUDA tensor allocation if CUDA is needed.
4. Import optional modules for the specific workflow.
5. Run the nearest sub-skill smoke script.
6. Only then run native examples/tests, notebooks, long simulations, browser servers, or user assets if explicitly safe/authorized.
