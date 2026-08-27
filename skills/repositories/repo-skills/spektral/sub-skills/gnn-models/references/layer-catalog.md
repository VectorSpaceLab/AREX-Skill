# Layer Catalog and Mode Support

This catalog helps match Spektral layers to loader outputs and graph data modes. Mode support is taken from layer docstrings and tests in the inspected Spektral 1.3.1 source.

## Convolution and message-passing layers

| Layer | Modes | Edge features | Notes |
| --- | --- | --- | --- |
| `AGNNConv` | single, disjoint, mixed | no | Attention-based graph neural network layer |
| `APPNPConv` | single, disjoint, mixed, batch | no | Personalized propagation with MLP options |
| `ARMAConv` | single, disjoint, mixed, batch | no | ARMA graph convolution |
| `CensNetConv` | single, disjoint, batch | yes | Updates node and edge channels |
| `ChebConv` | single, disjoint, mixed, batch | no | Chebyshev convolution; use Chebyshev preprocessing when needed |
| `CrystalConv` | single, disjoint, mixed | yes | Crystal graph convolution |
| `DiffusionConv` | single, disjoint, mixed, batch | no | Diffusion convolution with `K` steps |
| `ECCConv` | single, disjoint, batch, mixed | yes | Edge-conditioned convolution with optional kernel network |
| `EdgeConv` | single, disjoint, mixed | no | Dynamic edge-style convolution |
| `GATConv` | single, disjoint, mixed, batch | no | Graph attention; optional attention coefficients |
| `GatedGraphConv` | single, disjoint, mixed | no | Gated graph sequence model layer |
| `GCNConv` | single, disjoint, mixed, batch | no | Expects GCN-normalized adjacency; `preprocess(a)` calls `gcn_filter` |
| `GCSConv` | single, disjoint, mixed, batch | no | GraphConv with trainable skip connection |
| `GeneralConv` | single, disjoint, mixed | no | General-purpose design-space layer with normalization/dropout/aggregation |
| `GINConv` | single, disjoint, mixed | no | Graph Isomorphism Network layer |
| `GINConvBatch` | batch | no | Batch-mode GIN variant |
| `GraphSageConv` | single, disjoint, mixed | no | GraphSAGE layer with configurable aggregation |
| `GTVConv` | single, disjoint, batch | no | Graph total variation convolution |
| `MessagePassing` | single, disjoint | optional `e` | Base class; requires sparse adjacency |
| `TAGConv` | single, disjoint, mixed | no | Topology-adaptive graph convolution |
| `XENetConv` | single, disjoint, mixed | yes | Node/edge update with optional attention |
| `XENetConvBatch` | batch | yes | Batch-mode XENet variant |

## Pooling and readout layers

| Layer | Modes | Purpose |
| --- | --- | --- |
| `GlobalSumPool` | single, disjoint, mixed, batch | Sum node features into graph embeddings |
| `GlobalAvgPool` | single, disjoint, mixed, batch | Average node features |
| `GlobalMaxPool` | single, disjoint, mixed, batch | Max-pool node features |
| `GlobalAttentionPool` | single, disjoint, mixed, batch | Learn gated attention readout |
| `GlobalAttnSumPool` | single, disjoint, mixed, batch | Learn node attention weights for sum pooling; validate single mode on the target Keras version because rank-1 softmax behavior can fail |
| `SortPool` | single, disjoint, batch | Sort nodes by last channel and keep top `k` |
| `DiffPool` | single, batch | Dense differentiable pooling |
| `MinCutPool` | single, batch | Dense min-cut pooling |
| `DMoNPool` | single, batch | Modularity-based dense pooling |
| `AsymCheegerCutPool` | single, batch | Asymmetric Cheeger cut pooling |
| `JustBalancePool` | single, batch | Balanced dense pooling |
| `LaPool` | disjoint | Laplacian pooling |
| `SAGPool` | single, disjoint | Self-attention graph pooling |
| `TopKPool` | single, disjoint | Top-k node selection pooling |
| `SRCPool` | internal/general | Base for select-reduce-connect pooling |

## Base and utility layers

| Layer | Modes | Purpose |
| --- | --- | --- |
| `GraphMasking` | batch workflows | Removes the last feature from `x` as a mask and starts mask propagation |
| `Disjoint2Batch` | disjoint | Converts disjoint sparse graph tensors to dense batch tensors |
| `InnerProduct` | single | Pairwise inner product adjacency-like tensor |
| `MinkowskiProduct` | single | Hyperbolic inner product |
| `SparseDropout` | sparse tensors | Dropout for TensorFlow `SparseTensor` values |

## Practical matching rules

- `MessagePassing` and subclasses based on it need a rank-2 TensorFlow `SparseTensor` adjacency. Use `SingleLoader` or `DisjointLoader` rather than `BatchLoader`.
- Dense pooling layers usually need batch-compatible dense tensors. Use `BatchLoader(mask=True)` and put `GraphMasking` at the model input when padded nodes must be masked.
- Layers that support mixed mode work with shared adjacency and batched node features from `MixedLoader`.
- If a layer exposes `preprocess(a)`, use `LayerPreprocess(layer_class)` on the dataset or call the static method on every adjacency before loading.
- Edge-feature layers require the loader/model call to include `e`; validate loader output before building the model.
