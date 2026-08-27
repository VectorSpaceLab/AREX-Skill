---
name: distributed
description: "Routes ChainerMN distributed training, MPI, communicator, and
  model-parallel workflows."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# Distributed

Use this sub-skill for ChainerMN workflows: multi-process data parallelism, MPI launch issues, communicator selection, distributed optimizers, dataset scattering, multi-node evaluators, and model-parallel links.

## Typical requests

- "How do I modify a Chainer trainer for ChainerMN?"
- "Which communicator should I use?"
- "Why does `create_communicator` fail?"
- "How do I scatter datasets across workers?"
- "How do I use `MultiNodeChainList` or model-parallel seq2seq?"
- "Why do MPI workers hang after an exception?"

## Read these first

- `references/workflows.md` for distributed training patterns.
- `references/api-reference.md` for communicators, optimizers, datasets, links, and extensions.
- `references/troubleshooting.md` for MPI, mpi4py, NCCL, and launch failures.

## Use this script

- `../../scripts/chainermn_probe.py` for a safe MPI / ChainerMN prerequisite check.

## Include here

- `chainermn.create_communicator(...)`
- `chainermn.create_multi_node_optimizer(...)`
- `chainermn.scatter_dataset(...)`
- `chainermn.create_multi_node_evaluator(...)`
- `chainermn.MultiNodeChainList`
- MPI, `mpi4py`, NCCL, CUDA-aware MPI, and CPU-only `naive` communicator guidance

## Route elsewhere

- Ordinary single-node training -> `../training/`
- ONNX or Caffe model export -> `../export/`
- ChainerX-specific device behavior -> `../chainerx/`

## Verification caveat

ChainerMN runtime verification requires MPI and usually `mpi4py`; GPU-scale workflows also require CuPy, NCCL, and CUDA-aware MPI.
If those dependencies are unavailable, treat distributed execution as environment-blocked rather than disproven.
