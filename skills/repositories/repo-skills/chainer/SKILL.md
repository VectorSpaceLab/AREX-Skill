---
name: chainer
description: "Routes Chainer workflows for training, export, distributed
  learning, ChainerX, and checkout maintenance."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# Chainer

Chainer is a maintenance-phase deep learning framework.
Use this skill when a task mentions Chainer, ChainerMN, ChainerX, onnx_chainer, or the core `chainer` training APIs.

## Start here

- Read `references/install.md` when you need base install or optional-backend guidance.
- Read `references/workflows.md` for the high-level route map.
- Read `references/api-overview.md` when you need exact signatures or verified runtime facts.
- Read `references/troubleshooting.md` when import, backend, or build issues appear.
- Read `references/repo-provenance.md` when you need source freshness or version context.
- Run `scripts/runtime_probe.py` for a quick local health check.

## Route map

### `sub-skills/training/`
Use for define-by-run model building, datasets, iterators, trainers, serializers, GPU or CPU setup, static-graph usage, and single-node example workflows such as MNIST, CIFAR, PTB, or serialization.

### `sub-skills/export/`
Use for ONNX-Chainer export, `export_testcase`, and Caffe export or conversion troubleshooting.

### `sub-skills/distributed/`
Use for ChainerMN, MPI or mpi4py, communicator selection, data-parallel or model-parallel training, dataset scattering, multi-node evaluators, and multi-process debugging.

### `sub-skills/chainerx/`
Use for ChainerX build or install questions, backend and device selection, `native` or `cuda` device parsing, ChainerX limitations, and fallback behavior.

## Quick install and import check

```bash
pip install chainer
python - <<'PY'
import chainer
print(chainer.__version__)
PY
```

## Common surfaces

- `chainer.backends.cuda.available` and `chainer.backends.cuda.cudnn_enabled`
- `chainer.backends.intel64.is_ideep_available()`
- `chainerx.is_available()`
- `onnx_chainer.export(...)`
- `chainermn.create_communicator(...)`
- `chainer.print_runtime_info()`

## Shared smoke scripts

- `scripts/runtime_probe.py`
- `scripts/training_smoke.py`
- `scripts/serialization_smoke.py`
- `scripts/export_smoke.py`
- `scripts/chainerx_probe.py`
- `scripts/chainermn_probe.py`
