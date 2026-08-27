# DGL Dataloading and GraphBolt Workflows

Use these workflows to choose and assemble stochastic minibatch pipelines. Keep model-layer code in `../message-passing-training/`; this reference owns data movement, sampling, and minibatch object handoff.

## Choose Classic DGL DataLoader vs GraphBolt

Use classic `dgl.dataloading.DataLoader` when:

- You already have a `DGLGraph` in memory and seed node/edge ID tensors.
- You need GPU neighbor sampling or CUDA UVA sampling. GraphBolt does not support GPU-based neighborhood sampling in the DGL evidence used for this skill; use classic `DataLoader` for this route.
- You need mature `as_edge_prediction_sampler()` wrappers around DGL graph samplers.
- You want the familiar `(input_nodes, output_nodes, blocks)` or `(input_nodes, pair_graph, blocks)` iterator output.

Use GraphBolt when:

- You want a composable DataPipe pipeline with explicit stages: `ItemSampler -> negative sampler -> NeighborSampler -> FeatureFetcher -> copy_to -> DataLoader`.
- You are loading `OnDiskDataset` graph topology, features, and task splits.
- Features are large, pinned, or disk-backed and should be fetched by GraphBolt feature stores.
- You want a unified `MiniBatch` object with `seeds`, `labels`, `sampled_subgraphs`, `node_features`, `edge_features`, `compacted_seeds`, and lazy `blocks`.

Default debugging rule: make the smallest CPU pipeline work first with `num_workers=0`, then add feature fetching, device copy, multiprocessing, and overlap options one at a time.

## Classic Node Classification Neighbor Sampling

```python
import dgl
import torch

sampler = dgl.dataloading.NeighborSampler(
    [15, 10],
    prefetch_node_feats=["feat"],
    prefetch_labels=["label"],
)
dataloader = dgl.dataloading.DataLoader(
    graph,
    train_nid,
    sampler,
    batch_size=1024,
    shuffle=True,
    drop_last=False,
    num_workers=4,
)

for input_nodes, output_nodes, blocks in dataloader:
    input_feat = blocks[0].srcdata["feat"]
    output_label = blocks[-1].dstdata["label"]
    # Route model(blocks, input_feat) to message-passing-training.
```

Checklist:

- `len(fanouts)` must equal the number of GNN layers that consume `blocks`.
- `input_nodes` matches the original IDs represented by `blocks[0].srcdata[dgl.NID]`.
- `output_nodes` matches the seed nodes represented by `blocks[-1].dstdata[dgl.NID]`.
- For heterographs, pass `indices={"paper": train_paper_ids}` and feature names as `{"paper": ["feat"]}` when prefetching.
- If `prob` or `mask` is used, verify the edge feature exists on every sampled edge type and is scalar per edge.

## Classic Link Prediction or Edge Prediction

```python
import dgl

base_sampler = dgl.dataloading.NeighborSampler([10, 10])
edge_sampler = dgl.dataloading.as_edge_prediction_sampler(
    base_sampler,
    exclude="reverse_id",
    reverse_eids=reverse_eid_tensor,
    negative_sampler=negative_sampler,
    prefetch_labels=["label"],
)
dataloader = dgl.dataloading.DataLoader(
    graph,
    train_eids,
    edge_sampler,
    batch_size=1024,
    shuffle=True,
    num_workers=4,
)

for input_nodes, pair_graph, negative_graph, blocks in dataloader:
    # pair_graph contains positive edges; negative_graph comes from negative_sampler.
    # blocks contain sampled neighborhoods around compacted incident nodes.
    labels = pair_graph.edata.get("label")
```

Use `exclude` to prevent label leakage:

- `None`: fastest, but may sample the target edge itself.
- `'self'`: excludes the current positive edge IDs.
- `'reverse_id'`: excludes positive edges and reverse edges according to `reverse_eids`.
- `'reverse_types'`: excludes positive edges and paired reverse canonical edge types according to `reverse_etypes`.

For heterographs, use canonical edge-type dictionaries for `train_eids`, `reverse_eids`, and negative sampler output.

## GraphBolt Node Classification Pipeline

