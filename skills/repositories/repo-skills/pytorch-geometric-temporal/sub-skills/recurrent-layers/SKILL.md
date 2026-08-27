---
name: recurrent-layers
description: "Guide PyTorch Geometric Temporal recurrent graph layer selection,
  shape/state contracts, and tiny forecasting smoke tests."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# recurrent-layers

Use this sub-skill when the user is building, debugging, or smoke-testing a PyTorch Geometric Temporal model whose core temporal operator is a recurrent graph layer.

## Trigger phrases

Load this sub-skill for requests such as:

- "use GConvGRU/GConvLSTM/GCLSTM/DCRNN/TGCN/A3TGCN for forecasting"
- "what shape should `H`, `C`, `lambda_max`, `periods`, or batch tensors have?"
- "add a `torch.nn.Linear` head after a recurrent temporal layer"
- "preserve hidden state across temporal snapshots" or "reset recurrent state between graph sequences"
- "make a tiny CPU smoke test for recurrent temporal graph layers"
- "convert a recurrent example into a no-download synthetic training loop"

## Covered layer families

This sub-skill covers the recurrent exports in `torch_geometric_temporal.nn.recurrent`:

- Chebyshev recurrent cells: `GConvGRU`, `GConvLSTM`, `GCLSTM`.
- Diffusion recurrent cells: `DCRNN`, `BatchedDCRNN`.
- Temporal GCN cells: `TGCN`, `TGCN2`, `A3TGCN`, `A3TGCN2`.
- Relational/evolution/embedding recurrent cells: `LRGCN`, `DyGrEncoder`, `EvolveGCNH`, `EvolveGCNO`, `MPNNLSTM`, `AGCRN`.

The recurrent layers return hidden representations and states. They do not include the final forecasting/classification nonlinearity, loss, metric, optimizer, or task head unless explicitly stated by that layer. Add `torch.nn.functional.relu`, dropout, and `torch.nn.Linear` heads in the surrounding model when the task needs them.

## Boundaries and routing

Stay in this sub-skill for recurrent temporal graph layer selection, forward-call signatures, state management, shape debugging, and the bundled synthetic smoke script.

Route elsewhere when the user's main question is about:

- Attention-only or heterogeneous graph attention layers such as `STConv`, `ASTGCN`, `MSTGCN`, `GMAN`, `MTGNN`, `AAGCN`, `DNNTSP`, or `HeteroGCLSTM`: use `attention-and-hetero-layers`.
- Choosing and configuring real benchmark dataset loaders: use `dataset-loaders`.
- Constructing temporal signal iterators and `temporal_signal_split`: use `temporal-signals`.
- `IndexDataset`, `get_index_dataset`, index-batching tuple unpacking, or Dask-DDP: use `index-batching`.

## First steps for model-building

1. Identify the snapshot shape: ordinary snapshots use node features `X` shaped `[num_nodes, in_channels]`; batched recurrent variants use batch-aware shapes such as `[batch_size, num_nodes, in_channels]` or `[batch_size, sequence_length, num_nodes, in_channels]`.
2. Pick the layer whose state contract matches the data layout. Read [API reference](references/api-reference.md) before writing forward calls.
3. Add a task head outside the recurrent layer. A common forecasting head is `hidden = F.relu(hidden); prediction = torch.nn.Linear(hidden_dim, target_dim)(hidden)`.
4. Decide whether each independent temporal sequence resets `H`/`C` to `None`, or whether the returned state is passed into the next snapshot. Read [workflow recipes](references/workflows.md) for both patterns.
5. Run the bundled [synthetic recurrent smoke script](scripts/recurrent_forecasting_smoke.py) before adapting long examples or network-backed datasets.

## Quick checks

- `edge_index` is always a long tensor shaped `[2, num_edges]`.
- `edge_weight` is a float tensor shaped `[num_edges]` when provided. Some diffusion/batched helpers need explicit weights; use ones for an unweighted synthetic graph.
- Chebyshev layers with non-symmetric normalization (`normalization=None` or `"rw"`) require `lambda_max` in `forward`.
- `A3TGCN` expects `X` shaped `[num_nodes, in_channels, periods]`; `A3TGCN2` expects `[batch_size, num_nodes, in_channels, periods]`.
- `AGCRN` uses node embeddings `E` shaped `[num_nodes, embedding_dimensions]` instead of `edge_index`.

## Runtime references

- [API reference](references/api-reference.md): constructor and forward signatures, shape contracts, state returns, and layer-specific cautions.
- [Workflow recipes](references/workflows.md): snapshot loops, explicit heads and losses, hidden-state reset/preserve choices, batched `TGCN2`/`A3TGCN2` patterns, and optional Lightning caveats.
- [Troubleshooting](references/troubleshooting.md): shape mismatches, missing weights, Chebyshev `lambda_max`, `batch_size`/`periods` mistakes, state leaks, and network-heavy example caveats.
- [Synthetic smoke script](scripts/recurrent_forecasting_smoke.py): deterministic CPU-only recurrent layer smoke with `--help` and `--layer` choices.
