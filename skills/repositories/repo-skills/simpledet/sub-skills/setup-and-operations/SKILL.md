---
name: setup-and-operations
description: "Guides SimpleDet's legacy MXNet environment setup, Cython
  extension builds, backend diagnostics, checkpoints, TensorBoard, and safe
  distributed-operation prerequisites."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Setup and operations

Use this route for install/import errors, MXNet or `mxnext` compatibility,
Cython/custom-operator builds, checkpoint/log layout, TensorBoard, or cluster
prerequisites. Read [installation.md](references/installation.md) before
installing and [troubleshooting.md](references/troubleshooting.md) after a
failure.

## Establish the runtime boundary

SimpleDet is a checkout-driven Python 3 project. Its documented baseline is
Python 3.7, NumPy 1.x, OpenCV, `pytz`, patched `pycocotools`, `mxnext`, and a
CUDA 10.1-compatible MXNet 1.6-era wheel or source build. The root diagnostic
reports missing modules, `nvcc`, compiled artifacts, and MXNet GPU count without
installing, downloading, or starting a workflow.

```bash
python <skill-root>/scripts/check_environment.py --repo-root /path/to/simpledet --json
```

A CPU import is only an inspection signal: train, bbox test, mask test, and
speed workflows request `mx.gpu` contexts.

## Install and extension sequence

Use a private environment, install the exact backend variant first, then
compatible `mxnext` and patched COCO APIs, followed by OpenCV/`pytz` and
optional TensorBoard. The repository's Makefile attempts CPU Cython modules and
CUDA `gpu_nms`; `make` therefore needs `nvcc`. If `nvcc` is unavailable, do not
call a CPU-only partial build a complete install.

Useful safe helper:

```bash
python <skill-root>/scripts/check_environment.py --repo-root /path/to/simpledet --strict
```

The source cluster/setup helpers are not bundled as executable runtime scripts:
they contain network downloads, private paths, SSH, Singularity, or process
termination side effects. Read [operations.md](references/operations.md) for
their safe prerequisites.

## Route onward

- Dataset/cache/schema work: [data-preparation](../data-preparation/SKILL.md).
- Train/test/config/checkpoint work: [detection-workflows](../detection-workflows/SKILL.md).
- New symbols/components: [model-customization](../model-customization/SKILL.md).
