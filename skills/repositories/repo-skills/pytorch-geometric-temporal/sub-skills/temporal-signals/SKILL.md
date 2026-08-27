---
name: temporal-signals
description: "Guides construction, slicing, splitting, iteration, batching, and
  debugging of PyTorch Geometric Temporal signal iterators."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Temporal Signals

Use this sub-skill when a task is about building or debugging PyTorch Geometric Temporal snapshot iterators from in-memory arrays, not about downloading datasets or training models.

Keep this file as the router. Read the bundled references for constructor signatures, shape contracts, recipes, and failure recovery.

## Trigger phrases

Load this sub-skill for requests such as:

- "create a `StaticGraphTemporalSignal`/`DynamicGraphTemporalSignal`/`DynamicGraphStaticSignal`"
- "iterate temporal graph snapshots" or "what does `dataset[0]` return?"
- "split a temporal signal into train and test snapshots"
- "slice a temporal iterator without shuffling"
- "add optional per-snapshot attributes with `**kwargs`"
- "use temporal batches with a `batch` vector or `batch_dict`"
- "construct heterogeneous author/paper temporal snapshots"
- "debug `Temporal dimension inconsistency.` or missing hetero keys"

## Covered APIs

This sub-skill covers:

- Homogeneous iterators: `StaticGraphTemporalSignal`, `DynamicGraphTemporalSignal`, `DynamicGraphStaticSignal`.
- Homogeneous batch iterators: `StaticGraphTemporalSignalBatch`, `DynamicGraphTemporalSignalBatch`, `DynamicGraphStaticSignalBatch`.
- Heterogeneous iterators: `StaticHeteroGraphTemporalSignal`, `DynamicHeteroGraphTemporalSignal`, `DynamicHeteroGraphStaticSignal`.
- Heterogeneous batch iterators: `StaticHeteroGraphTemporalSignalBatch`, `DynamicHeteroGraphTemporalSignalBatch`, `DynamicHeteroGraphStaticSignalBatch`.
- `temporal_signal_split`, integer snapshot access, slice access, iterator reset behavior, `snapshot_count`, and optional temporal attributes passed through `**kwargs`.

## Route elsewhere

- Real benchmark loader choice, downloads, cache directories, or `get_dataset` side effects: use `dataset-loaders`.
- `IndexDataset`, `get_index_dataset`, sequence-to-sequence index batches, `allGPU`, `world_size`, or Dask-DDP: use `index-batching`.
- Model forward calls, training loops, recurrent hidden state, or forecasting heads after snapshots are produced: use `recurrent-layers` or `attention-and-hetero-layers`.

## First workflow

1. **Classify graph and feature dynamics.** Static edges plus temporal features use `StaticGraphTemporalSignal`; temporal edges plus temporal features use `DynamicGraphTemporalSignal`; temporal edges plus one fixed feature matrix use `DynamicGraphStaticSignal`.
2. **Choose homogeneous vs heterogeneous.** Homogeneous snapshots use arrays and return PyG `Data` or `Batch`; heterogeneous snapshots use node/relation dictionaries and return `HeteroData` or a hetero `Batch`.
3. **Choose ordinary vs batch variant.** Use batch variants only when each temporal snapshot already contains multiple disjoint graphs encoded by a `batch` vector or `batch_dict`.
4. **Validate temporal lengths before construction.** Every temporal sequence must have the same snapshot count for its class. Prefer `iterator.snapshot_count` over `len(iterator)` because `__len__` is not implemented consistently across all iterator classes.
5. **Inspect one snapshot.** Check object type and shapes: `edge_index`, `edge_attr`, `x`, `y`, and optionally `batch` or per-type attributes.
6. **Split or slice only after validating shapes.** `temporal_signal_split` preserves chronological order and calls slice access; it does not shuffle, copy deeply, or validate the ratio for you.
7. **Hand off after snapshots.** Once the iterator yields correct snapshots, route model selection/training to a model sub-skill.

## Runtime references and helper

- [API reference](references/api-reference.md): signatures, temporal length contracts, snapshot object types, shapes, slicing, and split behavior.
- [Workflow recipes](references/workflows.md): self-contained static, dynamic, dynamic-static, heterogeneous, batched, slicing, and train/test split examples.
- [Troubleshooting](references/troubleshooting.md): mismatched lengths, edge shapes, hetero key mismatches, optional attribute alignment, and split/slice surprises.
- [Synthetic smoke script](scripts/signal_iterator_smoke.py): no-download validator for ordinary, batch, hetero, dynamic-static, and split cases.
