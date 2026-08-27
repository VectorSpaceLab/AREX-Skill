# DGL Dataloading and GraphBolt Troubleshooting

Diagnose dataloading failures by first identifying the route: classic `dgl.dataloading.DataLoader` tuple output or GraphBolt `gb.DataLoader`/`gb.MiniBatch` output. Do not mix graph types, feature stores, or device rules across those routes.

## Classic DGL Device Mismatch

Symptoms:

- `ValueError: Expect graph and indices to be on the same device when use_uva=False.`
- `Graph must be on CPU if UVA sampling is enabled.`
- Blocks or prefetched features arrive on CPU while model parameters are on CUDA.

Fixes:

- CPU sampling: keep `graph` and `indices` on CPU, set `use_uva=False`, and set `device` to CPU or CUDA depending on output placement.
- GPU sampling: move both `graph` and `indices` to the same CUDA device, set `device` to that device, and set `num_workers=0`.
- UVA sampling: keep `graph` on CPU, move `indices` to the CUDA `device`, set `use_uva=True`, and set `num_workers=0`.
- Check `blocks[0].device`, feature tensor devices, labels, and model parameter devices before the first backward pass.

## `num_workers` with CUDA or UVA

Symptoms:

- `ValueError: num_workers must be 0 if UVA sampling is enabled.`
- `ValueError: num_workers must be 0 if graph and indices are on CUDA.`
- CUDA context errors, worker crashes, or hanging PyTorch loaders.

Fixes:

- Set `num_workers=0` for classic GPU sampling and classic UVA sampling.
- In GraphBolt, set `num_workers=0` when `copy_to(cuda_device)` is placed early or while debugging CUDA-related failures.
- Only add workers after a CPU pipeline is correct and after feature fetching/copy stages are placed according to the GraphBolt workflow.

## `use_uva` Constraints

Symptoms:

- UVA loader construction fails.
- GPU memory use is unexpectedly high.
- Sampling is slow despite `use_uva=True`.

Fixes:

- Confirm this is classic `dgl.dataloading.DataLoader`, not GraphBolt GPU sampling.
- Keep graph on CPU; do not call `graph.to('cuda')` for UVA.
- Move seed IDs to the target CUDA device before constructing the loader.
- Keep `num_workers=0`.
- Do not force `pin_prefetcher=True` or `use_prefetch_thread=True` with UVA; those advanced options are for CPU sampling with CUDA output when `use_uva=False`.
- Materialize sparse formats before multi-process training when advised by the distributed workflow owner.

## GraphBolt Native Library or Torch ABI Mismatch

Symptoms:

- Importing `dgl.graphbolt` fails.
- Error mentions a missing GraphBolt library, `libgraphbolt`, `graphbolt_pytorch_*`, unresolved symbols, or a PyTorch version suffix.
- GraphBolt works in source builds but not in the installed wheel, or vice versa.

Fixes:

- Verify `import dgl, torch; import dgl.graphbolt as gb` in the same Python environment that will run training.
- Ensure the DGL package build matches the installed PyTorch version and CPU/CUDA variant. GraphBolt native libraries are version-coupled to PyTorch.
- If GraphBolt import fails but classic DGL works, use classic `dgl.dataloading.DataLoader` as a fallback for in-memory graph training.
- Do not copy GraphBolt native libraries between environments; install a matching DGL build instead.
- For CPU-only validation, run `python scripts/graphbolt_pipeline_sanity.py --skip-graphbolt` to validate metadata shape without importing GraphBolt.

## GraphBolt Graph Type Mismatch

Symptoms:

- `gb.NeighborSampler` rejects a regular `DGLGraph`.
- Pipeline fails when `datapipe.sample_neighbor(graph, fanouts)` is called.
- `MiniBatch.sampled_subgraphs` or `MiniBatch.blocks` is missing after sampling.

Fixes:

- Use `dataset.graph` from `gb.OnDiskDataset(...).load()` or a `gb.fused_csc_sampling_graph(...)` object with GraphBolt samplers.
- Use classic `dgl.dataloading.NeighborSampler` for a regular `DGLGraph`.
- Keep fanouts as integers or 1D tensors accepted by the installed DGL version; tests commonly use `torch.LongTensor([fanout])` per layer.
- Verify the pipeline order is `ItemSampler -> NeighborSampler -> FeatureFetcher -> copy_to -> DataLoader`.

## Feature Name or Type Mismatch

Symptoms:

- `KeyError` from `FeatureFetcher` or feature store reads.
- `minibatch.node_features` is empty or lacks an expected key.
- Heterograph features are present but accessed with homogeneous string keys.

Fixes:

