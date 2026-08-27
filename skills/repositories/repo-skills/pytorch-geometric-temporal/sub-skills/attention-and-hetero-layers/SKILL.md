---
name: attention-and-hetero-layers
description: "Guides PyTorch Geometric Temporal attention-based temporal graph
  layers and heterogeneous recurrent layers, with model selection, tensor
  layouts, and smoke checks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Attention and Heterogeneous Temporal Layers

Use this sub-skill when a task involves PyTorch Geometric Temporal attention/STGCN-style layers, MTGNN/GMAN/AAGCN/DNNTSP models, or the heterogeneous `HeteroGCLSTM` layer. Keep this file as a router; read the bundled references for signatures, layouts, and complete wiring patterns.

## Read this when

- The user names `TemporalConv`, `STConv`, `ASTGCN`, `MSTGCN`, `GMAN`, `MTGNN`, `AAGCN`, `DNNTSP`, `ChebConvAttention`, `MixProp`, `GraphConstructor`, `GraphAAGCN`, `SpatioTemporalEmbedding`, `SpatioTemporalAttention`, or `HeteroGCLSTM`.
- The user is converting traffic tensors for STGCN/ASTGCN/MSTGCN/GMAN/MTGNN and needs the correct axis order.
- The user has heterogeneous PyG data (`x_dict`, `edge_index_dict`, `metadata`) and wants a recurrent hidden/cell-state update per node type.
- The user asks whether a class is a high-level forecasting/model block or a lower-level building block.

## Route elsewhere when

- The layer is recurrent-only (`GConvGRU`, `DCRNN`, `TGCN`, `A3TGCN`, `AGCRN`, `MPNNLSTM`, etc.): route to `recurrent-layers`.
- The task is loading or downloading benchmark datasets: route to `dataset-loaders` first, then return here only after tensors are prepared.
- The task is constructing or splitting temporal signal iterators: route to `temporal-signals`.
- The task is memory-efficient index batching, Dask-DDP, or `get_index_dataset`: route to `index-batching`.
- The user wants a full notebook case study: distill the relevant pattern into one of the workflows here instead of copying or depending on notebooks.

## First decision: choose the model family

| User intent | Start with | Why |
| --- | --- | --- |
| STGCN block over `[batch, time, nodes, features]` traffic windows | `TemporalConv` or `STConv` | `STConv` combines two temporal convolutions with a Chebyshev graph convolution; `TemporalConv` is only the temporal gated-conv block. |
| Attention-based traffic forecasting with spatial and temporal attention | `ASTGCN` | High-level ASTGCN model; use `ChebConvAttention` only for custom blocks. |
| ASTGCN-like traffic forecasting without explicit attention modules | `MSTGCN` | High-level multi-component STGCN variant. |
| GMAN-style multi-attention traffic prediction | `GMAN` | High-level model that consumes spatial embeddings and integer-coded temporal embeddings. |
| Multivariate time-series graph learning with adaptive adjacency | `MTGNN` | High-level model; `MixProp` and `GraphConstructor` are helper blocks. |
| Skeleton/action style spatio-temporal graph convolution | `AAGCN` | High-level 2S-AGCN block; `GraphAAGCN` only builds its three-channel adjacency tensor. |
| Temporal set prediction | `DNNTSP` | High-level temporal-set model; expect item-batched node features. |
| Heterogeneous temporal recurrence | `HeteroGCLSTM` | Heterogeneous graph convolutional LSTM cell returning hidden/cell dictionaries. |

## Layout warning before coding

The most common failure is transposing the wrong axes. Confirm the target class before creating tensors:

- `TemporalConv` and `STConv`: input is `[B, T, N, F]` and output keeps `[B, T_out, N, F_out]`.
- `ASTGCN` and `MSTGCN`: input is `[B, N, F, T]`; output is `[B, N, num_for_predict]`.
- `GMAN`: `X` is `[B, num_his, N]`; `SE` is `[N, K*d]`; `TE` is `[B, num_his + num_pred, 2]` with day-of-week and time-of-day integer codes.
- `MTGNN` and helpers: input is channel-first `[B, in_dim, N, seq_length]`.
- `AAGCN`: input is `[B, F, T, N]`.
- `HeteroGCLSTM`: use PyG-style dictionaries (`x_dict`, `edge_index_dict`) plus `metadata=(node_types, edge_types)`.

## Bundled references and script

- Read [references/api-reference.md](references/api-reference.md) for constructor/forward signatures, output shapes, and high-level-versus-helper labels.
- Read [references/workflows.md](references/workflows.md) for model-selection recipes, minimal code skeletons, and routing to sibling data/recurrent sub-skills.
- Read [references/troubleshooting.md](references/troubleshooting.md) when shapes, Laplacian normalization, PyG optional operations, hetero metadata, or expensive models fail.
- Run or adapt [scripts/attention_hetero_smoke.py](scripts/attention_hetero_smoke.py) for a tiny CPU smoke check of `TemporalConv`, `STConv`, and `HeteroGCLSTM` with no downloads.

## Minimal operating pattern

1. Pick the owning model family from the table above.
2. Convert tensors to that class's required layout before constructing the model.
3. Keep dataset loading, temporal-signal iteration, and index-batching mechanics outside this sub-skill.
4. Add a small assertion on output shape before training; for quick environment checks, run the bundled smoke script.
5. If a model is large (`ASTGCN`, `MSTGCN`, `GMAN`, `MTGNN`, `DNNTSP`), start with tiny synthetic dimensions and mark any full training or traffic benchmark run as optional/expensive.
