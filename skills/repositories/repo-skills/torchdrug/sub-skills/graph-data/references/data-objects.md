# Data Objects, Batching, Splits, and Datasets

This reference is for future agents that need to build or inspect TorchDrug data in memory without reopening source docs. Import the public surface with:

```python
import torch
from torchdrug import data, datasets
```

## Core Constructors

### `data.Graph`

Use `data.Graph(edge_list=None, edge_weight=None, num_node=None, num_relation=None, node_feature=None, edge_feature=None, graph_feature=None, **kwargs)` for generic sparse graphs.

- `edge_list` is shape `(num_edge, 2)` for ordinary directed edges `(source, target)` or `(num_edge, 3)` for relational edges `(source, target, relation)`.
- `edge_weight` is shape `(num_edge,)`; if omitted, TorchDrug uses ones.
- Always pass `num_node` when isolated nodes matter. If omitted, TorchDrug infers from the largest node id and can undercount isolated nodes.
- Pass `num_relation` with 3-column relation edge lists; all relation ids must be in `[0, num_relation)`.
- `node_feature`, `edge_feature`, and `graph_feature` are converted to tensors and registered under the right attribute scopes.

Example:

```python
edge_list = torch.tensor([[0, 1], [1, 2], [2, 0]])
node_feature = torch.eye(3)
graph = data.Graph(edge_list, num_node=3, node_feature=node_feature)
```

For relational graphs:

```python
triplets = torch.tensor([[0, 1, 0], [1, 2, 1], [2, 0, 0]])
graph = data.Graph(triplets, num_node=3, num_relation=2)
```

### `data.PackedGraph`

Prefer `data.Graph.pack([graph1, graph2, ...])` over manually constructing `PackedGraph`.

- A packed graph is one large disconnected graph with per-graph sizes in `num_nodes` and `num_edges`.
- `batch_size` is the number of graphs.
- `num_node` and `num_edge` are totals across the batch.
- `num_cum_nodes`, `num_cum_edges`, `node2graph`, and `edge2graph` help translate between per-graph and packed indexes.
- Use `packed.unpack()` or `packed[i]` to recover individual graphs.

### `data.Molecule` and `data.PackedMolecule`

Use `data.Molecule.from_smiles(smiles, atom_feature="default", bond_feature="default", mol_feature=None, with_hydrogen=False, kekulize=False)` for a single molecule.

Use `data.PackedMolecule.from_smiles(smiles_list, atom_feature="default", bond_feature="default", mol_feature=None, with_hydrogen=False, kekulize=False)` for a batch of SMILES.

- Molecules store each undirected chemical bond as two directed edges.
- `atom_feature="default"` creates `node_feature` / `atom_feature`; `bond_feature="default"` creates `edge_feature` / `bond_feature`.
- Set `mol_feature="ecfp"` when a graph-level ECFP fingerprint is needed.
- `with_hydrogen=True` explicitly includes hydrogens.
- `kekulize=True` changes aromatic relation handling in `edge_list`; `bond_type` still explicitly stores aromatic bonds.
- `to_smiles()`, `to_molecule()`, and `to_scaffold(chirality=False)` are useful validation and split helpers.

Example:

```python
mol = data.Molecule.from_smiles("c1ccccc1", mol_feature="ecfp")
assert mol.num_node == 6
assert mol.num_edge == 12
batch = data.PackedMolecule.from_smiles(["CCO", "c1ccccc1"])
assert batch.batch_size == 2
```

### `data.Protein` and `data.PackedProtein`

Use `data.Protein.from_sequence(sequence, atom_feature="default", bond_feature="default", residue_feature="default", mol_feature=None, kekulize=False)` for one protein sequence.

Use `data.PackedProtein.from_sequence(sequences, atom_feature="default", bond_feature="default", residue_feature="default", mol_feature=None, kekulize=False)` for a batch.

- Protein objects extend molecule graphs with residue fields and two views: `view="atom"` or `view="residue"`.
- `num_atom` / `num_node` count atoms; `num_residue` counts residues.
- `residue_feature` is scoped to residues, not atoms.
- For sequence-only work where atom bonds are unnecessary, pass `atom_feature=None, bond_feature=None, residue_feature="default"`; TorchDrug builds a residue-only object much faster.
- Unknown residue symbols are treated as glycine with a warning in residue-only construction.

Example:

