# Installation and backend preflight

## Package install

Use a supported Python (the 1.1.x metadata declares `>=3.8`; Python 3.8-3.10 is the conservative range for compiled dependencies). Install the public distribution or an editable local package:

```bash
python -m pip install nerfstudio
# or, while developing a package:
python -m pip install -e .
```

The base distribution includes torch/torchvision, `gsplat`, `nerfacc`, Open3D, image/video, config, logging, and viewer dependencies. Do not install every optional extra automatically.

## CUDA path

For production Nerfacto, Instant-NGP, Splatfacto, rendering, and checkpoint export, install a torch wheel whose CUDA runtime is supported by the NVIDIA driver. The project documentation uses CUDA 11.7/11.8 examples and a CUDA-capable PyTorch/TorchVision pair. Prove the backend before a long run:

```bash
python -c "import torch; print(torch.__version__, torch.version.cuda, torch.cuda.is_available()); print(torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'no cuda')"
```

The torch implementation can be used for reduced checks when tiny-cuda-nn is absent. That fallback does not prove CUDA extension performance.

## External binaries

- `ffmpeg` is needed for video/image preprocessing paths that invoke frame extraction or media conversion.
- `colmap` is needed for ordinary image/video pose reconstruction. `--skip-colmap` is appropriate only when a compatible sparse model already exists.
- `hloc`, Project Aria tools, and device-specific packages are optional and mode-specific.

Check without changing the environment:

```bash
ffmpeg -version
colmap -h
```

A missing binary should be reported as a prerequisite gap, not hidden by selecting a different command.

## Quick diagnostic

Run `python <skill-root>/scripts/check_environment.py --check-cli` for imports, entry points, external binaries, and help checks. Add `--require-cuda` when the requested route cannot use a CPU alternative.
