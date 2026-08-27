---
name: core-api-data
description: "Use core PaddleHelix pahelix APIs for datasets, NPZ caches,
  splitters, protein tokenization, compound feature utilities,
  featurizer/model-zoo orientation, and import diagnostics."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Core API and Data

Use this sub-skill when a task asks how to use the reusable `pahelix` package layer rather than a full application workflow. It covers small in-memory data objects, NPZ caches, splitters, protein token IDs, compound feature utility orientation, featurizer/model-zoo routing, and dependency diagnostics.

## Route Here

- The user asks to use `InMemoryDataset`, slice a `pahelix` dataset, or cache/reload a `data_list` as `.npz` files.
- The user asks how to split PaddleHelix molecular records with random, index, scaffold, or random-scaffold splitters.
- The user asks to tokenize protein sequences into PaddleHelix token IDs without launching training.
- The user asks what `CompoundKit`, `Compound3DKit`, `mol_to_graph_data`, or GEM featurizers expect and return.
- The user asks why `pahelix` imports fail, especially around optional `pgl`, `paddle`, `rdkit`, or deprecated `sklearn` packaging.

## Route Elsewhere

- App-level molecular property prediction, pretraining, DTI, molecular generation, docking, or HelixDock workflows: use `../compound-drug-discovery/SKILL.md`.
- Protein pretraining, sequence prediction, function prediction, PPI, or protein app commands: use `../protein-sequence-function/SKILL.md`.
- HelixFold, HelixFold-Single, HelixFold3, or HelixFold-S1 structure prediction: use `../structure-prediction/SKILL.md`.
- LinearRNA fold/partition build and API usage: use `../linear-rna/SKILL.md`.

## Core API Workflow

1. Identify the layer: `pahelix.utils.data_utils` and `pahelix.utils.protein_tools` are dependency-light; dataset loaders, splitters, compound tools, featurizers, and model-zoo modules add optional dependencies.
2. For simple cache work, use `save_data_list_to_npz`, `load_npz_to_data_list`, or `InMemoryDataset.save_data` rather than app-specific preprocessing.
3. For split work, confirm fractions sum to `1.0`; scaffold splitters also require `rdkit` and every record must contain a valid `smiles` string.
4. For molecular graph work, convert valid RDKit `Mol` objects with `mol_to_graph_data` or `mol_to_geognn_graph_data*`; do not pass raw SMILES directly except to featurizer transform functions that explicitly accept raw SMILES/records.
5. For model-zoo orientation, use this skill to choose the class family and data contract; send training, checkpoint, and config execution details to the owning workflow sub-skill.

## Dataset and Cache Pattern

- `InMemoryDataset(data_list=records)` stores a list-like `data_list`; `dataset[i]`, `dataset[start:stop]`, and `dataset[[i, j]]` return records or new datasets. It accepts Python `int`/`np.int32`/`np.int64`, `slice`, or `list` keys, not arbitrary NumPy index arrays.
- `InMemoryDataset(npz_data_path=cache_dir)` loads all sorted `*.npz` files from a directory; `InMemoryDataset(npz_data_files=[...])` loads explicit part files.
- `dataset.save_data(cache_dir)` writes `part-000000.npz`, `part-000001.npz`, and so on, with up to 10,000 records per part.
- `get_data_loader(...)` depends on `pgl.utils.data.Dataloader`; if `pgl` is missing, use the lower-level NPZ utilities or install `pgl` before importing `pahelix.datasets.inmemory_dataset`.

See `references/data-formats.md` for record and cache contracts.

## Splitter Pattern

- `RandomSplitter().split(dataset, frac_train, frac_valid, frac_test, seed=None)` shuffles indices with NumPy and preserves total length.
- `IndexSplitter().split(dataset, frac_train, frac_valid, frac_test)` takes contiguous index ranges without shuffling.
- `ScaffoldSplitter().split(dataset, frac_train, frac_valid, frac_test)` groups records by Bemis-Murcko scaffold from `record['smiles']` and assigns large scaffold groups first.
- `RandomScaffoldSplitter().split(dataset, frac_train, frac_valid, frac_test, seed=None)` randomizes scaffold groups before assigning valid/test/train groups.
- All splitter implementations assert that fractions sum to `1.0`; explain assertion errors as split-configuration problems, not model failures.

## Protein Tokenizer Pattern

