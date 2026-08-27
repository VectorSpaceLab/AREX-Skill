# Core API Reference

This reference summarizes reusable `pahelix` package APIs from the source modules and API docs. It is intended for future agents that need the contract without reopening source files.

## Import Layers

- Dependency-light: `pahelix`, `pahelix.utils.data_utils`, and `pahelix.utils.protein_tools` import with NumPy/scikit-learn-style base dependencies.
- PGL-dependent: `pahelix.datasets.inmemory_dataset`, splitter tests that use `InMemoryDataset`, most featurizers, and graph dataloaders import `pgl`.
- RDKit-dependent: `pahelix.utils.splitters` imports RDKit scaffold utilities; `pahelix.utils.compound_tools` imports RDKit chemistry APIs.
- Paddle-dependent: `pahelix.model_zoo.*` and neural network modules import `paddle`, often also `pgl`.

## Dataset and NPZ APIs

### `InMemoryDataset`

Module: `pahelix.datasets.inmemory_dataset`

```python
InMemoryDataset(data_list=None, npz_data_path=None, npz_data_files=None)
```

- `data_list`: list of record dictionaries, usually dictionaries of NumPy arrays or small scalar/string metadata.
- `npz_data_path`: directory containing sorted `*.npz` part files created by `save_data` or `save_data_list_to_npz`.
- `npz_data_files`: explicit ordered file list to load.
- `__getitem__(int)`: returns one record dictionary.
- `__getitem__(slice)` / `__getitem__(list)`: returns a new `InMemoryDataset` with selected records. NumPy index arrays are not accepted by the source implementation; convert them to Python lists first.
- `__len__()`: returns record count.
- `save_data(data_path)`: writes `part-%06d.npz` files with default 10,000 records per part.
- `transform(transform_fn, num_workers=4, drop_none=False)`: applies a function through `pahelix.utils.basic_utils.mp_pool_map`; with `drop_none=True`, removes failed transforms.
- `get_data_loader(batch_size, num_workers=4, shuffle=False, collate_fn=None)`: returns `pgl.utils.data.Dataloader` and therefore requires PGL.

### NPZ helpers

Module: `pahelix.utils.data_utils`

```python
save_data_list_to_npz(data_list, npz_file)
load_npz_to_data_list(npz_file)
get_part_files(data_path, trainer_id, trainer_num)
```

- `save_data_list_to_npz` writes compressed arrays plus per-key metadata fields `<key>.seq_len` and `<key>.singular`.
- `load_npz_to_data_list` reconstructs a list of record dictionaries from those metadata fields.
- `get_part_files` shuffles file names in `data_path` and returns files where `index % trainer_num == trainer_id`.

## Protein Tokenizer

Module: `pahelix.utils.protein_tools`

```python
tokenizer = ProteinTokenizer()
tokens = tokenizer.tokenize(sequence)
ids = tokenizer.convert_tokens_to_ids(tokens)
ids_with_bounds = tokenizer.gen_token_ids(sequence)
```

- `tokenize(sequence)` splits a sequence string into one-character residue tokens.
- `convert_token_to_id(token)` returns the vocabulary ID or `<unk>` ID for unknown tokens.
- `convert_tokens_to_ids(tokens)` maps token lists to IDs.
- `gen_token_ids(sequence)` prepends `<cls>` and appends `<sep>` before ID conversion.
- Special token IDs: `<pad>=0`, `<mask>=1`, `<cls>=2`, `<sep>=3`, `<unk>=4`.
- Residue token IDs include `A=5`, `B=6`, `C=7`, ..., `Z=29`; unsupported characters map to `4`.

## Splitters

Module: `pahelix.utils.splitters`

```python
RandomSplitter().split(dataset, frac_train=None, frac_valid=None, frac_test=None, seed=None)
IndexSplitter().split(dataset, frac_train=None, frac_valid=None, frac_test=None)
ScaffoldSplitter().split(dataset, frac_train=None, frac_valid=None, frac_test=None)
RandomScaffoldSplitter().split(dataset, frac_train=None, frac_valid=None, frac_test=None, seed=None)
generate_scaffold(smiles, include_chirality=False)
```