- For homogeneous GraphBolt, fetch with `node_feature_keys=["feat"]` and read `minibatch.node_features["feat"]`.
- For heterogeneous GraphBolt, fetch with `node_feature_keys={"paper": ["feat"]}` and read `minibatch.node_features[("paper", "feat")]`.
- For edge features, use edge type strings such as `"user:likes:item"` in `edge_feature_keys` and inspect each layer dict in `minibatch.edge_features`.
- Check `metadata.yaml` `feature_data` entries for matching `domain`, `type`, and `name`.
- In classic DGL prefetch, ensure `prefetch_node_feats`, `prefetch_labels`, and `prefetch_edge_feats` names exist in `graph.ndata`/`graph.edata` for every sampled type.

## Empty Seeds, Empty Splits, or Dropped Last Batch

Symptoms:

- `StopIteration` on the first `next(iter(loader))`.
- No minibatches are produced.
- Last partial batch disappears.
- GraphBolt `ItemSampler` length is zero.

Fixes:

- Check `len(train_set)` or `len(train_nid)` before constructing the loader.
- For `ItemSet(int_count, names="seeds")`, ensure `int_count > 0`.
- For tuple `ItemSet((seeds, labels), ...)`, ensure all tensors share the same first dimension.
- Set `drop_last=False` while debugging small datasets.
- In `OnDiskDataset`, verify `tasks`, selected task name, and split lists. A missing selected task may be skipped by the loader.
- For heterograph `HeteroItemSet`, inspect per-type lengths; one type can be empty even if another is non-empty.

## Item Names and MiniBatch Mapping

Symptoms:

- Warning: `Failed to map item list to MiniBatch as the names of items are not provided.`
- Warning: `Unknown item name ... is detected and added into MiniBatch.`
- Downstream code expects `minibatch.labels` but it is `None`.

Fixes:

- Provide `names="seeds"` for seed-only item sets.
- Provide `names=("seeds", "labels")` for supervised node or edge sets.
- Provide `names=("seeds", "labels", "indexes")` when grouped indexes are part of the task.
- For nonstandard item fields, pass a custom `minibatcher` to `gb.ItemSampler` and document the resulting `MiniBatch` attributes.
- Validate `metadata.yaml` split `data[].name` values because `OnDiskDataset` uses them to create `ItemSet` names.

## Fanout, Layer, and Block Shape Errors

Symptoms:

- Model has more or fewer layers than sampled blocks.
- First layer feature rows do not match block source nodes.
- Heterograph relation modules receive missing destination types.

Fixes:

- Set `len(fanouts)` equal to model message-passing layers.
- Use `fanout=-1` or `MultiLayerFullNeighborSampler(num_layers)` for full-neighbor minibatch dependencies.
- Inspect `len(blocks)`, `blocks[0].num_src_nodes()`, and `blocks[-1].num_dst_nodes()` before model code.
- For heterographs, build fanout dicts keyed by canonical edge types when different relations need different fanouts.
- Route model-specific block handling to `../message-passing-training/`.

## Edge Prediction Leakage

Symptoms:

- Link prediction validation looks unrealistically high.
- Positive training edges are sampled into their own neighborhoods.
- Reverse edges leak target labels.

Fixes:

- Classic DGL: use `as_edge_prediction_sampler(..., exclude='self')` at minimum.
- Use `exclude='reverse_id'` with `reverse_eids` when reverse edges share the same edge type.
- Use `exclude='reverse_types'` with `reverse_etypes` when reverse edges are stored in separate canonical edge types.
- GraphBolt: add negative sampling before neighbor sampling and use `datapipe.transform(gb.exclude_seed_edges)` when applicable.
- Confirm reverse mappings align with the graph after any edge reordering or preprocessing.

## OnDiskDataset Metadata Failures

Symptoms:

- YAML validation errors from pydantic or GraphBolt metadata models.
- Paths not found after moving a dataset directory.
- Loaded task sets have unexpected names or custom attributes.

Fixes:

- Use `metadata.yaml`, not `meta.yaml`.
- Keep paths relative to the metadata directory.
- Use `format: numpy` or `format: torch` for features and task data.
- Use `format: csv` or `format: numpy` for raw graph edges.
- In `tasks.*_set[].data`, use `name: seeds`, `labels`, or `indexes` unless a custom minibatcher expects another field.
- For heterographs, use `type: src:rel:dst` for edge-task sets and edge features.
- Run `python scripts/graphbolt_pipeline_sanity.py --metadata PATH --skip-graphbolt` for a shallow check before invoking full preprocessing.

## Performance Regressions After Correctness

Symptoms:

- CPU is saturated but GPU is idle.
- Dataloader spends most time fetching features.
- Multiprocessing makes GraphBolt slower or unstable.

Fixes:

- Increase `batch_size` only after memory checks pass.
- For classic CPU sampling with CUDA output, allow DGL defaults for prefetch threads/pinned prefetcher after debugging.
- For GraphBolt, add `num_workers` only after `FeatureFetcher` is placed; GraphBolt wraps the pipeline around feature fetching.
- Enable GraphBolt overlap options one at a time and keep `max_uva_threads` conservative if feature or graph fetch overlap starves compute.
- Keep `in_memory: false` only for features too large for RAM; small frequently accessed arrays are often faster in memory.