- Use `ProteinTokenizer().tokenize(sequence)` for character tokens.
- Use `ProteinTokenizer().convert_tokens_to_ids(tokens)` for explicit tokens.
- Use `ProteinTokenizer().gen_token_ids(sequence)` for `<cls> + residues + <sep>` IDs.
- Known special IDs are `<pad>=0`, `<mask>=1`, `<cls>=2`, `<sep>=3`, `<unk>=4`; unknown residue characters map to `<unk>`.

## Compound Utility Orientation

- `CompoundKit` owns atom/bond vocabularies, fingerprint helpers, daylight functional group counts, and atom/bond feature ID helpers.
- `Compound3DKit` owns atom positions, MMFF/2D pose helpers, bond lengths, and superedge angle helpers.
- `mol_to_graph_data(mol)` returns a molecular graph dictionary with atom features, directed edges plus self-loops, bond features, fingerprints, and functional group counts.
- `mol_to_geognn_graph_data(mol, atom_poses, dir_type)`, `mol_to_geognn_graph_data_MMFF3d(mol)`, and `mol_to_geognn_graph_data_raw3d(mol)` add `atom_pos`, `bond_length`, and `BondAngleGraph_*` fields for GEM-style geometry.
- These compound utilities require `rdkit`; collate/model code usually also requires `pgl` and `paddle`.

## Featurizer and Model-Zoo Map

- Pretrain GNN featurizers: `AttrmaskTransformFn`, `AttrmaskCollateFn`, `SupervisedTransformFn`, `SupervisedCollateFn`; route full compound training to `../compound-drug-discovery/SKILL.md`.
- GEM featurizers: `GeoPredTransformFn(pretrain_tasks, mask_ratio)` and `GeoPredCollateFn(...)` build atom-bond and bond-angle graph feeds for GEM pretraining.
- LiteGEM featurizers: `LiteGEMTransformFn(config)` and `LiteGEMCollateFn()` orient lightweight GEM graph batching.
- Compound model zoo: `PretrainGNNModel`, `AttrmaskModel`, `SupervisedModel`, `GeoGNNModel`, `GeoPredModel`, and `LiteGEM` are Paddle/PGL-backed classes.
- Protein model zoo: `ProteinEncoderModel`, `ProteinModel`, `ProteinCriterion`, and encoder/task classes depend on Paddle; route training or prediction to `../protein-sequence-function/SKILL.md`.
- Generative model orientation: `seq_vae_model.VAE` and `sd_vae_model.MolVAE` are model classes; route molecular generation workflows to `../compound-drug-discovery/SKILL.md`.

## Diagnostics Script

Run the bundled checker from this sub-skill directory:

```bash
python scripts/check_core_api.py --help
python scripts/check_core_api.py --repo-root <PaddleHelix checkout> --check imports --check protein-tokenizer
python scripts/check_core_api.py --repo-root <PaddleHelix checkout> --check dataset
python scripts/check_core_api.py --repo-root <PaddleHelix checkout> --check splitters
```

The script never downloads data or starts training. Use `--repo-root` when `pahelix` is not already installed or importable; the script adds that source tree to `sys.path` only for the selected check and reports optional dependency failures as actionable diagnostics.

## Troubleshooting Quick Map

- `ModuleNotFoundError: pgl`: expected when importing `InMemoryDataset`, splitters via dataset tests, featurizers, or many model-zoo paths without PGL; install compatible PGL or use dependency-light utilities.
- `ModuleNotFoundError: rdkit`: expected for scaffold splitters and compound graph utilities; install RDKit or avoid scaffold/compound feature checks.
- `ModuleNotFoundError: paddle`: expected for model-zoo execution; install a compatible PaddlePaddle backend before model construction/training.
- Deprecated `sklearn` package installation failure: install `scikit-learn` directly, or use the documented compatibility environment variable only for legacy install workflows.
- Missing `smiles` during scaffold split: add a string `smiles` key to every record or use `RandomSplitter`/`IndexSplitter`.
- NPZ reload key errors or wrong record shapes: inspect `.seq_len` and `.singular` metadata and confirm every record has the same keys.

See `references/troubleshooting.md` for detailed diagnosis.

## Evidence

This sub-skill is distilled from `pahelix/datasets/inmemory_dataset.py`, `pahelix/utils/data_utils.py`, `pahelix/utils/protein_tools.py`, `pahelix/utils/splitters.py`, `pahelix/utils/compound_tools.py`, `pahelix/featurizers/*.py`, `pahelix/model_zoo/*.py`, `docs/api_doc/*.rst`, `pahelix/tests/import_test.py`, and `pahelix/utils/tests/*.py`.
