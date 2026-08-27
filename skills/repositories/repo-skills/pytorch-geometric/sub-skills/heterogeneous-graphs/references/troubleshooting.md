# Heterogeneous Graph Troubleshooting

Use this guide when PyG heterogeneous graph code fails at data construction, sampling, `to_hetero` conversion, `HeteroConv`, or link prediction.

## Missing Node Stores or Features

Symptoms:

- `KeyError` for a node type.
- Edge validation fails because source or destination node type is absent.
- `num_nodes` cannot be inferred.
- A model receives no feature tensor for a node type.

Fixes:

- Create every node store before adding edges that reference it: `data['paper'].x = ...` or `data['paper'].num_nodes = ...`.
- For featureless node types, set `num_nodes` explicitly and add an embedding table in the model, or create synthetic features appropriate for the task.
- Check edge index ranges against the correct source and destination node counts, not the total node count.
- Run `python scripts/hetero_metadata_check.py` for a small template of store and edge validation.

## Incorrect Edge Type Triplets

Symptoms:

- Metadata contains unexpected relation keys.
- `HeteroConv` does not execute a relation you expected.
- `LinkNeighborLoader` or `RandomLinkSplit` cannot find the edge type.

Fixes:

- Use exact 3-tuples: `('author', 'writes', 'paper')`, not `'author__writes__paper'` in runtime code.
- Keep relation names consistent across data construction, transforms, loaders, model dictionaries, and loss code.
- Print `data.edge_types` before building loaders or transforms.
- Verify `edge_index[0]` indexes the source type and `edge_index[1]` indexes the destination type.

## Absent Reverse Edges for Link Prediction

Symptoms:

- `RandomLinkSplit` with `rev_edge_types` fails or silently leaves message-passing leakage risk.
- Validation/test labels are split only on the forward edge store while reverse stores still expose held-out information.
- Link prediction model performs suspiciously well because reverse edges leak target links.

Fixes:

- Add reverse stores for message passing, for example `('movie', 'rev_rates', 'user')` for `('user', 'rates', 'movie')`.
- Pass both `edge_types=[forward_type]` and `rev_edge_types=[reverse_type]` to `RandomLinkSplit`.
- Ensure reverse `edge_index` is exactly the flipped forward connectivity when it is intended to mirror the forward relation.
- Use `python scripts/hetero_metadata_check.py --require-reverse --forward-relation rates --reverse-relation rev_rates` as a safe synthetic reminder of the expected structure.

## `to_hetero` Metadata Mismatch

Symptoms:

- Converted model omits a node type.
- Conversion warns about node types that do not receive messages.
- Runtime errors mention missing dictionary keys or invalid generated module names.
- A model converted with old metadata fails after data relations changed.

Fixes:

- Finalize `HeteroData` before calling `to_hetero(model, data.metadata(), aggr='sum')`.
- Recreate the converted model when node types or edge types change.
- Make sure the original homogeneous model accepts `(x, edge_index)` and uses PyG message-passing layers that can be cloned per relation.
- Prefer `SAGEConv((-1, -1), ...)` in the homogeneous model for bipartite heterogeneous graphs.
- Avoid node type and relation names that collide after sanitization; simple lowercase names such as `paper`, `author`, `writes`, and `rev_writes` are safest.
- If a target node type has no incoming relation, add reverse edges, add a self relation, or compute that type with a separate branch.

## Bipartite Size Inference Issues

Symptoms:

- Tensor shape mismatch in a bipartite relation.
- `GCNConv` fails on a relation with different source and target feature sizes.
- Attention layers add invalid self-loops on cross-type edges.

Fixes:

- Use bipartite-aware layers such as `SAGEConv((-1, -1), out_channels)`.
- When calling a convolution directly, pass a pair of feature tensors: `conv((x_src, x_dst), edge_index)`.
- In `HeteroConv`, pass `data.x_dict` and `data.edge_index_dict`; PyG supplies source/target feature pairs for bipartite relations.
- Disable self-loops for bipartite attention relations: `GATConv((-1, -1), hidden, add_self_loops=False)`.
- Use `GCNConv` mainly for same-type homogeneous relations unless you have confirmed its assumptions fit the relation.

## Heterogeneous Loader Failures

Symptoms:

- `NeighborLoader` or `LinkNeighborLoader` raises missing optional backend errors.
- Batch does not contain expected labels or node types.
- Loss indexing is off by sampled context nodes.

Fixes:

- Keep loader smoke tests tiny and full-batch where possible if optional sampling backends are unavailable.
- For node tasks, use `batch[target_type].batch_size` to slice seed nodes before computing loss.
- For link tasks, use `batch[edge_type].edge_label_index` and `batch[edge_type].edge_label` from the same edge store.
- Set hetero fanouts with a dictionary keyed by the actual `data.edge_types`.
- Inspect one sampled `batch.metadata()` and the relevant stores before running long training.

## Output Dictionary Does Not Contain Expected Type

Symptoms:

- `out['paper']` raises `KeyError` after `to_hetero` or `HeteroConv`.
- Only destination node types for relations appear in model output.

Fixes:

- Remember message passing updates destination node types. Add reverse relations when you need embeddings for original source types.
- Add per-type linear skip branches if a node type should be carried forward without incoming messages.
- Validate output keys in a one-step smoke test before writing the training loss.

## Quick Diagnostic Commands

```bash
python scripts/hetero_metadata_check.py
python scripts/hetero_metadata_check.py --require-reverse
python scripts/hetero_metadata_check.py --drop-reverse --expect-failure --require-reverse
```

The last command intentionally creates a graph without the reverse relation and succeeds only if the validator catches the missing reverse edge type.
