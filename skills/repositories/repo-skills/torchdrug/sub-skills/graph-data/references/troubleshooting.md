# Graph Data Troubleshooting

## Invalid SMILES or RDKit Construction Failures

Symptoms:

- `ValueError: Invalid SMILES ...` from `data.Molecule.from_smiles` or `data.PackedMolecule.from_smiles`.
- Dataset load silently skips rows at debug logging level because `Chem.MolFromSmiles(smiles)` returned `None`.
- `to_molecule()` or `to_smiles()` fails after aggressive masking or editing.

Checks and fixes:

- Validate each SMILES before batching; one bad string fails `PackedMolecule.from_smiles` for the whole list.
- Empty SMILES `""` is a valid side case and creates a molecule with zero nodes and zero edges.
- Keep `kekulize=False` unless a downstream method needs explicit single/double aromatic relations.
- If masks are applied to molecules with stereo bonds, clear or re-check stereo metadata before converting back to RDKit objects; TorchDrug warns that masking stereo molecules may produce invalid molecules.
- Use `mol.to_molecule(ignore_error=True)` or `packed.to_molecule(ignore_error=True)` when inspecting generated or edited molecules and you prefer `None` over an exception.
- If RDKit itself cannot import, run `scripts/smoke_graph_data.py --skip-rdkit` to isolate generic graph behavior from chemistry dependencies.

## Attribute Length or Scope Errors

Symptoms:

- `ValueError: Expect node attribute ... to have shape (num_node, *)`.
- `ValueError: Expect edge attribute ... to have shape (num_edge, *)`.
- `ValueError: Expect graph attribute ... to have shape (batch_size, *)` on packed graphs.
- Masking, packing, or subgraph extraction drops or misaligns a custom field.

Checks and fixes:

- Assign attributes inside the correct context manager. Use `with graph.node():`, `with graph.edge():`, `with graph.graph():`; for molecules use `atom()`, `bond()`, `mol()`; for proteins also use `residue()`.
- The first dimension must match the component count: `num_node`, `num_edge`, `num_residue`, or packed `batch_size` for graph attributes.
- For a single `Graph`, graph-level attributes are unsqueezed during packing. For an already packed graph, assign one row per graph.
- Reference attributes must be `torch.long` and use valid ids or `-1` for missing references.
- If you need an edge attribute for all edges in a molecule, remember undirected bonds are stored twice, so the edge/bond attribute first dimension is `num_edge`, not the number of RDKit bonds.
- When a custom edge attribute breaks after `edge_mask`, verify that it was registered under `edge()` / `bond()` before masking; unregistered Python attributes are not automatically sliced.

## Edge Lists, Counts, and Relation Errors

Symptoms:

- `edge_list should only contain non-negative indexes`.
- `num_node is ... but found node ... in edge_list`.
- `num_relation is ... but found relation ... in edge_list`.
- Unexpected missing isolated nodes.

Checks and fixes:

- Use zero-based, non-negative node ids.
- Pass `num_node` explicitly whenever isolated nodes should exist.
- For relational graphs, provide a 3-column edge list and set `num_relation` larger than the maximum relation id.
- Keep `edge_weight` length equal to `edge_list` length.
- For dense adjacency conversion, use the public constructor appropriate for the adjacency rank: 2D for ordinary graphs, 3D for relation graphs.

## Packed Indexing and Masking Surprises

Symptoms:

- Masking a packed graph changes the wrong graph.
- `node_mask` preserves empty graph slots when the expected result was a smaller batch.
- `unpack_data(..., type="auto")` reports ambiguous node/edge data.

Checks and fixes:

- Packed node and edge masks use flattened ids across the whole batch. Convert local node ids to packed ids with `local + packed.num_cum_nodes[i] - packed.num_nodes[i]`.
- Use `packed.subbatch(indexes)` when selecting graphs and expecting compact graph ids and a smaller `batch_size`.
- `packed.graph_mask(indexes, compact=False)` preserves original batch slots with zero sizes for unselected graphs.
- Specify `type="node"` or `type="edge"` in `unpack_data` when `num_node == num_edge` or when the data length is otherwise ambiguous.