- All splitters assert `frac_train + frac_valid + frac_test == 1.0` using NumPy testing.
- `RandomSplitter` shuffles indices with `np.random.RandomState(seed)` and slices by integer cutoffs.
- `IndexSplitter` keeps the original dataset order and slices by integer cutoffs.
- `ScaffoldSplitter` groups `dataset[i]['smiles']` by Bemis-Murcko scaffold with chirality enabled, sorts scaffold groups largest-first, and assigns groups to train/valid/test.
- `RandomScaffoldSplitter` groups by scaffold, random-permutes scaffold groups, fills valid and test target counts first, and assigns the rest to train.
- Scaffold splitters require RDKit and a valid `smiles` key in every record. The current source imports RDKit at module import time, so even `RandomSplitter`/`IndexSplitter` from this module need RDKit available unless a caller reimplements those simple splitters separately.

## Compound Utility APIs

Module: `pahelix.utils.compound_tools`

### General helpers

```python
get_gasteiger_partial_charges(mol, n_iter=12)
create_standardized_mol_id(smiles)
check_smiles_validity(smiles)
split_rdkit_mol_obj(mol)
get_largest_mol(mol_list)
rdchem_enum_to_list(values)
safe_index(alist, elem)
get_atom_feature_dims(list_acquired_feature_names)
get_bond_feature_dims(list_acquired_feature_names)
```

- Inputs are RDKit `Mol` objects or SMILES strings unless otherwise stated.
- `check_smiles_validity` returns `False` if RDKit cannot parse the SMILES.
- `safe_index` returns the final vocabulary index for out-of-vocabulary values.

### `CompoundKit`

Important static methods:

```python
CompoundKit.get_atom_value(atom, name)
CompoundKit.get_atom_feature_id(atom, name)
CompoundKit.get_atom_feature_size(name)
CompoundKit.get_bond_value(bond, name)
CompoundKit.get_bond_feature_id(bond, name)
CompoundKit.get_bond_feature_size(name)
CompoundKit.get_morgan_fingerprint(mol, radius=2)
CompoundKit.get_morgan2048_fingerprint(mol, radius=2)
CompoundKit.get_maccs_fingerprint(mol)
CompoundKit.get_daylight_functional_group_counts(mol)
CompoundKit.get_ring_size(mol)
CompoundKit.atom_to_feat_vector(atom)
CompoundKit.get_atom_names(mol)
```

- Atom categorical names include `atomic_num`, `chiral_tag`, `degree`, `explicit_valence`, `formal_charge`, `hybridization`, `implicit_valence`, `is_aromatic`, `total_numHs`, `num_radical_e`, `atom_is_in_ring`, `valence_out_shell`, and ring-count names.
- Atom float names are `van_der_waals_radis`, `partial_charge`, and `mass`.
- Bond categorical names include `bond_dir`, `bond_type`, `is_in_ring`, `bond_stereo`, and `is_conjugated`.
- Fingerprint lengths: Morgan `200`, Morgan2048 `2048`, MACCS `167`.

### `Compound3DKit`

Important static methods:

```python
Compound3DKit.get_atom_poses(mol, conf)
Compound3DKit.get_MMFF_atom_poses(mol, numConfs=None, return_energy=False)
Compound3DKit.get_2d_atom_poses(mol)
Compound3DKit.get_bond_lengths(edges, atom_poses)
Compound3DKit.get_superedge_angles(edges, atom_poses, dir_type='HT')
```

- `get_MMFF_atom_poses` attempts hydrogen addition, conformer generation, MMFF optimization, and returns atom positions; when `return_energy=True`, it also returns energy.
- `get_2d_atom_poses` computes 2D coordinates as a fallback.
- Bond lengths and superedge angles expect graph `edges` plus `atom_poses` arrays.

### Graph conversion helpers

```python
mol_to_graph_data(mol)
mol_to_geognn_graph_data(mol, atom_poses, dir_type)
mol_to_geognn_graph_data_MMFF3d(mol)
mol_to_geognn_graph_data_raw3d(mol)
```