```python
protein = data.Protein.from_sequence("GAS", atom_feature=None, bond_feature=None)
assert protein.num_residue == 3
packed = data.PackedProtein.from_sequence(["GAS", "MKT"], atom_feature=None, bond_feature=None)
assert packed.batch_size == 2
```

## Attribute Contexts and Length Rules

TorchDrug tracks attribute scopes through context managers so packing, masking, and device movement transform attributes correctly.

### Generic graphs

```python
with graph.node():
    graph.node_score = torch.ones(graph.num_node, 1)
with graph.edge():
    graph.edge_score = torch.ones(graph.num_edge, 1)
with graph.graph():
    graph.graph_label = torch.tensor([1.0])
```

Length rules:

- Node attributes must have first dimension `num_node`.
- Edge attributes must have first dimension `num_edge`.
- For a single `Graph`, graph attributes are scalar or shape `(feature_dim, ...)`; during packing, graph attributes are stacked to first dimension `batch_size`.
- For a `PackedGraph`, graph attributes must have first dimension `batch_size`.
- Reference contexts (`node_reference`, `edge_reference`, `graph_reference`) require `torch.long` tensors with valid ids or `-1`.

### Molecule aliases

Molecules expose chemistry aliases for the same scopes:

- `with mol.atom():` is the node scope.
- `with mol.bond():` is the edge scope.
- `with mol.mol():` is the graph scope.

Default SMILES construction adds common fields such as `atom_type`, `bond_type`, `formal_charge`, `explicit_hs`, `chiral_tag`, `bond_stereo`, and `stereo_atoms` under the correct scopes.

### Protein residue scope

Proteins add:

```python
with protein.residue():
    protein.residue_score = torch.ones(protein.num_residue, 1)
with protein.residue_reference():
    protein.residue_partner = torch.arange(protein.num_residue)
```

Residue attributes must have first dimension `num_residue`; residue references must be long tensors in `[-1, num_residue)`.

## Batching and Collation

### Manual packing

```python
graphs = [data.Graph([[0, 1]], num_node=2), data.Graph([[0, 1], [1, 2]], num_node=3)]
packed = data.Graph.pack(graphs)
assert packed.batch_size == 2
assert len(packed.unpack()) == 2
```

Use `data.PackedMolecule.from_smiles(smiles_list)` and `data.PackedProtein.from_sequence(sequences)` when the batch starts from strings.

### `graph_collate` and `DataLoader`

`data.graph_collate(batch)` recursively collates nested structures:

- Tensor values become stacked tensors.
- Numbers become tensors.
- Strings remain lists.
- `data.Graph` instances are packed.
- Dictionaries are collated by key.
- Sequences must have equal length.

Example for local samples:

```python
samples = [
    {"graph": data.Molecule.from_smiles("CCO"), "label": 0},
    {"graph": data.Molecule.from_smiles("CCN"), "label": 1},
]
batch = data.graph_collate(samples)
assert batch["graph"].batch_size == 2
assert batch["label"].shape == (2,)
```

`data.DataLoader(dataset, batch_size=..., shuffle=..., num_workers=...)` is a `torch.utils.data.DataLoader` with `graph_collate` as the default collate function.

## Masking, Indexing, and Unpacking

### Single graphs

- `graph.subgraph(nodes)` is equivalent to `graph.node_mask(nodes, compact=True)` and remaps node ids to a compact range.
- `graph.node_mask(nodes, compact=False)` keeps original node ids and preserves isolated positions.
- `graph.edge_mask(edges)` keeps selected edges and preserves node count.
- `graph.compact()` removes isolated nodes after masking.
- `graph[i, j]` returns edge weight for one edge; slices/lists over axes produce edge-masked graphs.

Example:

```python
graph = data.Graph([[0, 1], [1, 2], [2, 3]], num_node=4, node_feature=torch.eye(4))
sub = graph.subgraph([1, 2, 3])
assert sub.num_node == 3
edge_only = graph.edge_mask([0, 2])
assert edge_only.num_node == 4
assert edge_only.num_edge == 2
```

### Packed graphs

- `packed.node_mask(node_indexes, compact=False)` masks nodes across the flattened packed node ids.
- `packed.edge_mask(edge_indexes)` masks flattened packed edge ids.
- `packed.graph_mask(graph_indexes, compact=False)` keeps selected graphs but preserves batch slots unless compacted.
- `packed.subbatch(graph_indexes)` is `packed.graph_mask(graph_indexes, compact=True)`.
- `packed[i]` returns one unpacked graph; `packed[[2, 0]]` reorders and compacts a subbatch.
- To mask nodes for a particular graph in a batch, convert local ids to packed ids using `num_cum_nodes - num_nodes` for that graph.

