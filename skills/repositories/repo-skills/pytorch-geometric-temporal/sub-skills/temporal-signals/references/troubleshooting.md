# Troubleshooting

Use the symptom -> cause -> fix table below when a temporal iterator behaves unexpectedly.

| Observable symptom | Likely cause | Fix |
| --- | --- | --- |
| `AssertionError: Temporal dimension inconsistency.` during construction | One temporal sequence is longer or shorter than another, or an optional kwarg sequence has a different snapshot count. | Make every temporal list the same length before calling the constructor. Use the public snapshot count as the consistency check. |
| `edge_index` looks like `[E, 2]`, or downstream code complains that the first dimension is not `2` | Edges were stored as a list of pairs instead of the required `[2, E]` layout. | Transpose the array once, for example with `np.array(edges).T`, so rows are source and destination indices. |
| `edge_attr` or `edge_weight` length does not match the number of edges | Weights were built per node, or the edge-weight array was shaped along the wrong axis. | Make the first dimension of the weight array equal the number of edges. If you use 2-D weights, the first dimension still needs to be `E`. |
| Targets or optional arrays come out with the “wrong” dtype | The iterator converts integer arrays to `LongTensor` and float arrays to `FloatTensor`. | Cast intentionally before construction. Use integer targets for class labels and float targets for regression. |
| A homogeneous optional kwarg containing `None` crashes during access | Homogeneous `**kwargs` are converted with `.dtype`, so a `None` element is not a safe placeholder. | Either supply an array at every snapshot for that kwarg or omit the kwarg entirely. |
| A hetero snapshot is missing a node type, edge type, or optional field | A key was omitted from one snapshot, or the edge-index and edge-weight dictionaries do not use the same relation key. | Keep relation keys identical across edge dictionaries and keep node-type keys consistent whenever a downstream model expects them. Use `None` only when you intentionally want to skip a whole snapshot or a whole node/relation value. |
| Downstream PyG code complains about batch size, index bounds, or shape mismatch | The batch vector does not match the number of nodes in the snapshot. | For homogeneous batch iterators, concatenate one batch id per node. For hetero batch iterators, provide one batch vector per node type with the matching length. |
| `temporal_signal_split` returns an empty train or test iterator | The ratio was truncated with `int(...)` to `0` or to the full snapshot count. | Choose a ratio and snapshot count that leave both partitions non-empty, or slice manually after checking the counts. |
| Code expects `Data.batch`, but a hetero snapshot appears to have no batch | `Data`, `Batch`, `HeteroData`, and hetero batch snapshots have different batch semantics. | Use `snapshot.batch` only for homogeneous batch snapshots. For hetero batch snapshots, read `snapshot[node_type].batch` or the per-type store. For plain hetero snapshots, there is no batch vector unless you add one yourself. |

## Quick diagnosis patterns

- If the failure happens at construction time, check list lengths first.
- If the failure happens at `snapshot[0]`, check tensor shapes and dtype conversion.
- If the failure happens only after splitting, check `train_ratio` and `snapshot_count`.
- If the failure happens only for hetero data, inspect each node-type key and each relation key independently.

## Safe fixes to try first

1. Print or assert each list length before construction.
2. Print one snapshot and verify `edge_index.shape`, `edge_attr.shape`, `x.shape`, `y.shape`, and `batch.shape`.
3. For hetero data, verify `snapshot[node_type].x`, `snapshot[node_type].y`, and `snapshot[relation].edge_index` separately.
4. When in doubt, reduce to a 2- or 3-snapshot synthetic example and rebuild the iterator from scratch.
