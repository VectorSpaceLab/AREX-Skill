# Graph API Workflows

These recipes assume a PyTorch backend and small in-memory examples. Keep tensors, graph structure, and feature tensors on the same device.

## Create a Homogeneous Graph

```python
import dgl
import torch

src = torch.tensor([0, 0, 1, 2], dtype=torch.int64)
dst = torch.tensor([1, 2, 2, 3], dtype=torch.int64)
g = dgl.graph((src, dst), num_nodes=5, idtype=torch.int64)

g.ndata['feat'] = torch.randn(g.num_nodes(), 8)
g.edata['weight'] = torch.ones(g.num_edges(), 1)

assert g.num_nodes() == 5
assert g.num_edges() == 4
assert g.ndata['feat'].shape == (5, 8)
assert g.edata['weight'].shape == (4, 1)
```

Use `num_nodes` when isolated nodes may exist. Without it, DGL infers the count from the maximum node ID in the edge tensors.

## Inspect Graph Structure

```python
print(g.ntypes)
print(g.etypes)
print(g.canonical_etypes)
print(g.idtype, g.device)

nodes = g.nodes()
src, dst, eid = g.edges(form='all', order='eid')
in_src, in_dst, in_eid = g.in_edges(torch.tensor([2]), form='all')
out_src, out_dst, out_eid = g.out_edges(torch.tensor([0]), form='all')
```

Validation checklist:

- `g.num_nodes(ntype)` equals the expected row count for each node feature tensor.
- `g.num_edges(etype)` equals the expected row count for each edge feature tensor.
- `g.idtype` matches ID tensors used later for indexing or subgraph extraction.
- `g.device` matches the device of tensors assigned into `ndata` and `edata`.

## Create a Heterograph

```python
import dgl
import torch

graph_data = {
    ('user', 'rates', 'movie'): (torch.tensor([0, 1, 1]), torch.tensor([0, 0, 1])),
    ('critic', 'rates', 'movie'): (torch.tensor([0]), torch.tensor([1])),
    ('user', 'follows', 'user'): (torch.tensor([0]), torch.tensor([1])),
}
hg = dgl.heterograph(
    graph_data,
    num_nodes_dict={'user': 3, 'critic': 1, 'movie': 2},
    idtype=torch.int64,
)

hg.nodes['user'].data['feat'] = torch.randn(hg.num_nodes('user'), 4)
hg.nodes['movie'].data['feat'] = torch.randn(hg.num_nodes('movie'), 4)
hg.edges[('user', 'rates', 'movie')].data['score'] = torch.ones(
    hg.num_edges(('user', 'rates', 'movie')), 1
)
```

Heterograph checks:

```python
assert set(hg.ntypes) == {'user', 'critic', 'movie'}
assert ('user', 'rates', 'movie') in hg.canonical_etypes
assert ('critic', 'rates', 'movie') in hg.canonical_etypes
assert hg.num_nodes('user') == 3
assert hg.num_edges(('user', 'rates', 'movie')) == 3
```

## Resolve Canonical Edge-Type Ambiguity

When two relations share the same edge type name, do not use the bare string.

```python
# Ambiguous because both canonical edge types use relation name 'rates'.
print(hg.etypes)  # may include ['rates', 'rates', 'follows']

user_rates = ('user', 'rates', 'movie')
critic_rates = ('critic', 'rates', 'movie')

for canonical_etype in [user_rates, critic_rates]:
    src, dst, eid = hg.edges(form='all', etype=canonical_etype)
    print(canonical_etype, src, dst, eid)
```

If a task receives an edge type string from a caller, normalize it:

```python
def require_canonical_etype(graph, etype):
    if isinstance(etype, tuple):
        if etype not in graph.canonical_etypes:
            raise ValueError(f'unknown canonical etype: {etype}')
        return etype
    matches = [c_etype for c_etype in graph.canonical_etypes if c_etype[1] == etype]
    if len(matches) != 1:
        raise ValueError(f'etype {etype!r} matches {matches}; pass a canonical triplet')
    return matches[0]
```

## Convert Heterogeneous to Homogeneous

Use this when downstream code expects one node type and one edge type.

```python
for ntype in hg.ntypes:
    if 'feat' not in hg.nodes[ntype].data:
        hg.nodes[ntype].data['feat'] = torch.zeros(hg.num_nodes(ntype), 4)

homogeneous = dgl.to_homogeneous(hg, ndata=['feat'])

assert dgl.NTYPE in homogeneous.ndata
assert dgl.NID in homogeneous.ndata
assert dgl.ETYPE in homogeneous.edata
assert dgl.EID in homogeneous.edata
assert homogeneous.ndata['feat'].shape[0] == homogeneous.num_nodes()
```

Use `return_count=True` when a model or post-processing step needs type segment lengths:

