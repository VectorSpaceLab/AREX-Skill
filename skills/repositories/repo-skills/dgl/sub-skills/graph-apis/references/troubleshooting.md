# Graph API Troubleshooting

Use this checklist when graph construction, feature assignment, conversion, batching, or subgraph extraction fails.

## Import or Native Library Failure

Symptoms:

- `import dgl` fails before any graph code runs.
- Error mentions a missing DGL shared library, GraphBolt library, backend selection, `torchdata`, PyTorch, CUDA, or incompatible package versions.
- A smoke script fails before printing graph checks.

Actions:

1. Confirm the active Python environment can import `torch` and `dgl` in the same interpreter.
2. Check `python -c "import dgl, torch; print(dgl.__version__, torch.__version__)"`.
3. Prefer CPU-only graph API checks unless the task explicitly requires CUDA.
4. If the error is about package installation, backend compatibility, persistent datasets, or graph I/O setup, route to [datasets-and-io](../../datasets-and-io/SKILL.md) for environment and storage guidance.
5. If the task is only graph construction, run `python scripts/graph_smoke.py` from this sub-skill directory after import is fixed.

## Canonical Edge-Type Ambiguity

Symptoms:

- Error says edge type name must be specified.
- Error says an edge type is ambiguous.
- `hg.etypes` contains duplicate strings such as `['rates', 'rates']`.
- `hg.edges['rates'].data[...]`, `hg.num_edges('rates')`, or `hg.edges(etype='rates')` fails or reads the wrong relation.

Cause:

DGL lets multiple canonical edge types share the same relation name. A bare string is valid only when it uniquely identifies one canonical triplet.

Actions:

```python
print(hg.canonical_etypes)
canonical_etype = ('user', 'rates', 'movie')
assert canonical_etype in hg.canonical_etypes
src, dst, eid = hg.edges(form='all', etype=canonical_etype)
hg.edges[canonical_etype].data['score'] = score_tensor
```

For caller-provided strings, resolve them before use:

```python
matches = [c_etype for c_etype in hg.canonical_etypes if c_etype[1] == etype]
if len(matches) != 1:
    raise ValueError(f'pass a canonical etype, got {etype!r} matching {matches}')
canonical_etype = matches[0]
```

## Feature Shape or Dtype Mismatch

Symptoms:

- Assignment fails when writing `g.ndata['feat']` or `g.edata['weight']`.
- `dgl.batch` fails with a schema mismatch.
- `dgl.to_homogeneous(..., ndata=[...])` or `edata=[...]` fails while concatenating features.
- Error mentions incompatible `Scheme(shape=..., dtype=...)`.

Causes:

- The tensor's first dimension does not match the node/edge count for that type.
- Feature dtypes differ across graphs or across node/edge types.
- Feature trailing shapes differ across graphs or across node/edge types.
- A requested feature key is missing on one graph/type.

Actions:

```python
assert feat.shape[0] == g.num_nodes()
assert weight.shape[0] == g.num_edges()

for ntype in hg.ntypes:
    assert hg.nodes[ntype].data['feat'].shape[0] == hg.num_nodes(ntype)

for c_etype in hg.canonical_etypes:
    if 'weight' in hg.edges[c_etype].data:
        assert hg.edges[c_etype].data['weight'].shape[0] == hg.num_edges(c_etype)
```

When batching or converting, either standardize schemas or opt out:

```python
bg = dgl.batch(graphs, ndata=['feat'], edata=None)
homogeneous = dgl.to_homogeneous(hg, ndata=['feat'], edata=None)
```

## Device Mismatch

Symptoms:

- Error mentions tensors and graph are on different devices.
- `dst_nodes` passed to `dgl.to_block` fails context checks.
- Feature assignment fails after moving only part of the data to CUDA or CPU.

Actions:

```python
device = g.device
feat = feat.to(device)
g.ndata['feat'] = feat

# For tensor selections, match both device and idtype.
nodes = torch.tensor([0, 1], dtype=g.idtype, device=g.device)
sg = dgl.node_subgraph(g, nodes)
```

Move graph and features together:

```python
g = g.to(torch.device('cpu'))
```

Do not require CUDA for graph API validation unless the user's task explicitly needs GPU execution.

## ID Type Mismatch

Symptoms:

- Error mentions int32/int64 mismatch.
- Subgraph selection or edge lookup rejects an ID tensor.
- Code mixes default `torch.int64` tensors with an int32 graph.

Actions:

```python
ids = torch.tensor([0, 1], dtype=g.idtype, device=g.device)
sg = dgl.node_subgraph(g, ids)

# Or standardize the graph structure dtype.
g = g.long()  # int64
# or
g = g.int()   # int32
```

Guidance:

- Use `torch.int64` unless memory pressure or downstream code requires `torch.int32`.
- Use `idtype=torch.int32` at construction time for small graphs only when the whole workflow supports int32 IDs.
- Keep all structure ID tensors in the same dtype as `g.idtype`.

