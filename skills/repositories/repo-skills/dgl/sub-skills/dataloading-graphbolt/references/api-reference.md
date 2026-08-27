# DGL Dataloading and GraphBolt API Reference

This reference targets DGL 2.x PyTorch workflows. Live inspection verified DGL 2.1.0 signatures, while source/docs/tests evidence from a newer DGL checkout fills in GraphBolt and OnDiskDataset behavior. Prefer the live signatures for call shapes and this reference for practical contracts.

## Classic `dgl.dataloading`

Use classic dataloading when you already have a `DGLGraph` and want node/edge minibatches, GPU sampling, or UVA sampling.

Verified signatures:

- `dgl.dataloading.DataLoader(graph, indices, graph_sampler, device=None, use_ddp=False, ddp_seed=0, batch_size=1, drop_last=False, shuffle=False, use_prefetch_thread=None, use_alternate_streams=None, pin_prefetcher=None, use_uva=False, gpu_cache=None, **kwargs)`
- `dgl.dataloading.NeighborSampler(fanouts, edge_dir='in', prob=None, mask=None, replace=False, prefetch_node_feats=None, prefetch_labels=None, prefetch_edge_feats=None, output_device=None, fused=True)`
- `dgl.dataloading.MultiLayerFullNeighborSampler(num_layers, **kwargs)`
- `dgl.dataloading.as_edge_prediction_sampler(sampler, exclude=None, reverse_eids=None, reverse_etypes=None, negative_sampler=None, prefetch_labels=None)`

`DataLoader` inputs:

- `graph`: a homogeneous or heterogeneous `DGLGraph`.
- `indices`: a tensor for homogeneous node/edge IDs, or `{type: tensor}` for heterographs. For edge prediction, these are edge IDs keyed by canonical edge type when heterogeneous.
- `graph_sampler`: a `Sampler`, usually `NeighborSampler`, `MultiLayerFullNeighborSampler`, or a node sampler wrapped by `as_edge_prediction_sampler()`.
- `batch_size`, `shuffle`, `drop_last`, `num_workers`, and `persistent_workers` are forwarded in PyTorch `DataLoader` style through `**kwargs`.

Classic node minibatch output:

```python
for input_nodes, output_nodes, blocks in dataloader:
    # input_nodes: source nodes needed by the first GNN layer.
    # output_nodes: seed/output nodes for the last layer.
    # blocks: list[DGLBlock], one block per GNN layer.
    pass
```

Classic edge/link minibatch output after `as_edge_prediction_sampler()`:

```python
for input_nodes, pair_graph, blocks in dataloader:
    pass

for input_nodes, pair_graph, negative_graph, blocks in dataloader:
    pass
```

`NeighborSampler` contracts:

- `fanouts` length equals the number of GNN layers. Use `[15, 10, 5]` for three layers ordered from outermost dependency layer to innermost output layer.
- A fanout item can be an integer for all edge types or a dict keyed by canonical edge type for heterographs.
- `-1` samples all neighbors for a layer/edge type.
- `edge_dir='in'` is the usual message-passing direction; use `'out'` for reverse dependency traversal.
- `prob` names a scalar edge feature containing non-negative sampling weights.
- `mask` names a boolean edge feature. `prob` and `mask` are mutually exclusive.
- `prefetch_node_feats`, `prefetch_labels`, and `prefetch_edge_feats` create lazy feature fetches into the returned blocks.

`MultiLayerFullNeighborSampler(num_layers, **kwargs)` is equivalent to `NeighborSampler([-1] * num_layers, **kwargs)`.

`as_edge_prediction_sampler()` contracts:

- Wraps a node-wise sampler so each batch of edge IDs builds a positive pair graph and sampled blocks around the pair graph's incident nodes.
- `exclude='self'` excludes the current positive edges from sampled neighborhoods.
- `exclude='reverse_id'` also excludes reverse edges according to `reverse_eids`.
- `exclude='reverse_types'` excludes reverse edges stored under paired canonical edge types from `reverse_etypes`.
- `negative_sampler` returns negative pairs. Homogeneous samplers may return `(src, dst)`; heterograph samplers should return `{canonical_etype: (src, dst)}`.
- `prefetch_labels` fetches edge labels onto the positive pair graph.