```python
import dgl.graphbolt as gb
import torch

dataset = gb.OnDiskDataset(dataset_dir).load(tasks="node_classification")
graph = dataset.graph
feature = dataset.feature
train_set = dataset.tasks[0].train_set

datapipe = gb.ItemSampler(train_set, batch_size=1024, shuffle=True)
datapipe = datapipe.sample_neighbor(graph, [torch.tensor([10]), torch.tensor([10])])
datapipe = datapipe.fetch_feature(feature, node_feature_keys=["feat"])
datapipe = datapipe.copy_to(torch.device("cpu"))
dataloader = gb.DataLoader(datapipe, num_workers=0)

for minibatch in dataloader:
    x = minibatch.node_features["feat"]
    y = minibatch.labels
    blocks = minibatch.blocks
```

Checklist:

- `train_set` must be an `ItemSet` or `HeteroItemSet` with `names="seeds"` or `names=("seeds", "labels")`.
- `graph` must be a GraphBolt `FusedCSCSamplingGraph`, not a regular `DGLGraph`.
- Fanouts are ordered from outermost dependency layer to innermost layer. Use one fanout item per GNN layer.
- `node_feature_keys=["feat"]` is homogeneous; use `{"paper": ["feat"], "author": ["feat"]}` for heterographs.
- `minibatch.blocks` converts sampled GraphBolt subgraphs into DGL blocks for ordinary DGL layers.

## GraphBolt Link Prediction Pipeline

```python
import dgl.graphbolt as gb
import torch

edge_pairs = torch.tensor([[0, 1], [2, 3], [4, 5]])
labels = torch.ones(edge_pairs.shape[0])
item_set = gb.ItemSet((edge_pairs, labels), names=("seeds", "labels"))

datapipe = gb.ItemSampler(item_set, batch_size=2, shuffle=True)
datapipe = datapipe.sample_uniform_negative(graph, 5)
datapipe = datapipe.sample_neighbor(graph, [torch.tensor([10]), torch.tensor([10])])
datapipe = datapipe.transform(gb.exclude_seed_edges)
datapipe = datapipe.fetch_feature(feature, node_feature_keys=["feat"])
dataloader = gb.DataLoader(datapipe, num_workers=0)

for minibatch in dataloader:
    compact_pairs = minibatch.compacted_seeds
    labels = minibatch.labels
    node_features = minibatch.node_features["feat"]
    blocks = minibatch.blocks
```

Notes:

- `seeds` with shape `(N, 2)` represents node pairs.
- After negative sampling, use `labels` and `compacted_seeds` for positive/negative pair scoring.
- `gb.exclude_seed_edges` prevents target seed edges from appearing in sampled neighborhoods when applicable.
- For heterographs, build `gb.HeteroItemSet({"src:rel:dst": gb.ItemSet(edge_pairs, names="seeds")})` and fetch features with type-key dictionaries.

## GraphBolt Feature Fetching

Feature fetch stage placement:

```python
datapipe = gb.ItemSampler(train_set, batch_size=1024, shuffle=True)
datapipe = datapipe.sample_neighbor(graph, [torch.tensor([15]), torch.tensor([10])])
datapipe = datapipe.fetch_feature(
    feature_store,
    node_feature_keys=["feat"],
    edge_feature_keys=["weight"],
    overlap_fetch=False,
)
datapipe = datapipe.copy_to(device)
```

Feature-key rules:

- Homogeneous node features: `node_feature_keys=["feat", "label"]` produces `minibatch.node_features["feat"]` and `minibatch.node_features["label"]`.
- Heterogeneous node features: `node_feature_keys={"paper": ["feat"], "author": ["feat"]}` produces keys like `("paper", "feat")`.
- Homogeneous edge features: `edge_feature_keys=["weight"]` produces a list `minibatch.edge_features[layer_id]["weight"]`.
- Heterogeneous edge features: `edge_feature_keys={"user:likes:item": ["weight"]}` produces keys like `("user:likes:item", "weight")` in each layer feature dict.
- Missing feature keys are not a data-loading feature; either add the feature to the store or remove it from the fetch list.

## Classic GPU Neighbor Sampling

Use this only when the whole graph and seed indices fit on a single GPU.

