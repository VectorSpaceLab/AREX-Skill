# Installation and runtime reference

## Repository shape

mixtral-offloading is a source-only Python repository. It does not provide
`pyproject.toml`, `setup.py`, setup metadata, console entry points, or a package
version. Public code is imported as modules under `src.*` when the user's
checkout root is on `PYTHONPATH` or inserted into `sys.path`.

A typical local setup is:

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
export PYTHONPATH="/path/to/user/mixtral-offloading:${PYTHONPATH}"
python -c "from src.build_model import OffloadConfig, QuantConfig, build_model; print('ok')"
```

Use environment-manager equivalents when Conda or another isolated runtime is
preferred. Do not install or repair dependencies in a shared environment without
approval.

## Runtime dependencies

The repository runtime requirements are:

- `torch>=2.1.0`
- `transformers==4.36.1`
- HQQ from the repository-pinned git commit `37502bea31f2969c6680c0c4a88ca74b3bb234a5`
- `numpy==1.24.4`
- `tqdm==4.66.1`

The code also imports `safetensors`, `triton`, and Hugging Face utilities through
those dependencies. CUDA-capable PyTorch is required for actual offloaded
inference and Triton matmul execution.

## Minimal import check

```bash
PYTHONPATH="/path/to/user/mixtral-offloading" python - <<'PY'
import torch
from src.build_model import OffloadConfig, QuantConfig, build_model
from src.packing import pack_4bit_u8_common
print('torch', torch.__version__, 'cuda', torch.cuda.is_available())
print(OffloadConfig(main_size=4, offload_size=4, buffer_size=1, offload_per_layer=1))
print('imports ok')
PY
```

For a reusable check with clearer output, run `scripts/check_environment.py`.

## CUDA expectations

The README/notebook workflow targets consumer/Colab-style CUDA GPUs. The demo
notes approximately 16 GB VRAM and 11 GB system RAM for normal generation, with
`offload_per_layer=4` as the default and `offload_per_layer=5` as a starting
point for about 12 GB VRAM.

A CUDA smoke should prove:

- `torch.cuda.is_available()` is true.
- A tiny tensor can be allocated on `cuda:0`.
- Triton imports and, when kernel behavior matters, a tiny Triton wrapper smoke
  runs.

CPU-only validation is useful for signatures, config math, and packing helpers,
but it cannot verify the advertised offloaded Mixtral inference path.

## Model artifacts

The demo downloads or expects two families of artifacts:

- Base tokenizer/model config from the Mixtral Instruct model name.
- A quantized state directory with `model.safetensors.index.json` and safetensors
  shards compatible with this repo's HQQ/offloading state-dict layout.

Do not start downloads in an automated workflow unless the user has approved
network access, disk use, and runtime cost. Validate any already-local state
path before model construction.

## No CLI

The repository README states that no command-line script is available. Future
agents should build scripts from the distilled workflow and bundled helpers
rather than expecting an installed console command.