## Blocks and `dgl.to_block()` Handoff

Classic `NeighborSampler` samples frontiers and converts each frontier to a block. A block is a bipartite `DGLBlock` where destination nodes are the seed/output nodes for that layer and source nodes are the dependency nodes needed to compute them.

Key block fields:

- `block.srcdata[dgl.NID]`: original node IDs for source side input.
- `block.dstdata[dgl.NID]`: original node IDs for destination side output.
- `block.edata[dgl.EID]`: original edge IDs when available.
- `block.is_block`: true for block graphs.

For model code, route details to `../message-passing-training/`: built-in DGL layers usually accept `layer(block, feat)` or `layer(block, (src_feat, dst_feat))`.

## GraphBolt Core Objects

Import as `import dgl.graphbolt as gb`. GraphBolt builds a PyTorch DataPipe pipeline that passes `gb.MiniBatch` objects through item sampling, subgraph sampling, feature fetching, and device copy stages.

Verified signatures from live inspection:

- `gb.ItemSet(items, names=None)`
- `gb.ItemSampler(item_set, batch_size, minibatcher=..., drop_last=False, shuffle=False, use_indexing=True, buffer_size=-1)`
- `gb.DataLoader(datapipe, num_workers=0, persistent_workers=True, overlap_feature_fetch=True, overlap_graph_fetch=False, max_uva_threads=6144)`

Source-level GraphBolt constructor forms in DGL 2.x also include:

- `gb.HeteroItemSet({type_or_etype: gb.ItemSet(...)})`
- `gb.ItemSetDict(...)` as a deprecated alias for `HeteroItemSet`; prefer `HeteroItemSet` in new code.
- `gb.NeighborSampler(datapipe, graph, fanouts, replace=False, prob_name=None, deduplicate=True, overlap_fetch=False, num_gpu_cached_edges=0, gpu_cache_threshold=1, cooperative=False, asynchronous=False)`
- Functional DataPipe form: `datapipe.sample_neighbor(graph, fanouts, ...)`.
- `gb.FeatureFetcher(datapipe, feature_store, node_feature_keys=None, edge_feature_keys=None, overlap_fetch=True, cooperative=False)` or `datapipe.fetch_feature(feature_store, node_feature_keys=..., edge_feature_keys=...)`.
- `datapipe.copy_to(device)` to move minibatch data after sampling/fetching.

## `ItemSet`, `HeteroItemSet`, and `ItemSampler`

`ItemSet` wraps the initial training/evaluation items:

- `items=int` or scalar tensor means IDs are `torch.arange(items)`.
- `items=tensor` indexes along the first dimension. Use shape `(N,)` for node seeds and `(N, 2)` for node pairs.
- `items=(tensor1, tensor2, ...)` requires equal first dimension and maps to multiple minibatch fields.
- `names` must have one name per item tensor. Common names are `"seeds"`, `"labels"`, and `"indexes"` because the default minibatcher maps these to `MiniBatch` attributes.

Examples:

```python
seed_nodes = gb.ItemSet(torch.arange(num_train_nodes), names="seeds")
node_pairs = gb.ItemSet(edge_pairs, names="seeds")
node_pairs_with_labels = gb.ItemSet((edge_pairs, labels), names=("seeds", "labels"))
hetero_nodes = gb.HeteroItemSet({"paper": gb.ItemSet(paper_ids, names="seeds")})
hetero_edges = gb.HeteroItemSet({"user:likes:item": gb.ItemSet(pair_ids, names="seeds")})
```

`ItemSampler(item_set, batch_size, shuffle=False, drop_last=False, ...)` yields minibatches. With recognized names, the default minibatcher returns a `MiniBatch`; without names, it returns raw batches and emits a warning.