```python
device = torch.device("cuda:0")
graph = graph.to(device)
train_nid = train_nid.to(device)
sampler = dgl.dataloading.NeighborSampler([15, 10])
dataloader = dgl.dataloading.DataLoader(
    graph,
    train_nid,
    sampler,
    device=device,
    batch_size=1024,
    shuffle=True,
    drop_last=False,
    num_workers=0,
)
```

Required constraints:

- `graph.device == device`.
- `train_nid.device == device`.
- `device` argument is the same CUDA device.
- `num_workers=0`; CUDA contexts cannot be shared by multiple loader worker processes.
- Do not set `use_uva=True` when the graph itself is already on GPU.

## Classic CUDA UVA Sampling

Use UVA when the graph is too large for GPU memory but CPU graph storage can be pinned and the seed IDs can be on GPU.

```python
device = torch.device("cuda:0")
train_nid = train_nid.to(device)
sampler = dgl.dataloading.NeighborSampler([15, 10])
dataloader = dgl.dataloading.DataLoader(
    graph,                 # CPU graph.
    train_nid,             # GPU seed IDs.
    sampler,
    device=device,
    use_uva=True,
    batch_size=1024,
    shuffle=True,
    drop_last=False,
    num_workers=0,
)
```

Required constraints:

- `graph` must be on CPU.
- `indices` must be on the same device as `device`.
- `num_workers=0`.
- DGL will create sparse formats and pin the graph for DGLGraph inputs.
- Do not enable `pin_prefetcher=True` or `use_prefetch_thread=True` for UVA; those are for CPU sampling with CUDA output when `use_uva=False`.

## CPU Sampling with CUDA Output

Use this when the graph stays on CPU, sampling happens on CPU, but model execution is on GPU.

```python
device = torch.device("cuda:0")
sampler = dgl.dataloading.NeighborSampler(
    [15, 10],
    prefetch_node_feats=["feat"],
    prefetch_labels=["label"],
)
dataloader = dgl.dataloading.DataLoader(
    graph,                 # CPU graph.
    train_nid,             # CPU seed IDs when use_uva=False.
    sampler,
    device=device,
    use_uva=False,
    batch_size=1024,
    shuffle=True,
    num_workers=4,
)
```

DGL may default `pin_prefetcher`, `use_prefetch_thread`, and alternate streams for this route. If debugging, set advanced options explicitly to `False`, then restore them after correctness is proven.

## OnDiskDataset Loading to GraphBolt

```python
import dgl.graphbolt as gb

dataset = gb.OnDiskDataset(dataset_dir).load(tasks="node_classification")
assert dataset.graph is not None
assert len(dataset.tasks) == 1
train_set = dataset.tasks[0].train_set

pipe = gb.ItemSampler(train_set, batch_size=1024, shuffle=True)
pipe = pipe.sample_neighbor(dataset.graph, [10, 10])
pipe = pipe.fetch_feature(dataset.feature, node_feature_keys=["feat"])
loader = gb.DataLoader(pipe, num_workers=0)
```

OnDiskDataset handoff checklist:

- `metadata.yaml` exists and uses relative paths.
- `dataset.tasks[0].train_set` is non-empty before constructing `ItemSampler`.
- Task set `data[].name` values match GraphBolt `MiniBatch` fields: usually `seeds`, `labels`, and optionally `indexes`.
- Graph features needed by sampling probabilities should be stored on the graph topology; model input features should be in `feature_data` and fetched through `dataset.feature`.
- Use `scripts/graphbolt_pipeline_sanity.py --metadata PATH` to catch shallow metadata shape errors before calling `OnDiskDataset`.

## Validation Checklist Before Training

- Print one minibatch and verify object type: tuple for classic DGL loaders, `gb.MiniBatch` for GraphBolt.
- Verify `len(blocks) == len(fanouts)` or `minibatch.num_layers() == len(fanouts)`.
- Verify `blocks[0].num_src_nodes()` matches the first-layer feature row count.
- Verify labels align with `output_nodes` or `minibatch.seeds` depending on the task.
- Verify every tensor consumed by the model is on the expected device.
- Run a single forward/loss/backward step before increasing `batch_size`, `num_workers`, overlap, or GPU/UVA optimizations.