## CPU, CUDA, and Device Movement

Symptoms:

- Tensor device mismatch errors in models or transforms.
- Code calls `.cuda()` on a machine without CUDA.
- Nested graph batches have tensors on mixed devices.

Checks and fixes:

- TorchDrug data objects support `.cuda()`, `.cpu()`, and `.to(device)` like PyTorch tensors; these move registered attributes and cached graph tensors.
- Guard CUDA usage with `torch.cuda.is_available()` and prefer `graph.to(device)` when the device is dynamic.
- Move the whole nested batch returned by `graph_collate` or `DataLoader` consistently before passing it to models or tasks.
- Avoid keeping side tensors outside registered contexts unless you move them manually.
- TorchDrug 0.2.1 targets CUDA/PyTorch tensor backends; do not assume Apple MPS support for graph operations.

## Dataset Download, Network, and Filesystem Problems

Symptoms:

- Built-in dataset constructors fail with download errors, missing archives, or permission issues.
- Dataset initialization is slow or writes unexpectedly under the chosen path.
- File-backed protein/ligand datasets fail on missing PDB, LMDB, or CSV fields.

Checks and fixes:

- Built-in `torchdrug.datasets.*` constructors typically download, extract, or cache files under the `path` argument. Confirm network and write permissions before using them.
- For no-network tests, use `data.MoleculeDataset().load_smiles(...)` or `data.ProteinDataset().load_sequence(...)` with tiny local lists.
- Set `verbose=0` in automated scripts if progress bars are noisy.
- Check dataset-specific constructor arguments: some molecule datasets accept `node_position`; protein datasets may accept `test_cutoff`, `branch`, `species_id`, or split selectors.
- If a constructor forwards `**kwargs`, those usually go to `Molecule.from_smiles`, `Protein.from_sequence`, or related loaders, so use feature options there.

## Split Length and Grouping Mistakes

Symptoms:

- Split sizes differ from requested lengths.
- Scaffold splits produce very imbalanced train/valid/test subsets.
- `key_split` groups appear in multiple splits.
- `ordered_scaffold_split` ignores custom-looking length ratios.

Checks and fixes:

- `key_split` rounds boundaries to avoid splitting identical keys. Exact sample counts are not guaranteed.
- `scaffold_split` groups by `sample["graph"].to_scaffold()` and also rounds by scaffold group.
- `ordered_scaffold_split` groups by `dataset.smiles_list` and uses an internal 80/10/10 train/valid/test cutoff policy. Use it only when that policy is acceptable.
- Ensure `keys` length equals `len(dataset)` for `key_split`.
- Ensure split lengths are non-negative and sum to the dataset size for ordinary PyTorch `random_split`; TorchDrug scaffold helpers expect desired counts but may return adjusted sizes.
- Invalid SMILES removed during `load_smiles` change `len(dataset)`, so compute split lengths after loading and filtering.

## Lazy Loading Memory and Performance

Symptoms:

- Dataset loads quickly but each dataloader step is slow.
- Feature-dimension or type queries warn or take a long time.
- Invalid input appears only during iteration.

Checks and fixes:

- `lazy=True` delays molecule/protein construction to `__getitem__`; it saves CPU memory and initial loading time but shifts cost to dataloader workers.
- Avoid querying expensive cached properties such as atom and bond type sets on large lazy datasets unless needed.
- When a model needs `dataset.node_feature_dim` or `edge_feature_dim`, make sure at least the first stored graph exists and has the feature generated. Some lazy flows keep only the first graph materialized.
- Use `lazy=False` for small datasets, debugging, split validation, and smoke tests.
- Use `lazy=True` for very large SMILES/sequence collections after basic validity checks.
