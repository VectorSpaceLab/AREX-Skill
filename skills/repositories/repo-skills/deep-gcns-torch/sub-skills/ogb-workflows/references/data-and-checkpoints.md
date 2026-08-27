# OGB data, feature, layout, and checkpoint contracts

## Data contracts

- **Node tasks:** a PyG node dataset supplies one `Data` object with
  `x`, `edge_index`, and `y`; split indices come from `get_idx_split()`. Arxiv
  converts the edge list to undirected form and optionally adds self-loops.
  Products and proteins construct induced subgraphs from random integer cluster
  assignments. A partition is not a lossless mini-batch: edges crossing the
  selected node set are absent from that subgraph. Repartitioning occurs every
  training epoch in the reference workflows.
- **Graph tasks:** a PyG batch supplies node `x`, `edge_index`, `edge_attr`,
  graph assignment vector `batch`, and graph-level `y`. The output is one row
  per graph. Skip degenerate one-node batches only as the source training loop
  does; do not infer that an empty loss is valid.
- **Link task:** `ogbl-collab` supplies node features and a graph edge index,
  while `get_edge_split()` supplies positive train/validation/test edges and
  sampled negative validation/test edges. The encoder produces all node
  embeddings; endpoint pairs are processed in edge-sized batches.
- **Proteins:** raw node labels are multi-task binary labels and raw edge
  attributes are width 8. The dataset helper aggregates edge attributes by
  source node using `add`, `mean`, or `max` to create the initial node feature
  file. Its optional species encoding is a categorical one-hot matrix used as
  the second input branch.

## Molecular and PPA features

- `AtomEncoder` and `BondEncoder` are OGB categorical encoders, not ordinary
  float linear layers. Preserve integer categorical tensors when using them.
- Molecular `--feature simple` slices node and edge attributes to their first
  two columns, so it is a deliberately smaller ablation and not equivalent to
  the full feature mode.
- Molecular graph pooling is selected by `--graph_pooling`: `mean` (default),
  `max`, or `sum` (`global_mean_pool`, `global_max_pool`, or `global_add_pool`).
- With `--add_virtual_node`, the model initializes one zero embedding per
  graph, adds it to every node, then updates it from `global_add_pool` plus an
  MLP after each intermediate layer. The graph `batch` vector must be present.
- PPA starts with zero node features only when `--not_extract_node_feature`
  is set; otherwise `utils.data_util.extract_node_feature` reduces edge
  attributes by `--aggr` (`add`, `mean`, or `max`).

## Partition implementation details

The reference helper samples `parts = randint(cluster_number, size=num_nodes)`.
For each cluster it selects nodes assigned to that cluster and extracts the
induced edge index. Therefore cluster sizes are random, may be uneven, and
some clusters can be empty in a tiny synthetic fixture. The documented large
runs use one subgraph per optimizer step. Products use 10 clusters for train
and full-batch CPU test; proteins use 10 for train and 5 for evaluation. The
reversible proteins workflow preserves the same partition contract.

For a safe local experiment, make the partition explicit, seed it, assert that
all node IDs are in range, and report the number of retained versus original
edges. Do not call the dataset helper merely to test partitioning: its dataset
constructor may download OGB data and its cache files are working-directory
relative.

## Checkpoint contract

The standard PyG training helper saves a dictionary containing:

```python
{
    "epoch": epoch,
    "model_state_dict": model.state_dict(),  # moved to CPU before saving
    "optimizer_state_dict": optimizer.state_dict(),
    "loss": loss,
}
```

Files are named from a task-specific prefix and suffix such as
`<subdir>_valid_best.pth`. Evaluation loads `checkpoint["model_state_dict"]`.
The link workflow saves a second dictionary for the link predictor, with a
separate `*_valid_best_link_predictor.pth` name. Use `map_location="cpu"` for
CPU inspection and move the model after loading. Do not assume the alternative
utility `load_pretrained_models` format (`state_dict`, optional best value,
and optional scheduler) is interchangeable with the OGB `save_ckpt` format.

Checkpoints are architecture-specific. Match dataset feature mode, hidden
width, block, layer count, aggregator, normalization, edge encoding, virtual
node choice, pooling, reversible group, and predictor depth before loading.
An external filename in documentation is a prerequisite, not a bundled asset;
never fetch it implicitly.

## Backend and version boundary

The historical README calls for PyTorch 1.5 and PyG 1.6-era APIs. The inspected
runtime instead has PyTorch 2.11.0+cu128, PyG 2.8.0.post1, matching scatter and
cluster extensions, OGB 1.3.6, and a working CUDA allocation. CPU synthetic
model checks are portable across the selected PyG-compatible environment, but
neither CPU nor a tiny graph validates the original large-graph result. The
repository's SAGE wrapper is incompatible with modern PyG; use GENConv or
route API-level alternatives to graph-layers after checking the installed
signatures.
