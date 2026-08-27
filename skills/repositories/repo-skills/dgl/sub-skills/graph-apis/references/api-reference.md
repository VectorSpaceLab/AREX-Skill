# Graph API Reference

This reference covers DGL graph construction and structural manipulation APIs for homogeneous graphs, heterogeneous graphs, feature frames, conversions, blocks, batching, and subgraphs.

## Constructors

### `dgl.graph`

Verified signature:

```python
dgl.graph(data, *, num_nodes=None, idtype=None, device=None, row_sorted=False, col_sorted=False)
```

Use for homogeneous graphs with one node type and one edge type.

- `data` is usually `(src, dst)`, where `src[i] -> dst[i]` creates edge ID `i`.
- `data` may also be `('coo', (src, dst))`, `('csr', (indptr, indices, eids))`, or `('csc', (indptr, indices, eids))`.
- `num_nodes` is required when the largest node ID is isolated or when the graph intentionally has more nodes than the maximum ID in edges.
- `idtype` must be a backend integer dtype, typically `torch.int32` or `torch.int64`.
- `device` may be a backend device, typically `torch.device('cpu')` or `torch.device('cuda:0')`; if omitted, DGL infers it from tensor inputs or uses CPU for Python sequences.
- `row_sorted=True` and `col_sorted=True` are hints for sorted COO inputs; leave them false unless the input order is known.

Minimal pattern:

```python
import dgl
import torch

src = torch.tensor([0, 0, 1], dtype=torch.int64)
dst = torch.tensor([1, 2, 2], dtype=torch.int64)
g = dgl.graph((src, dst), num_nodes=4, idtype=torch.int64, device=torch.device('cpu'))
```

### `dgl.heterograph`

Verified signature:

```python
dgl.heterograph(data_dict, num_nodes_dict=None, idtype=None, device=None)
```

Use for graphs with multiple node types, edge types, or relations.

- `data_dict` maps canonical edge types `(src_type, edge_type, dst_type)` to graph data such as `(src_ids, dst_ids)`.
- Each node type has its own ID space. `user` node `0` and `item` node `0` are different entities.
- `num_nodes_dict` is required for node types with isolated nodes or for types that do not appear in any edge endpoint.
- `idtype` and `device` follow the same rules as `dgl.graph`.
- A relation name may appear in multiple canonical edge types. In that case, use the full triplet in APIs that accept `etype`.

Minimal pattern:

```python
hg = dgl.heterograph(
    {
        ('user', 'rates', 'movie'): (torch.tensor([0, 1]), torch.tensor([1, 0])),
        ('critic', 'rates', 'movie'): (torch.tensor([0]), torch.tensor([1])),
    },
    num_nodes_dict={'user': 2, 'critic': 1, 'movie': 2},
)
```

## DGLGraph Object Model

`dgl.graph` and `dgl.heterograph` both return `DGLGraph` objects. A homogeneous graph is represented internally as a one-relation heterograph.

| Concept | Homogeneous graph | Heterogeneous graph |
| --- | --- | --- |
| Node types | `g.ntypes == ['_N']` by default | `g.ntypes` lists all node type names |
| Edge type names | `g.etypes == ['_E']` by default | `g.etypes` may contain duplicate names |
| Canonical edge types | `g.canonical_etypes == [('_N', '_E', '_N')]` | Triplets such as `('user', 'rates', 'movie')` |
| Feature views | `g.ndata['x']`, `g.edata['w']` | `g.nodes['user'].data['x']`, `g.edges[c_etype].data['w']` |
| ID spaces | One node ID space, one edge ID space | Separate node ID spaces per node type; separate edge IDs per canonical edge type |

Useful structural attributes and methods:

- `g.ntypes`, `g.etypes`, `g.canonical_etypes`: inspect schema.
- `g.is_homogeneous`, `g.is_multigraph`, `g.is_block`, `g.is_unibipartite`: inspect graph category.
- `g.num_nodes(ntype=None)` and `g.number_of_nodes(ntype=None)`: node counts.
- `g.num_edges(etype=None)` and `g.number_of_edges(etype=None)`: edge counts.
- `g.nodes(ntype=None)`: node IDs for one node type; `ntype` is required when multiple node types exist.
- `g.edges(form='uv', order='eid', etype=None)`: edge endpoint tensors, edge IDs, or all three for one edge type.
- `g.in_edges(nodes, form='uv', etype=None)` and `g.out_edges(nodes, form='uv', etype=None)`: incident edges.
- `g.predecessors(v, etype=None)` and `g.successors(v, etype=None)`: one-hop neighbor IDs.
- `g.find_edges(eids, etype=None)`: map edge IDs back to endpoints.
- `g.idtype`, `g.device`: graph structure dtype and device.
- `g.int()` and `g.long()`: clone/cast graph structure IDs to int32 or int64.
- `g.to(device)`: clone/move graph structure and feature frames to another device.
- `g.formats()` or `g.formats('csr')`: inspect or restrict internal sparse formats.

