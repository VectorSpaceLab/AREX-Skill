# Layer API and shape reference

This reference describes the inspected public constructor and call contracts.
Keep the feature width explicit in every design: `in_channels` and
`out_channels` are channel counts, not point counts.

## Sparse representation

- Node features are `(N, C)`.
- `edge_index` is a `torch.long` tensor `(2, E)`. Row 0 contains source
  neighbors and row 1 contains target/center nodes for the repository's
  message and relative-difference operations.
- `batch` is `(N,)`, assigning each node to an independent graph. Pass it only
  to a dynamic layer when the layer must build KNN edges; a supplied
  `edge_index` does not need `batch`.
- `edge_attr` for `GENConv` is `(E, F_e)` and must either already match the
  node width when `encode_edge=False`, or be encodable to `in_dim` when
  `encode_edge=True`.

### Sparse constructors

```text
GraphConv(in_channels, out_channels, conv='edge', act='relu',
          norm=None, bias=True, heads=8)
DynConv(in_channels, out_channels, kernel_size=9, dilation=1,
        conv='edge', act='relu', norm=None, bias=True, heads=8, **kwargs)
GENConv(in_dim, emb_dim, aggr='softmax', t=1.0, learn_t=False,
        p=1.0, learn_p=False, y=0.0, learn_y=False, msg_norm=False,
        learn_msg_scale=True, encode_edge=False, bond_encoder=False,
        edge_feat_dim=None, norm='batch', mlp_layers=2, eps=1e-7)
```

`GraphConv(x, edge_index)` returns `(N, out_channels)`. Its `conv` choices
are `edge`, `mr`, `gat`, `gcn`, `gin`, `sage`, and `rsage`; only the first
five are validated as working in the current modern-PyG inspection. For GAT,
the wrapper passes `out_channels // heads` to the underlying layer, so choose
an output width divisible by `heads` if the requested width matters.

`DynConv(x, batch=None, edge_index=None)` builds a dilated KNN graph only when
`edge_index` is omitted, then returns the same feature shape contract as
`GraphConv`. Supplying an edge index is the deterministic way to separate
layer testing from KNN testing.

`GENConv(x, edge_index, edge_attr=None)` first messages from source nodes,
optionally adds encoded edge features, aggregates, optionally applies
`MsgNorm`, adds the input (`x + m`), and applies an MLP. Its output width is
`emb_dim`; use `emb_dim == in_dim` for a same-width residual composition.

Sparse blocks have these contracts:

- `PlainDynBlock(channels, ...) -> (features, batch)`; no skip is added.
- `ResDynBlock(channels, ..., res_scale=1) -> (features, batch)`; the body
  output is added to `res_scale * x`, so widths must match.
- `DenseDynBlock(in_channels, out_channels=64, ...) -> (features, batch)`;
  it concatenates `x` and the body result along dimension 1, producing
  `in_channels + out_channels` channels.
- `ResGraphBlock(channels, ..., heads=8, res_scale=1) -> (features,
  edge_index)`; static residual, same-width requirement.
- `DenseGraphBlock(in_channels, out_channels, ..., heads=8) -> (features,
  edge_index)`; static concatenation along dimension 1.

The tuple return from sparse dynamic blocks is intentional: preserve `batch`
when chaining blocks. Do not treat it as a feature tensor.

## Dense point-cloud representation

Dense layers use `x` with shape `(B, C, N, 1)`. The last singleton dimension
is part of the contract. A dense KNN index has shape `(2, B, N, K)`:
`edge_index[0]` gathers neighbors and `edge_index[1]` gathers centers. The
index is local to each batch element, so do not use sparse global node ids.

```text
GraphConv2d(in_channels, out_channels, conv='edge', act='relu',
            norm=None, bias=True)
DynConv2d(in_channels, out_channels, kernel_size=9, dilation=1,
         conv='edge', act='relu', norm=None, bias=True,
         stochastic=False, epsilon=0.0, knn='matrix')
```

`GraphConv2d(x, edge_index)` returns `(B, out_channels, N, 1)` and supports
`edge` and `mr`. `DynConv2d(x, edge_index=None)` constructs indices when
needed. `knn='matrix'` uses a batched pairwise-distance/top-k path; the other
path calls compiled `torch_cluster` independently for each batch element.
Both paths are CPU-testable at tiny sizes but have different memory/performance
profiles.

Dense blocks return tensors rather than `(tensor, batch)`:

- `PlainDynBlock2d(in_channels, ...)` preserves width.
- `ResDynBlock2d(in_channels, ..., res_scale=1)` adds a same-width body.
- `DenseDynBlock2d(in_channels, out_channels=64, ...)` concatenates along the
  channel axis and returns `in_channels + out_channels` channels.

`BasicConv` is a 1x1 `Conv2d` stack used by dense edge/MR layers. Dense
normalization is batch or instance normalization; sparse MLP normalization
also accepts layer normalization.

## KNN and dilation contracts

Sparse `DilatedKnnGraph(k, dilation, stochastic=False, epsilon=0.0,
knn='matrix')` receives `(N, C)` plus `batch`, asks its selected KNN routine
for `k*dilation` candidates, then takes every `dilation`-th candidate. Dense
`DenseDilatedKnnGraph` receives `(B,C,N,1)` and returns `(2,B,N,k)` using the
batched matrix route. Dense `DilatedKnnGraph` uses the compiled KNN route.

`stochastic=True` can randomly choose `k` positions from the `k*dilation`
window during training with probability `epsilon`; otherwise deterministic
striding is used. Set `eval()` and fixed seeds for a reproducible smoke. Make
sure each graph has at least `k*dilation` points. Pairwise matrix KNN includes
the nearest entries produced by `topk` and can include self; do not assume
self-loop exclusion without checking the selected backend/path.

## Small feature helpers

The reusable data utilities include `extract_node_feature(data, reduce)` for
`mean`, `max`, or `add` scatter reduction, point transforms that preserve
leading point-cloud dimensions, and atom/bond categorical feature dimensions
used by `BondEncoder`. Dataset classes, downloads, and raw-file processing are
not layer-level runtime helpers and belong to the task-specific sibling
skills.
