# Installation and Backend Reference

## Install variants

```bash
pip install colossalai
python -c "import colossalai; print(colossalai.__version__)"
```

Source inspection or development usually follows:

```bash
python -m pip install -r requirements/requirements.txt
python -m pip install -e .
```

Use `BUILD_EXT=1` only when you need ahead-of-time CUDA kernels and have a compatible CUDA toolkit/compiler stack:

```bash
BUILD_EXT=1 python -m pip install .
```

If `BUILD_EXT=1` is omitted, ColossalAI may build kernels lazily at runtime. That is acceptable for many workflows but can surprise users with first-use compile overhead.

## Backend checks

```bash
python - <<'PY'
import torch
print(torch.__version__, torch.version.cuda)
print(torch.cuda.is_available(), torch.cuda.device_count())
if torch.cuda.is_available():
    print(torch.cuda.get_device_name(0), torch.cuda.get_device_capability(0))
PY
colossalai check -i
```

ColossalAI's primary routes are CUDA-centric. CPU can validate import, config parsing, and CLI help, but it is only a partial substitute for distributed training, Gemini/ZeRO, ShardFormer, or inference acceleration.

## Optional extras and build tools

- `CUDA_HOME`/`nvcc`: needed for source/AOT extension builds; not always needed for PyTorch CUDA wheel execution.
- Apex: needed only for selected fused normalization paths.
- flash-attn: needed only for workflows that enable flash attention or rely on models requiring it.
- TensorNVMe: needed only for async checkpoint save or NVMe/offload-specific workflows.
- Application packages: create separate environments because app requirements can conflict with the core package.

## Read `colossalai check -i`

Important fields:

- `Colossal-AI version`: import/package version.
- `PyTorch version`: PyTorch runtime version.
- `System CUDA version`: toolkit discovered through `CUDA_HOME`; `N/A` means toolkit not visible.
- `CUDA version required by PyTorch`: CUDA runtime embedded in the PyTorch wheel.
- AOT compilation fields: only meaningful when ColossalAI was installed with prebuilt extensions.

A healthy PyTorch CUDA wheel can show system CUDA as `N/A`. Source builds and AOT extension builds cannot.