```python
homogeneous, node_counts, edge_counts = dgl.to_homogeneous(
    hg, ndata=['feat'], store_type=False, return_count=True
)
```

Feature merge rule: every requested `ndata` key must exist for every node type and have the same trailing shape and dtype. Every requested `edata` key must satisfy the same rule across edge types.

## Convert Homogeneous Back to Heterogeneous

```python
homogeneous = dgl.to_homogeneous(hg, ndata=['feat'])
roundtrip = dgl.to_heterogeneous(homogeneous, hg.ntypes, hg.etypes)

assert set(roundtrip.ntypes) == set(hg.ntypes)
assert set(roundtrip.canonical_etypes) == set(hg.canonical_etypes)
```

This works best when the homogeneous graph still has the type fields `dgl.NTYPE` and `dgl.ETYPE` created by `dgl.to_homogeneous(..., store_type=True)`.

## Extract Subgraphs

Homogeneous node subgraph:

```python
sg = dgl.node_subgraph(g, torch.tensor([0, 1, 2]))
assert dgl.NID in sg.ndata
assert dgl.EID in sg.edata
```

Heterogeneous edge subgraph:

```python
selected_edges = {
    ('user', 'rates', 'movie'): torch.tensor([0, 2]),
    ('critic', 'rates', 'movie'): torch.tensor([0]),
}
esg = dgl.edge_subgraph(hg, selected_edges, relabel_nodes=True, store_ids=True)
```

Inbound or outbound subgraphs:

```python
in_sg = dgl.in_subgraph(hg, {'movie': torch.tensor([1])}, relabel_nodes=False)
out_sg = dgl.out_subgraph(hg, {'user': torch.tensor([1])}, relabel_nodes=False)
```

Subgraph checks:

- Use dictionaries for heterographs.
- Use canonical edge types as dictionary keys for edge selections.
- Expect `dgl.NID` and `dgl.EID` when `store_ids=True`.
- Restore batch metadata manually if the input graph was batched.

## Create a Block With Known Destinations

```python
dst_nodes = torch.tensor([2, 3], dtype=g.idtype)
block = dgl.to_block(g, dst_nodes=dst_nodes, include_dst_in_src=True)

assert block.is_block
assert dgl.NID in block.srcdata
assert dgl.NID in block.dstdata
assert dgl.EID in block.edata
```

For heterographs, pass a node-type dictionary:

```python
block = dgl.to_block(hg, dst_nodes={'movie': torch.tensor([0, 1], dtype=hg.idtype)})
movie_dst_ids = block.dstnodes['movie'].data[dgl.NID]
```

Use `to_block` only when destination nodes are explicit and small enough to reason about directly. For production neighbor sampling, route to [dataloading-graphbolt](../../dataloading-graphbolt/SKILL.md).

## Batch and Unbatch Graphs

Homogeneous graphs with matching schemas:

```python
g1 = dgl.graph((torch.tensor([0, 1]), torch.tensor([1, 2])), num_nodes=3)
g2 = dgl.graph((torch.tensor([0]), torch.tensor([1])), num_nodes=2)

g1.ndata['feat'] = torch.zeros(g1.num_nodes(), 4)
g2.ndata['feat'] = torch.ones(g2.num_nodes(), 4)

bg = dgl.batch([g1, g2], ndata=['feat'], edata=None)
assert bg.batch_size == 2
assert bg.batch_num_nodes().tolist() == [3, 2]
assert bg.ndata['feat'].shape == (5, 4)

parts = dgl.unbatch(bg)
assert len(parts) == 2
```

Heterographs with matching schemas:

```python
schema = {('user', 'rates', 'movie'): (torch.tensor([0]), torch.tensor([0]))}
hg1 = dgl.heterograph(schema, num_nodes_dict={'user': 1, 'movie': 1})
hg2 = dgl.heterograph(schema, num_nodes_dict={'user': 1, 'movie': 1})

for graph in [hg1, hg2]:
    graph.nodes['user'].data['feat'] = torch.ones(graph.num_nodes('user'), 2)
    graph.nodes['movie'].data['feat'] = torch.zeros(graph.num_nodes('movie'), 2)

bhg = dgl.batch([hg1, hg2], ndata=['feat'], edata=None)
assert bhg.batch_num_nodes()['user'].tolist() == [1, 1]
```

Batching checks:

- All graphs must have the same relation schema.
- All batched feature keys must exist where required and share dtype/trailing shape.
- Pass `ndata=None` or `edata=None` when schema differs and features are not needed.
- Do not pass blocks to `dgl.batch`.

## Safe Local Smoke Check

From this sub-skill directory:

```bash
python scripts/graph_smoke.py
```

The script validates homogeneous graph construction, heterograph canonical edge handling, feature schemas, batching/unbatching, and a temporary save/load roundtrip without touching external repository files or user data.