## Zero Nodes, Zero Edges, and Isolated Nodes

Symptoms:

- Graph has fewer nodes than expected.
- Feature assignment fails because `feat.shape[0]` is larger than `g.num_nodes()`.
- A node type disappears or has zero nodes in a heterograph.
- Subgraph extraction returns zero edges unexpectedly.

Causes:

- `dgl.graph` infers node count from edge endpoints when `num_nodes` is omitted.
- `dgl.heterograph` infers each node type count from endpoints unless `num_nodes_dict` is provided.
- A selected subgraph has no edges after filtering.

Actions:

```python
g = dgl.graph((src, dst), num_nodes=expected_num_nodes)

hg = dgl.heterograph(
    data_dict,
    num_nodes_dict={'user': num_users, 'movie': num_movies, 'critic': num_critics},
)
```

Validation:

```python
for ntype in hg.ntypes:
    print(ntype, hg.num_nodes(ntype))
for c_etype in hg.canonical_etypes:
    print(c_etype, hg.num_edges(c_etype))
```

Zero-edge graphs can still be valid, but batching and feature assignment require consistent schemas if features are batched.

## Batching Schema Mismatch

Symptoms:

- `dgl.batch` fails with schema mismatch.
- Heterograph batching fails even though each graph works independently.
- Batched feature shape is not the expected sum of component rows.

Causes:

- Input list is empty.
- Heterographs do not share the same canonical edge types or node types.
- A selected feature key is missing on one graph.
- A selected feature has different dtype or trailing shape.
- A block graph was passed to `dgl.batch`.

Actions:

```python
assert graphs
schema0 = (tuple(graphs[0].ntypes), tuple(graphs[0].canonical_etypes))
for graph in graphs:
    assert not graph.is_block
    assert (tuple(graph.ntypes), tuple(graph.canonical_etypes)) == schema0

bg = dgl.batch(graphs, ndata=['feat'], edata=None)
```

If feature schemas cannot be standardized, batch structure only:

```python
bg = dgl.batch(graphs, ndata=None, edata=None)
```

For custom unbatching of heterographs, provide complete dictionaries:

```python
parts = dgl.unbatch(
    bg,
    node_split={ntype: split_tensor for ntype in bg.ntypes},
    edge_split={c_etype: split_tensor for c_etype in bg.canonical_etypes},
)
```

## Homogeneous Conversion Fails

Symptoms:

- `dgl.to_homogeneous` fails on selected `ndata` or `edata`.
- Reconstructed graph from `dgl.to_heterogeneous` has unexpected relation order.
- Type or original ID fields are missing.

Actions:

1. Before conversion, make requested feature keys present on every relevant type.
2. Ensure each requested key has the same trailing shape and dtype across all node or edge types.
3. Keep `store_type=True` when you need `dgl.to_heterogeneous` later.
4. Use `return_count=True` if downstream code needs type segment lengths.
5. Compare sets of `ntypes` and `canonical_etypes`, not list order, unless the order is part of the task contract.

## `to_block` Fails

Symptoms:

- Error says `dst_nodes` is not a superset of nodes with inbound edges.
- Error says tensor form cannot be used with multiple node types.
- Error says graph and `dst_nodes` need the same context.

Actions:

```python
# Homogeneous graph.
dst_nodes = torch.tensor([2, 3], dtype=g.idtype, device=g.device)
block = dgl.to_block(g, dst_nodes=dst_nodes)

# Heterograph.
dst_nodes = {'movie': torch.tensor([0, 1], dtype=hg.idtype, device=hg.device)}
block = dgl.to_block(hg, dst_nodes=dst_nodes)
```

If destination nodes are sampled by a dataloader or neighbor sampler, route to [dataloading-graphbolt](../../dataloading-graphbolt/SKILL.md) rather than manually recreating the full sampling stack.

## Subgraph Selection Fails

Symptoms:

- Heterograph subgraph call asks for a dictionary.
- Edge selection returns unexpected relation data.
- Result lacks batch metadata.

Actions:

```python
node_selection = {'user': torch.tensor([0, 1], dtype=hg.idtype, device=hg.device)}
sg = dgl.node_subgraph(hg, node_selection, store_ids=True)

edge_selection = {('user', 'rates', 'movie'): torch.tensor([0], dtype=hg.idtype, device=hg.device)}
esg = dgl.edge_subgraph(hg, edge_selection, relabel_nodes=True, store_ids=True)
```

Remember:

- Heterograph node selections are keyed by node type.
- Heterograph edge selections are keyed by canonical edge type.
- `dgl.NID` and `dgl.EID` preserve original IDs when `store_ids=True`.
- Subgraph extraction discards batch information; restore it only if the downstream task requires unbatching.