## Feature APIs

For homogeneous graphs:

```python
g.ndata['feat'] = torch.randn(g.num_nodes(), 16)
g.edata['weight'] = torch.ones(g.num_edges(), 1)
```

For heterogeneous graphs:

```python
hg.nodes['user'].data['feat'] = torch.randn(hg.num_nodes('user'), 16)
hg.edges[('user', 'rates', 'movie')].data['score'] = torch.ones(
    hg.num_edges(('user', 'rates', 'movie')), 1
)
```

Feature rules:

- The leading dimension must equal the number of nodes or edges for that type.
- Features must be numeric tensors.
- Features attached to the same name must have compatible shape and dtype when DGL concatenates them, such as in `dgl.batch(..., ndata='__ALL__')` or `dgl.to_homogeneous(..., ndata=['feat'])`.
- Feature tensors must live on the same device as the graph when assigned.
- In a heterograph, `g.ndata['feat']` returns a dictionary keyed by node type when multiple node types have that feature; `g.edata['feat']` returns a dictionary keyed by canonical edge type.

## Canonical Edge Types

A canonical edge type is `(source_node_type, edge_type_name, destination_node_type)`.

Use full canonical triplets whenever:

- The same edge type string appears more than once in `g.etypes`.
- A DGL error says the edge type is ambiguous or must be specified.
- You set/read edge features on a heterograph with repeated relation names.
- You call `g.num_edges`, `g.edges`, `g.in_edges`, `g.out_edges`, `g.find_edges`, `dgl.edge_subgraph`, or `dgl.to_block` on relation-specific data.

Safe helper pattern:

```python
rates_user_movie = ('user', 'rates', 'movie')
assert rates_user_movie in hg.canonical_etypes
src, dst, eid = hg.edges(form='all', etype=rates_user_movie)
```

## Structural Mutation APIs

Common in-place mutation methods:

```python
g.add_nodes(num, data=None, ntype=None)
g.add_edges(u, v, data=None, etype=None)
g.remove_nodes(nids, ntype=None, store_ids=False)
g.remove_edges(eids, etype=None, store_ids=False)
```

Rules:

- For heterographs with multiple node or edge types, specify `ntype` or a canonical `etype` where required.
- `add_edges` will add missing endpoint nodes for the selected relation if IDs exceed the current type-local node count.
- `data` must match the number of newly added nodes or edges and follow the same feature device rules as `ndata` and `edata`.
- Removing nodes also removes incident edges and reindexes remaining nodes/edges for that type.
- Removing nodes or edges preserves batch metadata; deterministic subgraph extraction does not.
- Use immutable construction plus subgraph/transform APIs when reproducibility matters more than in-place edits.

## Conversion APIs

Verified signatures:

```python
dgl.to_homogeneous(G, ndata=None, edata=None, store_type=True, return_count=False)
dgl.to_heterogeneous(G, ntypes, etypes, ntype_field='_TYPE', etype_field='_TYPE', metagraph=None)
```

`dgl.to_homogeneous` merges node and edge type ID spaces into one graph.

- By default, it stores original node type IDs in `hg.ndata[dgl.NTYPE]` and edge type IDs in `hg.edata[dgl.ETYPE]`.
- It also stores type-local original node IDs in `hg.ndata[dgl.NID]` and edge IDs in `hg.edata[dgl.EID]`.
- `ndata` and `edata` list feature names to concatenate across all node or edge types. Every selected feature must have the same shape and dtype across types.
- `store_type=False` avoids storing type tensors when not needed.
- `return_count=True` returns per-type counts in addition to the homogeneous graph.

`dgl.to_heterogeneous` reconstructs a heterograph from a homogeneous graph with stored type fields.

- `ntypes` and `etypes` are type-name lists used to decode integer type IDs.
- If two relations share the same edge type ID but have different source/destination node type IDs, DGL can split them into distinct canonical edge types.
- It copies non-reserved node and edge features back into type-specific feature frames.

