---
name: layers-and-networks
description: "Guides agents building MinkowskiEngine sparse layers, networks,
  convolution, pooling, broadcast, pruning, interpolation, union,
  KernelGenerator, and quick-start architectures."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Layers and networks

Use this operating sub-skill when the task is to assemble, debug, or adapt MinkowskiEngine sparse layers or network blocks: sparse convolutions and transposed convolutions, custom kernels, pooling and global heads, broadcast, normalization, nonlinearities, pruning, interpolation, union, sparse matrix multiplication, feature utilities, and `MinkowskiNetwork` subclasses.

## Route

- For callable signatures and return semantics, load [references/api-reference.md](references/api-reference.md).
- For end-to-end layer patterns, coordinate-output choices, quick-start network skeletons, and performance guidance, load [references/workflows.md](references/workflows.md).
- For dimension, channel, coordinate manager/key, device, CPU/GPU, kernel-map, and memory failures, load [references/troubleshooting.md](references/troubleshooting.md).
- To sanity-check an installed package without downloads, run `python scripts/layer_smoke.py --help` then `python scripts/layer_smoke.py --device cpu` from this sub-skill directory.

## Operating defaults

- Prefer `ME.utils.batched_coordinates(...)` or `ME.utils.sparse_collate(...)` when constructing inputs; do not guess the batch-coordinate column manually.
- Pass `dimension=D` consistently to every spatial layer and to each `MinkowskiNetwork` subclass.
- Reuse a tensor's `coordinate_manager` or `coordinate_map_key` deliberately whenever layers or feature utilities require identical coordinates.
- Treat the bundled script as CPU-first verification. Only use CUDA paths when the user's installed MinkowskiEngine build reports CUDA support and the user explicitly wants GPU execution.
