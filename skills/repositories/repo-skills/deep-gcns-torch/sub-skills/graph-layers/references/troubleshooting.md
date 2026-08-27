# Troubleshooting graph layers

## Compiled PyG dependencies and ABI

The sparse KNN path and scatter-based message passing require a coherent
PyTorch Geometric stack. Verify the versions/build tags of `torch`,
`torch-geometric`, `torch-scatter`, and `torch-cluster` in the same environment;
then run a tiny CPU `knn_graph` and scatter operation. A package import alone
is insufficient because an extension can import while an operator fails at
runtime.

The inspected environment had PyTorch 2.11.0+cu128, PyG 2.8.0.post1,
`torch-scatter` 2.1.2+pt211cu128, and `torch-cluster` 1.6.3+pt211cu128, with
`pip check` passing. Match extension wheels to the installed PyTorch and CUDA
(or CPU) build rather than copying these tags blindly. If an extension reports
an undefined symbol, incompatible device code, or missing operator, repair the
environment first. Do not work around it by changing tensor shapes or by
silently falling back to a different graph construction path.

A historical PyG 1.6.3 probe failed against torch 1.13.1 due to the removed
`torch._six.container_abcs` import. Exact repository-era benchmark recreation
needs a coherent old environment; current API smoke results do not prove old
benchmark numbers.

## `sage` / `rsage` incompatibility

The repository wrapper's `SAGEConv` implementation uses an older internal
`SAGEConv` contract: its custom message path expects a `weight` member and its
propagation signature conflicts with modern PyG inspector type expectations.
On the inspected modern PyG, `GraphConv(..., conv='sage')` and `conv='rsage'`
fail rather than producing a validated output. This is a known source/API
incompatibility, not a user input mistake.

When modern PyG is required, select a validated sparse convolution (`edge`,
`mr`, `gcn`, `gin`, or `gat`) and preserve the same `(N,C)` / `(2,E)` contract.
Do not claim SAGE compatibility merely because the constructor is present. If
an exact historical SAGE result is mandatory, isolate the historical package
set and verify the old route there; do not mix old source assumptions with
modern PyG.

## KNN, dilation, and edge-index errors

- `k*dilation > points_per_graph` causes top-k or KNN failures. Reduce `k` or
  `dilation`, or use a larger synthetic fixture.
- Sparse dynamic KNN needs `batch` for multiple independent graphs. A missing
  batch can connect graphs conceptually or route into a backend's single-graph
  behavior. For one graph, `batch=None` is acceptable for the inspected path.
- Dense matrix KNN expects `(B,C,N,1)`, not `(B,N,C)` or `(B,C,N)`. It returns
  `(2,B,N,K)`; sparse `(2,E)` indices are not interchangeable.
- Dense compiled KNN is called per batch element and requires a compatible
  `torch-cluster`; use `knn='matrix'` to diagnose layout independently of the
  extension.
- `edge_index` must be integer and within the node range. A sparse edge index
  uses global node ids across a batched graph; a dense index uses local ids per
  batch element.
- A supplied edge index bypasses dynamic KNN. Use it to separate convolution
  failures from graph-construction failures.

## Feature and aggregation errors

- `GraphConv`/`GENConv` width mismatches usually mean `in_channels` was set to
  point count or the previous dense block's concatenated width was ignored.
  Print/assert feature shapes at every block boundary.
- Residual blocks require equal input/body widths. Dense blocks increase width
  by `out_channels`; update the next constructor accordingly.
- `GENConv(encode_edge=False)` adds edge attributes directly, so edge features
  must have width `in_dim`. For a linear encoder, set `edge_feat_dim`; for
  categorical OGB bond fields, use the matching encoder and feature columns.
- Avoid `p=0` for power aggregation. Begin with fixed `t`, `p`, and `y`, then
  enable learnable controls one at a time and check finite gradients.
- Power aggregation clamps message and output magnitudes in the inspected
  implementation. This is a stability behavior, not a guarantee that extreme
  inputs preserve their original scale.
- `MsgNorm` normalizes along feature dimension 1 and rescales by the input
  norm. It is intended for node feature matrices; do not pass a dense 4-D
  tensor without adapting the layout.

## Reversible failures

- Assert feature width and every channel-aligned extra argument are divisible
  by `group`. `edge_index` is shared and must not be chunked.
- `GroupAdditiveCoupling` chunks every extra positional argument after
  `edge_index` along the feature split dimension. Passing a scalar, an
  `(E, F)` edge tensor with a width unrelated to the node groups, or a graph
  structure in that position violates the wrapper contract.
- Forward/inverse mismatch usually indicates non-deterministic Fm behavior,
  unequal group widths, a wrong Fm input/output width, or incorrect ordering of
  extra arguments. Test with `disable=True` and a deterministic Fm first.
- Checkpointed backward may only be used for the configured
  `num_bwd_passes`. Use ordinary `.backward()` and keep `num_bwd_passes=1`
  unless the training workflow proves a need for more.
- Random dropout must be shared/replayed during reconstruction. Prefer an
  externally created mask or enable RNG preservation when appropriate.

## Scope and safe limits

Do not debug a layer error by launching a dataset download, full training,
large reversible depth, distributed run, or GUI visualization. The bundled
smoke is CPU-sized and self-contained. Dataset/config/checkpoint issues route
to the owning sibling skill; optional DGL and VTK are not required for this
layer skill.