## Block API

Verified signature:

```python
dgl.to_block(g, dst_nodes=None, include_dst_in_src=True, src_nodes=None)
```

Use `to_block` for a small, explicit bipartite message-flow graph when you already know destination nodes. For full neighbor sampling and minibatch dataloading, route to [dataloading-graphbolt](../../dataloading-graphbolt/SKILL.md).

- A block has source-side and destination-side node sets.
- If `dst_nodes` is a tensor, the graph must have one node type.
- If `dst_nodes` is a dictionary, keys are destination node types.
- `dst_nodes` must include every node with an inbound edge included by the conversion.
- `include_dst_in_src=True` prefixes destination nodes in the source node set.
- Original node and edge IDs are stored under `dgl.NID` and `dgl.EID`.
- Use `block.srcdata`, `block.dstdata`, `block.srcnodes[...]`, and `block.dstnodes[...]` for source/destination feature views.

## Batching APIs

Verified signatures:

```python
dgl.batch(graphs, ndata='__ALL__', edata='__ALL__')
dgl.unbatch(g, node_split=None, edge_split=None)
```

`dgl.batch` forms a disjoint union of graphs.

- Input list must be non-empty.
- Heterograph inputs must share the same node types and canonical edge types.
- Batched graphs preserve per-component counts in `bg.batch_num_nodes()` and `bg.batch_num_edges()`.
- Feature batching concatenates selected node/edge features along dimension 0.
- Pass `ndata=None` or `edata=None` to skip feature batching.
- Pass `ndata=['feat']` or `edata=['weight']` to batch only selected feature keys.
- Blocks/message-flow graphs are not supported by `dgl.batch`.

`dgl.unbatch` splits a batched graph back into a list.

- Without split arguments, DGL uses stored batch counts.
- For heterographs, custom `node_split` and `edge_split` must be dictionaries covering every node type and canonical edge type.
- All split lists must describe the same number of output graphs.

## Serialization APIs Used for Smoke Checks

Verified signatures:

```python
dgl.save_graphs(filename, g_list, labels=None, formats=None)
dgl.load_graphs(filename, idx_list=None)
```

Use these here only for tiny local roundtrip checks, such as `scripts/graph_smoke.py`. For dataset layout, caching, labels, production graph persistence, and CSV/custom dataset flows, route to [datasets-and-io](../../datasets-and-io/SKILL.md).

## Subgraph and Transform Basics

Common deterministic subgraph APIs:

- `dgl.node_subgraph(graph, nodes, relabel_nodes=True, store_ids=True, output_device=None)` extracts an induced node subgraph.
- `dgl.edge_subgraph(graph, edges, relabel_nodes=True, store_ids=True, output_device=None)` extracts an edge-induced subgraph.
- `dgl.in_subgraph(graph, nodes, relabel_nodes=False, store_ids=True, output_device=None)` keeps inbound edges to nodes.
- `dgl.out_subgraph(graph, nodes, relabel_nodes=False, store_ids=True, output_device=None)` keeps outbound edges from nodes.
- `dgl.node_type_subgraph(graph, ntypes)` and `dgl.edge_type_subgraph(graph, etypes)` retain selected types.

Subgraph rules:

- For homogeneous graphs, node and edge selections can be tensors, Python iterables, or boolean masks.
- For heterographs, selections must be dictionaries keyed by node type or canonical edge type.
- `store_ids=True` stores original IDs under `dgl.NID` and `dgl.EID`.
- Subgraph feature copies are lazy; data movement happens when features are accessed.
- Subgraph extraction discards batch metadata; restore it manually with `set_batch_num_nodes` and `set_batch_num_edges` if needed.

Common lightweight transforms:

- `dgl.add_self_loop(g)` and `dgl.remove_self_loop(g)` adjust self-loop structure for homogeneous or selected relation contexts.
- `dgl.add_reverse_edges(g, copy_ndata=False, copy_edata=False, ignore_bipartite=False)` adds reverse edges.
- `dgl.to_bidirected(g, copy_ndata=False)` creates a graph with both directions.
- `dgl.reverse(g, copy_ndata=True, copy_edata=False)` reverses edge directions.
- `dgl.to_simple(g, copy_ndata=True, copy_edata=False, return_counts='count')` collapses parallel edges.

Check each transform's copy flags before assuming feature propagation.