- `mol_to_graph_data` returns `None` for empty molecules or molecules with dummy atoms.
- It emits atom feature arrays, directed bond edges, self-loop edges, bond feature arrays, `morgan_fp`, `maccs_fp`, and `daylight_fg_counts`; the source implementation does not emit an `atom_count` key.
- `mol_to_geognn_graph_data` adds `atom_pos`, `bond_length`, `BondAngleGraph_edges`, and `bond_angle`.
- `mol_to_geognn_graph_data_MMFF3d` uses MMFF poses for molecules with at most 400 atoms, otherwise 2D poses.
- `mol_to_geognn_graph_data_raw3d` uses an existing conformer from the RDKit molecule.

## Featurizer Orientation

Module family: `pahelix.featurizers`

```python
AttrmaskTransformFn()
AttrmaskCollateFn(atom_names, bond_names, mask_ratio=0.15)
SupervisedTransformFn()
SupervisedCollateFn(atom_names, bond_names)
GeoPredTransformFn(pretrain_tasks, mask_ratio)
GeoPredCollateFn(atom_names, bond_names, bond_float_names, bond_angle_float_names, pretrain_tasks, mask_ratio, Cm_vocab)
LiteGEMTransformFn(config)
LiteGEMCollateFn()
DDiFeaturizer()
```

- Pretrain GNN transform functions convert raw SMILES records into graph dictionaries; collate functions build PGL graph batches and labels.
- GEM transform/collate functions create geometry pretraining feeds keyed by tasks such as `Cm`, `Fg`, `Bar`, `Blr`, and `Adc`.
- LiteGEM and heterogeneous/DDI featurizers are orientation points; route end-to-end workflows to the app-specific sub-skills.

## Model-Zoo Orientation

Module family: `pahelix.model_zoo`

### Compound graph models

```python
PretrainGNNModel(model_config={})
AttrmaskModel(model_config, compound_encoder)
SupervisedModel(model_config, compound_encoder)
GeoGNNModel(model_config={})
GeoPredModel(model_config, compound_encoder)
LiteGEM(config, with_efeat=True)
```

- `PretrainGNNModel` expects `model_config['atom_names']` and `model_config['bond_names']` plus optional `embed_dim`, `dropout_rate`, `norm_type`, `graph_norm`, `residual`, `layer_num`, `gnn_type`, `JK`, and `readout`.
- `GeoGNNModel` expects `atom_names`, `bond_names`, `bond_float_names`, and `bond_angle_float_names` with optional `embed_dim`, `dropout_rate`, `layer_num`, and `readout`.
- These classes require Paddle and PGL and are not safe import checks in a minimal environment.

### Protein sequence models

```python
LstmEncoderModel(vocab_size, emb_dim=128, hidden_size=1024, n_layers=3, padding_idx=0, epsilon=1e-5, dropout_rate=0.1)
ResnetEncoderModel(vocab_size, emb_dim=128, hidden_size=256, kernel_size=9, n_layers=35, padding_idx=0, dropout_rate=0.1, epsilon=1e-6)
TransformerEncoderModel(vocab_size, emb_dim=512, hidden_size=512, n_layers=8, n_heads=8, padding_idx=0, dropout_rate=0.1)
ProteinEncoderModel(model_config, name='')
ProteinModel(encoder_model, model_config)
ProteinCriterion(model_config)
```

- `ProteinEncoderModel` chooses `lstm`, `transformer`, or `resnet` from `model_config['model_type']`.
- `ProteinModel` chooses `pretrain`, `seq_classification`, `classification`, or `regression` from `model_config['task']`.
- These classes require Paddle; use this reference for orientation and route execution to the protein sub-skill.

### VAE model orientation

```python
seq_vae_model.VAE(vocab, model_config)
sd_vae_model.MolVAE(...)
```

- These are neural model classes for molecular generation; route data preparation, sampling, and checkpoint workflows to `../compound-drug-discovery/SKILL.md`.

## Evidence Labels

- `pahelix/datasets/inmemory_dataset.py`
- `pahelix/utils/data_utils.py`
- `pahelix/utils/protein_tools.py`
- `pahelix/utils/splitters.py`
- `pahelix/utils/compound_tools.py`
- `pahelix/featurizers/*.py`
- `pahelix/model_zoo/*.py`
- `docs/api_doc/datasets.rst`
- `docs/api_doc/utils.rst`
- `docs/api_doc/model_zoo.rst`