## `MiniBatch` Contract

Common `gb.MiniBatch` attributes:

- `seeds`: seed nodes or node pairs; tensor for homogeneous data or dict for heterogeneous data.
- `labels`: labels aligned with `seeds`, tensor or dict.
- `indexes`: query/group indexes aligned with seeds, especially for hyperlink or grouped negative sampling tasks.
- `sampled_subgraphs`: list of GraphBolt sampled subgraph objects, one per sampled layer.
- `input_nodes`: nodes needed by the outermost layer.
- `node_features`: `{feature_name: tensor}` for homogeneous graphs, `{(ntype, feature_name): tensor}` for heterogeneous graphs.
- `edge_features`: list of feature dicts, one per sampled layer; heterograph edge keys are `(etype_string, feature_name)`.
- `compacted_seeds`: node-pair seeds compacted into minibatch-local node IDs for link prediction.
- `blocks`: lazily converts `sampled_subgraphs` into DGL blocks for DGL layer forward code.

GraphBolt training code usually unpacks `MiniBatch` as:

```python
for batch in gb.DataLoader(datapipe):
    x = batch.node_features["feat"]
    y = batch.labels
    blocks = batch.blocks
```

## GraphBolt Graph and Feature Stores

GraphBolt samplers operate on a `FusedCSCSamplingGraph`, usually loaded from `gb.OnDiskDataset(...).load().graph` or built with `gb.fused_csc_sampling_graph(indptr, indices, ...)` for custom tests.

Feature fetchers operate on a GraphBolt feature store:

- `dataset.feature` from `OnDiskDataset` returns a `TorchBasedFeatureStore`.
- `gb.BasicFeatureStore({("node", None, "feat"): gb.TorchBasedFeature(tensor)})` is useful for tiny synthetic examples.
- Homogeneous `node_feature_keys=["feat"]` yields `batch.node_features["feat"]`.
- Heterogeneous `node_feature_keys={"paper": ["feat"]}` yields `batch.node_features[("paper", "feat")]`.
- Edge feature keys use edge type strings such as `"user:likes:item"` in GraphBolt feature stores.

## GraphBolt `DataLoader`

`gb.DataLoader(datapipe, ...)` iterates the finished pipeline and handles multiprocessing around feature fetching where supported.

Practical contracts:

- Use `num_workers=0` while developing, debugging, or when a `copy_to(cuda_device)` stage appears before multiprocessing-sensitive stages.
- With `num_workers>0`, GraphBolt inserts minibatch sharding after `ItemSampler` and wraps the pipeline before `FeatureFetcher` in a PyTorch multiprocessing loader.
- `persistent_workers=True` only has an effect when `num_workers>0`.
- `max_uva_threads` limits CUDA thread use for UVA feature or graph fetch overlap.
- If using a runtime where `gb.DataLoader` exposes `overlap_feature_fetch` or `overlap_graph_fetch`, keep overlap disabled until the CPU pipeline is correct, then enable one optimization at a time.

## `OnDiskDataset`

`gb.OnDiskDataset(path, include_original_edge_id=False, force_preprocess=None, auto_cast_to_optimal_dtype=True)` reads a dataset directory or metadata path and returns itself after `.load()`.

Important attributes after `dataset = gb.OnDiskDataset(dataset_dir).load()`:

- `dataset.dataset_name`: optional top-level dataset name.
- `dataset.graph`: `FusedCSCSamplingGraph` for GraphBolt sampling, if graph topology exists.
- `dataset.feature`: feature store for `fetch_feature()`.
- `dataset.tasks`: list of task objects with `.metadata`, `.train_set`, `.validation_set`, and `.test_set`.
- `dataset.all_nodes_set`: `ItemSet` or `HeteroItemSet` containing all nodes.

Task sets are converted to `ItemSet` or `HeteroItemSet` using the `data[].name` fields, so `seeds`, `labels`, and `indexes` names directly control the `MiniBatch` fields produced by `ItemSampler`.
