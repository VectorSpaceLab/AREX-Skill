# Core Data Formats

This reference describes the small data contracts used by the core `pahelix` APIs.

## `data_list` Records

`InMemoryDataset` manages a `data_list`: a Python list where every item is a dictionary. For NPZ cache compatibility, treat every dictionary as having the same keys and compatible value shapes.

Common record shapes:

```python
{
    "feature": np.array(...),
    "label": np.array(...),
}
```

```python
{
    "smiles": "CCO",
    "label": np.array([1], dtype="float32"),
}
```

Guidelines:

- Keep keys consistent across all records before calling `save_data_list_to_npz` or `InMemoryDataset.save_data`.
- Values that are arrays are concatenated across records and split back using sequence-length metadata.
- Scalar values are stored with `singular=1`; array-like values are stored with `singular=0`.
- Scaffold splitters require a string `smiles` key in every record.
- Featurizer transform functions may return `None` for invalid molecules; `InMemoryDataset.transform(..., drop_none=True)` can remove those failed records.

## NPZ Part Files

`save_data_list_to_npz(data_list, npz_file)` writes a compressed `.npz` file with three entries per logical key:

- `<key>`: concatenated values for all records.
- `<key>.seq_len`: sequence lengths for reconstructing each record.
- `<key>.singular`: `1` for scalar/singular values, `0` for sequence values.

`load_npz_to_data_list(npz_file)` reconstructs records by scanning all entries that do not end in `.seq_len` or `.singular`, then loading matching metadata entries.

Failure modes that indicate a cache-format problem:

- Missing `<key>.seq_len` or `<key>.singular` for a logical key.
- Different records have different keys, so save-time lookup fails or reload produces incomplete records.
- Non-concatenable arrays under the same key, such as incompatible trailing dimensions.
- Empty `data_list`; save-time code reads `data_list[0]` and cannot infer keys.
- Manually edited `.npz` files where metadata length does not match reconstructed records.

## `InMemoryDataset` Cache Directories

`InMemoryDataset.save_data(data_path)` writes files named like:

```text
part-000000.npz
part-000001.npz
```

The loader behavior is:

- `InMemoryDataset(npz_data_path=path)` reads all files ending in `.npz` from `path` in sorted order.
- `InMemoryDataset(npz_data_files=[file1, file2])` reads only the listed files in the provided order.
- `get_part_files(data_path, trainer_id, trainer_num)` shuffles the file list and returns files assigned to one trainer by modulo; seed the Python `random` module externally if deterministic partitioning is required.

## Splitter Expectations

All splitters expect a list-like dataset that supports `len(dataset)` and `dataset[index_or_indices]`. PaddleHelix `InMemoryDataset` satisfies this contract for Python lists of indices, slices, and integer indices; convert NumPy index arrays with `.tolist()` before indexing it directly.

Fraction rules:

- `frac_train + frac_valid + frac_test` must equal `1.0` within NumPy assertion tolerance.
- Cutoffs are integer/floor-style, so very small datasets can produce empty splits.
- Use explicit seeds for reproducible `RandomSplitter` and `RandomScaffoldSplitter` behavior.

Scaffold splitter rules:

- Requires RDKit import support.
- Requires every record to contain `smiles`.
- `ScaffoldSplitter` is deterministic after scaffold generation and sorts scaffold groups largest-first.
- `RandomScaffoldSplitter` randomizes scaffold groups and fills valid/test target counts before train.
- Invalid SMILES can fail during RDKit scaffold generation; validate SMILES first for user-facing workflows.

## Protein Token IDs

`ProteinTokenizer` uses a fixed vocabulary.

Special tokens:

| Token | ID |
| --- | ---: |
| `<pad>` | 0 |
| `<mask>` | 1 |
| `<cls>` | 2 |
| `<sep>` | 3 |
| `<unk>` | 4 |

Residue IDs:

| Token | ID | Token | ID | Token | ID |
| --- | ---: | --- | ---: | --- | ---: |
| `A` | 5 | `B` | 6 | `C` | 7 |
| `D` | 8 | `E` | 9 | `F` | 10 |
| `G` | 11 | `H` | 12 | `I` | 13 |
| `K` | 14 | `L` | 15 | `M` | 16 |
| `N` | 17 | `O` | 18 | `P` | 19 |
| `Q` | 20 | `R` | 21 | `S` | 22 |
| `T` | 23 | `U` | 24 | `V` | 25 |
| `W` | 26 | `X` | 27 | `Y` | 28 |
| `Z` | 29 |  |  |  |  |

`gen_token_ids("ACD")` yields IDs for `<cls>`, `A`, `C`, `D`, `<sep>`. Lowercase or punctuation map to `<unk>` unless normalized upstream.

## Molecular Graph Dictionaries

`mol_to_graph_data(mol)` emits a dictionary suitable for PGL graph construction by PaddleHelix collate functions.

Core keys:

- Atom categorical arrays: `atomic_num`, `chiral_tag`, `degree`, `explicit_valence`, `formal_charge`, `hybridization`, `implicit_valence`, `is_aromatic`, `total_numHs`.
- Atom float array: `mass`.
- Edge index array: `edges`, shaped like `(edge_count, 2)`, with both bond directions plus self-loops.
- Bond arrays: `bond_dir`, `bond_type`, `is_in_ring`.
- Fingerprints/groups: `morgan_fp`, `maccs_fp`, `daylight_fg_counts`.

Feature ID conventions:

- Most categorical atom/bond IDs are offset by `+1`; `0` is reserved for out-of-vocabulary/mask.
- Self-loop bond feature IDs use `feature_size + 2` in `mol_to_graph_data`.
- Molecules with no bonds get empty `edges` and bond arrays.
- Molecules with dummy atoms or zero atoms can return `None`.

## GeoGNN Graph Dictionaries

`mol_to_geognn_graph_data(mol, atom_poses, dir_type)` starts from `mol_to_graph_data` and adds geometry fields:

- `atom_pos`: `float32` atom coordinates.
- `bond_length`: length for each graph edge.
- `BondAngleGraph_edges`: superedge graph between directed bond edges.
- `bond_angle`: angle features for the bond-angle graph.

Convenience helpers:

- `mol_to_geognn_graph_data_MMFF3d(mol)` builds MMFF poses for molecules with at most 400 atoms, otherwise falls back to 2D poses.
- `mol_to_geognn_graph_data_raw3d(mol)` uses an existing conformer from the RDKit molecule.

## Featurizer Batch Contracts

- `AttrmaskTransformFn` expects raw records with `smiles` and returns `mol_to_graph_data` output or `None`.
- `SupervisedTransformFn` expects raw records with `smiles` and `label`, returns graph data plus flattened `label`.
- `AttrmaskCollateFn` and `SupervisedCollateFn` expect graph dictionaries and build batched PGL graphs.
- `GeoPredTransformFn` accepts a raw SMILES string and returns GeoGNN graph data plus pretraining task keys.
- `GeoPredCollateFn` expects GeoGNN dictionaries and returns `(graph_dict, feed_dict)` for GEM pretraining.

## Evidence Labels

- `pahelix/datasets/inmemory_dataset.py`
- `pahelix/utils/data_utils.py`
- `pahelix/utils/protein_tools.py`
- `pahelix/utils/splitters.py`
- `pahelix/utils/compound_tools.py`
- `pahelix/featurizers/pretrain_gnn_featurizer.py`
- `pahelix/featurizers/gem_featurizer.py`
