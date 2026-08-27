# Troubleshooting Layers and Extensions

## Optional Extension Imports

Symptoms:

- `ModuleNotFoundError: No module named 'torch_scatter'`
- `ModuleNotFoundError: No module named 'torch_cluster'`
- Import errors mentioning incompatible CUDA, PyTorch, or undefined symbols.

Fixes:

- Install `torch`, `torch-scatter`, and `torch-cluster` wheels that match the local PyTorch and CUDA build.
- On CPU-only machines, use CPU wheels and avoid assuming CUDA kernels are present.
- Reinstall extension wheels after changing PyTorch, CUDA, Python, or the operating system.
- Use `python scripts/inspect_layers.py --optional` to report optional import status without downloading anything.

## Build and Platform Failures

Symptoms:

- C++/CUDA build failures while installing PyG-style dependencies.
- `ninja`, compiler, Visual Studio Build Tools, or CUDA toolkit errors.
- Apple Silicon failures around GPU acceleration.

Fixes:

- Prefer prebuilt wheels over source builds when possible.
- Keep Python within TorchDrug's supported range for this release and match PyTorch to the extension wheels.
- Windows source builds may require Visual Studio C++ Build Tools.
- Apple Silicon should be treated as CPU-only for this TorchDrug release; do not plan around `mps` acceleration.

## Shape Mismatches in Graph Layers

Symptoms:

- Matrix multiply errors in `Linear` layers.
- `RuntimeError` from tensor addition between node and edge features.
- GAT errors about `output_dim` and `num_head`.

Fixes:

- Set model `input_dim` to `graph.node_feature.shape[-1]` or the actual input tensor width.
- Set `edge_input_dim` to `graph.edge_feature.shape[-1]`; leave it as `None` if there is no edge feature tensor.
- For `GraphAttentionConv` / `GAT`, ensure every hidden dimension passed to a GAT layer is divisible by `num_head`.
- With `concat_hidden=True`, update downstream task/head input dimensions to `model.output_dim`, not just the final hidden dimension.
- If a readout is `Set2Set`, account for doubled graph feature width.

## Relation and Edge Feature Mismatches

Symptoms:

- Assertion failure in `RelationalGraphConv` or `GeometricRelationalGraphConv`.
- Index errors involving `edge_list[:, 2]`.
- Wrong output shape after relation aggregation.

Fixes:

- Use relational layers only when `edge_list` contains a third relation-id column.
- Pass `num_relation=graph.num_relation` to `RGCN`, `GearNet`, `RelationalGraphConv`, and `GeometricRelationalGraphConv`.
- Ensure every relation id is in `[0, graph.num_relation - 1]`.
- Do not confuse categorical relation ids with dense `edge_feature`; relation ids live in `edge_list[:, 2]`, while `edge_input_dim` describes `graph.edge_feature` width.
- For GearNet-style protein geometry, keep `GraphConstruction(edge_feature="gearnet")`, `SpatialLineGraph(num_angle_bin=...)`, and model `num_angle_bin` consistent.

## Variadic Size Errors

Symptoms:

- `variadic_*` helpers return wrong grouping, wrong top-k results, or device errors.
- `size.sum()` does not match the first dimension of the packed input.
- Index tensors fail on GPU.

Fixes:

- Check `input.shape[0] == size.sum().item()` before calling `variadic_sum`, `variadic_mean`, `variadic_max`, `variadic_softmax`, or `variadic_cross_entropy`.
- Use graph-provided sizes such as `graph.num_nodes`, `graph.num_edges`, or `graph.num_residues` for packed batches.
- Keep `size`, indexes, masks, and input tensors on the same device.
- Use `long` dtype for indexes and targets.
- For scatter aggregations, always pass `dim_size=graph.num_node` or `dim_size=graph.batch_size` when isolated nodes or empty graphs are possible.

## Custom Message Passing Scatter Errors

Symptoms:

- `scatter_add` dimension errors in a custom PageRank-like layer.
- Missing rows for isolated nodes.
- CPU/GPU device mismatch from `torch.arange`.

Fixes:

- Use `node_in = graph.edge_list[:, 0]` for source nodes and `node_out = graph.edge_list[:, 1]` for target nodes.
- Aggregate with `scatter_add(message, node_out, dim=0, dim_size=graph.num_node)` or an equivalent scatter call.
- Create new indexes with `device=graph.device`.
- Unsqueeze degree tensors before dividing node-feature matrices, for example `graph.degree_in[node_in].unsqueeze(-1)`.
- Clamp or add epsilon for zero-degree divisions.

## CUDA Extension and JIT Issues

Symptoms:

- Errors from `torch.utils.cpp_extension`, `load`, `ninja`, or missing CUDA architecture flags.
- Extension recompiles every run or fails after moving environments.

Fixes:

- Keep compiled extension cache compatible with the exact Python, PyTorch, and CUDA versions in use.
- Clear stale Torch extension caches after upgrades.
- Prefer CPU checks for documentation/inspection tasks that do not require training.
- Avoid triggering downloads or heavyweight model imports just to inspect signatures; use the bundled inspection helper first.

## `setuptools` / `pkg_resources` Warnings

Symptoms:

- Deprecation warnings mentioning `pkg_resources` during import.
- Warnings from packaging libraries that do not stop execution.

Fixes:

- Treat warnings as non-fatal unless they accompany an actual import error.
- If warnings pollute test logs, filter them at the test runner or warning-control layer rather than changing TorchDrug layer code.
- Do not mask real extension import failures; inspect optional package status separately.
