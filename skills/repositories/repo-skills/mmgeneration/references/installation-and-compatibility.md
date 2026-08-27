# Installation and Compatibility

## Purpose

Read this when installing MMGeneration into a new environment, repairing a broken install, or checking whether a wheel set is compatible with the repo.

## What the repo expects

- The package import name is `mmgen`.
- The repository depends on PyTorch, MMCV, and MMClassification.
- `setup.py` reads `requirements.txt`, which pulls in the runtime list and the test-oriented dependencies used by this repo.
- `setup.py` imports `torch` while building metadata, so install PyTorch before installing the repo itself.

## Compatible install order

A safe order for a fresh environment is:

1. Install PyTorch and torchvision first.
2. Install a matching `mmcv-full` wheel in the 1.x line.
3. Install `mmcls` in the 0.x line.
4. Install the repo editable package with `pip install -e .`.
5. Run the shared install check script.

Example pattern:

```bash
python -m pip install torch torchvision
python -m pip install 'mmcv-full==1.7.2' -f https://download.openmmlab.com/mmcv/dist/cu117/torch2.0/index.html --only-binary mmcv-full
python -m pip install 'mmcls==0.25.0'
python -m pip install -e .
python scripts/check_install.py
```

## Verified inspection combo

The following combination was verified during skill construction on this host:

- Python 3.11.14
- torch 2.0.1
- torchvision 0.15.2
- mmcv-full 1.7.2
- mmcls 0.25.0
- CUDA-enabled runtime available on an NVIDIA A100 host

That combo is useful evidence, but it is not the only possible environment. The repo's own historical CI used Python 3.7 and torch 1.8.1-era wheels, so if you are aligning with an older toolchain, keep the MMCV line in the 1.x family and verify `mmcv.runner` still imports.

## Wheel and backend notes

- `mmcv 2.x` is not a drop-in replacement here; the repo still uses `mmcv.runner` and `mmcv.parallel`.
- A CPU-only environment can still verify configuration and API behavior, but GPU-specific workflows such as latent editing, distributed metrics, or TorchServe packaging need the appropriate runtime and model assets.
- If `torch.cuda.is_available()` is false on a GPU host, suspect the wrong torch wheel, a missing driver, or container GPU passthrough.
- If `import mmcv.ops` fails, the environment likely has `mmcv` instead of `mmcv-full`, or the wheel does not match the torch/CUDA combination.

## Minimal import check

```bash
python - <<'PY'
import mmgen
from mmgen.apis import init_model
print(mmgen.__version__)
print(init_model)
PY
```

For a more complete smoke test on a GPU-capable host, use `scripts/check_install.py --check-mmcv-ops --check-cuda`. On a CPU-only host, omit `--check-cuda` and keep the import check.