Example local-to-packed node ids:

```python
local_nodes = torch.tensor([0, 2])
graph_id = 1
packed_nodes = local_nodes + packed.num_cum_nodes[graph_id] - packed.num_nodes[graph_id]
masked = packed.node_mask(packed_nodes, compact=True)
```

Protein packed objects add `residue_mask(index, compact=False)` and maintain residue fields in `graph_mask` / `subbatch`.

## Dataset Loading Patterns

TorchDrug dataset constructors usually accept a local `path`, `verbose=1`, and data-object keyword arguments such as `atom_feature`, `bond_feature`, `residue_feature`, `lazy`, or `transform` depending on dataset type. Most built-in datasets download or unpack files under `path`, so use them only when network and storage are allowed.

Common groups:

- Molecule datasets: `datasets.ClinTox(path, **kwargs)`, `Tox21`, `BBBP`, `BACE`, `HIV`, `QM8`, `QM9`, `ZINC250k`, `MOSES`, `PCQM4M`, and related property datasets.
- Protein datasets: `BetaLactamase`, `Fluorescence`, `Stability`, `Solubility`, `EnzymeCommission`, `GeneOntology`, `AlphaFoldDB`, and structure datasets.
- Pair or ligand datasets: `HumanPPI`, `YeastPPI`, `PPIAffinity`, `BindingDB`, `PDBBind`.
- Citation and node datasets: `Cora`, `CiteSeer`, `PubMed`.
- Knowledge graph datasets exist but task-specific KG guidance belongs in `../../knowledge-graphs/`.

### Build tiny local datasets without downloading

For local SMILES:

```python
smiles = ["CCO", "CCN", "c1ccccc1"]
targets = {"label": [0, 1, 0]}
dataset = data.MoleculeDataset()
dataset.load_smiles(smiles, targets, lazy=False)
item = dataset[0]
assert set(item) == {"graph", "label"}
```

For local protein sequences:

```python
sequences = ["GAS", "MKT"]
targets = {"score": [0.1, 0.2]}
dataset = data.ProteinDataset()
dataset.load_sequence(sequences, targets, lazy=True, atom_feature=None, bond_feature=None)
```

`transform` is called on each item after graph construction and target insertion. Return the same nested shape that the downstream loader expects.

### Lazy loading

- `lazy=False` constructs data objects during load and stores them in memory.
- `lazy=True` stores strings or paths and constructs graphs in `__getitem__`, saving initial memory and load time but slowing dataloader workers.
- Some cached properties such as `atom_types`, `bond_types`, and feature dimensions can become expensive or unavailable in lazy mode because they need to materialize graphs.
- In lazy molecule datasets, invalid SMILES may surface during item access rather than initial load.

## Split Helpers

### Random tensor split

For arbitrary datasets, `torch.utils.data.random_split(dataset, lengths)` works when chemistry-aware splits are not needed.

### `data.key_split(dataset, keys, lengths=None, key_lengths=None)`

Use `key_split` when samples with the same key must remain in the same split.

- `keys` must align one-to-one with `dataset`.
- `lengths` are desired sample counts; boundaries are rounded to avoid splitting a key group.
- Alternatively, use `key_lengths` to allocate by number of unique key groups.
- Returned values are `torch.utils.data.Subset` objects.

### `data.scaffold_split(dataset, lengths)`

Use for molecule datasets where Murcko scaffolds should not overlap across splits.

- Each dataset item must be a dict with `sample["graph"]` as a `Molecule` supporting `to_scaffold()`.
- `lengths` are expected counts, but exact split sizes may change because scaffold groups stay intact.
- This iterates over dataset samples and can materialize lazy molecules.

### `data.ordered_scaffold_split(dataset, lengths, chirality=True)`

Use for deterministic scaffold grouping based on `dataset.smiles_list`.

- Returns train, valid, and test subsets sorted by scaffold frequency.
- The implementation uses an 80/10/10 cutoff policy internally, so treat `lengths` as part of the public signature but do not rely on custom ratios here.
- Requires a molecule dataset with `smiles_list` populated.

For small local SMILES experiments, construct `MoleculeDataset`, call `load_smiles`, then use `scaffold_split` or `ordered_scaffold_split` only after filtering invalid SMILES.
