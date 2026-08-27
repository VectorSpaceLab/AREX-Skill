---
name: graph-layers
description: "Construct and troubleshoot the repository's sparse and dense graph
  layers, dynamic or dilated KNN blocks, GENConv aggregation, and reversible
  coupling primitives; use this skill for layer-level API and shape questions,
  not end-to-end dataset workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Graph layers

Use this skill for a layer-level design or debugging task. It is a distilled
operating guide, not a source-checkout import recipe. Start with the tensor
layout and graph representation, choose a static or dynamic layer, then run the
small bundled smoke before moving to a real workload.

## Route by task

- For ModelNet40, S3DIS, PartNet, point-cloud data loading, task flags,
  checkpoints, or visualization, hand off to the sibling
  [point-cloud-workflows](../point-cloud-workflows/SKILL.md) skill.
- For OGB datasets, DeeperGCN benchmark configurations, graph pooling,
  partitioning, or RevGNN/RevGAT experiments, hand off to
  [ogb-workflows](../ogb-workflows/SKILL.md).
- For PPI data, F1 metrics, and PPI training/evaluation, hand off to
  [ppi-workflows](../ppi-workflows/SKILL.md).
- Keep the root skill responsible for installation and broad routing. This
  skill can identify dependency failures but does not install packages or run
  long training.

## Quick decision procedure

1. **Identify layout.** Use sparse node features `(N, C)` with a PyG
   `edge_index` `(2, E)` and optional `batch` `(N,)` for independent graphs;
   use dense point-cloud features `(B, C, N, 1)` with dense indices
   `(2, B, N, K)`. Do not pass a dense tensor to sparse layers or flatten a
   dense batch without preserving graph membership.
2. **Choose graph construction.** Use a supplied `edge_index` when topology is
   fixed. Otherwise use `DynConv`/`DynConv2d`, selecting `kernel_size K`,
   `dilation d`, and (for dense layers) `knn='matrix'` or the compiled
   `torch_cluster` path. Ensure `K*d` does not exceed points per graph.
3. **Choose convolution.** Sparse `GraphConv` supports `edge`, `mr`, `gat`,
   `gcn`, and `gin` in the inspected implementation. `sage` and `rsage` are
   exposed but are not a supported modern-PyG route; see
   [troubleshooting](references/troubleshooting.md). Dense `GraphConv2d` and
   `DynConv2d` support `edge` and `mr`.
4. **Choose composition.** Plain blocks transform features, residual blocks
   add a same-width scaled skip, and dense blocks concatenate newly produced
   channels. Static blocks preserve and return `edge_index`; sparse dynamic
   blocks return `(features, batch)`.
5. **For generalized aggregation**, configure `GENConv` and validate the
   aggregator, temperature/power parameters, edge encoding, and message
   normalization together. See [aggregation and blocks](references/aggregation-and-blocks.md).
6. **For memory-efficient depth**, use a channel-divisible group additive
   coupling with deterministic per-group functions, then wrap it with the
   reversible wrapper only after a direct forward/inverse round trip passes.
   See [reversible](references/reversible.md).
7. Run the safe helper from any working directory:

   ```bash
   python /absolute/path/to/graph-layers/scripts/layer_smoke.py --help
   python /absolute/path/to/graph-layers/scripts/layer_smoke.py --tiny
   ```

   Resolve the absolute path in the caller's skill installation; never add a
   source checkout to `PYTHONPATH` for this helper.

## Dependency boundary

The core layer behavior depends on a coherent PyTorch, PyTorch Geometric,
`torch-scatter`, and `torch-cluster` installation. The verified inspection
combination was PyTorch 2.11.0+cu128, PyG 2.8.0.post1,
`torch-scatter` 2.1.2+pt211cu128, and `torch-cluster` 1.6.3+pt211cu128, with
`pip check` passing. Treat those versions as evidence, not as a universal pin:
match PyG extension wheels to the installed PyTorch and CUDA/CPU build. A
missing or ABI-incoherent compiled extension is a dependency failure, not a
layer-shape bug. The tiny helper probes these dependencies without importing
repository modules.

Exact benchmark reproduction is intentionally outside this skill. The
repository-era PyG 1.6.3 probe did not import with torch 1.13.1 because of the
removed `torch._six.container_abcs`; use a coherent historical environment for
old-number reproduction and do not infer benchmark equivalence from the modern
smoke.

## References

- [API and shape reference](references/api-reference.md)
- [Aggregation and block choices](references/aggregation-and-blocks.md)
- [Reversible coupling and wrapper contracts](references/reversible.md)
- [Troubleshooting](references/troubleshooting.md)
