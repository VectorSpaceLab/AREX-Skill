---
name: ffcv
description: "Use FFCV to convert datasets into .beton files, build fast PyTorch
  loader pipelines, handle image and custom fields/transforms, and tune cache,
  traversal, and throughput behavior."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# FFCV operating router

Use this skill when a task names **FFCV**, `.beton`, `DatasetWriter`, `Loader`,
`OrderOption`, FFCV fields/decoders/transforms, or an FFCV cache/throughput
problem. FFCV is a compiled, PyTorch-oriented data storage and loading system;
it replaces the data input path, not the model or optimizer.

## Choose a route

- **Convert or inspect a dataset** — read
  [dataset-writing](sub-skills/dataset-writing/SKILL.md). It covers indexable
  datasets, local WebDataset shards, field schemas, custom fields, `.beton`
  read-back, and writer resource controls.
- **Build or debug a loader/pipeline** — read
  [loader-pipelines](sub-skills/loader-pipelines/SKILL.md). It covers decoder
  selection, operation order, images, CPU/GPU boundaries, custom operations,
  subsets, partial batches, and training integration.
- **Diagnose speed, memory, or distributed behavior** — read
  [performance-tuning](sub-skills/performance-tuning/SKILL.md). It covers OS
  versus process cache, sequential/random/quasi-random traversal, concurrency,
  compilation, measurement, and distributed constraints.

For a task spanning routes, write the dataset first, validate it structurally,
then construct the loader, then tune one resource variable at a time. Do not
start with benchmark numbers or a full training run when a tiny `.beton` fixture
can expose the same correctness issue.

## Minimal operating contract

1. Install FFCV with a compatible PyTorch, NumPy/Numba, OpenCV, and TurboJPEG
   runtime. The package includes a native extension; verify both `import ffcv`
   and `import ffcv._libffcv`. Read [installation](references/installation.md)
   before diagnosing compiled-install failures.
2. A writer mapping's insertion order is the sample tuple order. Declare short,
   unique ASCII field names and adapt mapping-shaped samples to an explicit
   tuple before multiprocessing.
3. A loader pipeline starts with the field decoder. Keep native NumPy/JIT
   transforms before `ToTensor`; put `ToDevice` before GPU work and
   `ToTorchImage` where the model needs BCHW layout.
4. Make shape, dtype, device, field names, order, seed, cache mode, batch size,
   and `drop_last` explicit. Validate a complete batch and a one-row tail when
   partial batches are allowed.
5. Treat CUDA as additive runtime coverage unless the downstream task truly
   requires it. A CPU import or smoke test does not prove GPU transfer,
   normalization, or multi-GPU correctness.

Use [api-reference](references/api-reference.md) for verified signatures and
object relationships, and [troubleshooting](references/troubleshooting.md) for
cross-cutting install, schema, pipeline, cache, and device failures. The small
helper [scripts/ffcv_smoke.py](scripts/ffcv_smoke.py) creates a temporary
integer `.beton` file and checks a sequential loader; pass `--cuda` only on a
reserved compatible GPU.

## Scope boundary

This graph is self-contained operating knowledge for package users. It does not
require the original checkout, source examples, downloaded datasets, benchmark-
scale matrices, ImageNet/CIFAR training, release automation, Docker files, or
binary documentation assets. Those are evidence behind the distilled guidance,
not runtime dependencies.
