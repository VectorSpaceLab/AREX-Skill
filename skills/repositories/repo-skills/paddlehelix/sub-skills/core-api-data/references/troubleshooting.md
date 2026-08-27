# Core API Troubleshooting

Use this guide to turn common core `pahelix` failures into clear, actionable diagnoses.

## Import and Optional Dependency Failures

### `ModuleNotFoundError: No module named 'pgl'`

Likely context:

- Importing `pahelix.datasets.inmemory_dataset` because it imports `pgl.utils.data.Dataloader` at module import time.
- Importing `pahelix.featurizers.*`, many graph collate functions, or compound model-zoo modules.
- Running native splitter tests that also import `InMemoryDataset`.

Actions:

- For NPZ-only work, import `pahelix.utils.data_utils` directly and avoid `InMemoryDataset` until PGL is installed.
- For graph batching/model work, install a PGL version compatible with the selected PaddlePaddle backend.
- For diagnostics, run `scripts/check_core_api.py --check imports --check dataset` and read which layer fails.

### `ModuleNotFoundError: No module named 'rdkit'`

Likely context:

- Importing `pahelix.utils.splitters`; scaffold splitters import RDKit scaffold helpers.
- Importing `pahelix.utils.compound_tools`; compound graph utilities import RDKit chemistry APIs.
- Running `--check rdkit` or `--check splitters` in the bundled checker.

Actions:

- Install RDKit in the environment if scaffold splitting or compound graph conversion is required.
- Use equivalent random or index splitting logic if a project cannot install RDKit; the source `pahelix.utils.splitters` module itself still imports RDKit at module import time.
- Validate user SMILES before graph conversion; malformed SMILES are data problems, not model problems.

### `ModuleNotFoundError: No module named 'paddle'`

Likely context:

- Importing `pahelix.model_zoo.*`, `pahelix.networks.*`, or running any model construction/training.

Actions:

- Install a PaddlePaddle build compatible with CPU/GPU hardware and the rest of the environment.
- Treat model-zoo references in this sub-skill as orientation only unless Paddle/PGL are already installed.
- Route training or inference workflow setup to the relevant sibling sub-skill.

### Deprecated `sklearn` package failure

Likely context:

- Legacy setup metadata names the deprecated `sklearn` package rather than modern `scikit-learn`.
- Modern pip may reject installing `sklearn` by name.

Actions:

- Install `scikit-learn` directly.
- Use a legacy compatibility environment variable only when a legacy install path cannot be edited: `SKLEARN_ALLOW_DEPRECATED_SKLEARN_PACKAGE_INSTALL=True`.
- Prefer fixing requirements files or install commands to use `scikit-learn` when maintaining an environment.

## Dataset and NPZ Failures

### Empty or inconsistent `data_list`

Symptoms:

- `IndexError` around `data_list[0]` during `save_data_list_to_npz`.
- `KeyError` for a key that exists in some records but not all.
- NumPy concatenation errors for arrays with incompatible shapes.

Diagnosis:

- `save_data_list_to_npz` infers keys from the first record and then indexes every record with those keys.
- Sequence-like values under the same key must be concatenable along axis `0`.
- Scalar values and array values under the same key should not be mixed.

Actions:

- Check `len(data_list) > 0` before saving.
- Normalize every record to the same keys.
- Convert Python lists/scalars to consistent NumPy arrays when appropriate.
- Save one logical schema per NPZ cache; do not append unrelated record shapes into the same part file.

### NPZ metadata mismatch

Symptoms:

- Loading fails for missing `<key>.seq_len` or `<key>.singular`.
- Reloaded record count is wrong.
- Values appear shifted across records.

Diagnosis:

- PaddleHelix cache files are not generic `.npz` tables; they require per-key metadata created by `save_data_list_to_npz`.
- Manual edits or third-party `.npz` writers usually do not create the required metadata.

Actions:

- Rebuild cache files with `save_data_list_to_npz` or `InMemoryDataset.save_data`.
- Inspect `np.load(file).files` and verify every logical key has matching metadata.
- Keep part files sorted or pass explicit `npz_data_files` in the required order.

## Splitter Failures

### Fractions do not sum to `1.0`

Symptoms:

- `AssertionError` or NumPy assertion output from `np.testing.assert_almost_equal`.

Actions:

- Check `frac_train + frac_valid + frac_test` exactly in code.
- Use conventional triples such as `(0.8, 0.1, 0.1)`, `(0.7, 0.1, 0.2)`, or `(0.34, 0.33, 0.33)`.
- For tiny datasets, explain that valid/test can be empty even when fractions are correct.

### Missing `smiles` for scaffold split

Symptoms:

- `KeyError: 'smiles'` from `dataset[i]['smiles']`.

Actions:

- Add a `smiles` string to every record before using `ScaffoldSplitter` or `RandomScaffoldSplitter`.
- Use `RandomSplitter` or `IndexSplitter` if the data has no molecular SMILES.
- Run `scripts/check_core_api.py --check splitters --simulate-missing-smiles` to see the expected diagnostic shape.

### RDKit missing or invalid SMILES

Symptoms:

- `ModuleNotFoundError: rdkit` at splitter import.
- RDKit parsing/scaffold errors for malformed SMILES.

Actions:

- Install RDKit if scaffold grouping is required.
- Validate each SMILES before scaffold splitting.
- Treat invalid SMILES as input-data quality issues and filter or fix records before splitting.

## Protein Tokenization Surprises

Symptoms:

- Unexpected `<unk>` IDs in tokenized sequences.
- Sequence IDs include two extra tokens.

Diagnosis:

- `gen_token_ids` always adds `<cls>` at the start and `<sep>` at the end.
- Unknown characters, lowercase residues, punctuation, whitespace, and unsupported letters map to `<unk>`.

Actions:

- Normalize sequences to uppercase one-letter amino-acid tokens before tokenization.
- Strip FASTA headers and whitespace before calling `gen_token_ids`.
- Use `tokenize` plus `convert_tokens_to_ids` when boundary tokens are not wanted.

## Compound Utility Failures

### RDKit molecule is `None`

Symptoms:

- `mol_to_graph_data` fails because a caller passed `None` from `Chem.MolFromSmiles`.
- Featurizer transform returns `None` for invalid SMILES.

Actions:

- Validate SMILES first with RDKit or `check_smiles_validity`.
- Use `InMemoryDataset.transform(..., drop_none=True)` when filtering bad transform outputs is acceptable.
- Report invalid SMILES as data cleaning issues.

### `mol_to_graph_data` returns `None`

Likely causes:

- Molecule has zero atoms.
- Molecule contains dummy atoms with atomic number `0`.

Actions:

- Filter such molecules before graph conversion.
- Use a clear message that the graph utility rejected the molecule schema, not that Paddle/PGL failed.

### Geometry generation issues

Likely context:

- `Compound3DKit.get_MMFF_atom_poses` can fail during conformer generation or MMFF optimization and fall back internally.
- `mol_to_geognn_graph_data_raw3d` expects an existing conformer.

Actions:

- Use `mol_to_geognn_graph_data_MMFF3d` when no conformer is present.
- Use `mol_to_geognn_graph_data_raw3d` only for molecules with conformers.
- For molecules larger than 400 atoms, expect 2D pose fallback in the MMFF helper path.

## Model-Zoo Import Failures

Symptoms:

- Import errors for `paddle`/`pgl`.
- Runtime config `KeyError` for missing `atom_names`, `bond_names`, `bond_float_names`, or task fields.

Actions:

- Install backend dependencies before importing or constructing model classes.
- Build `model_config` from the featurizer data contract: compound graph models need atom/bond feature names; GEM needs bond float and bond-angle names; protein models need `model_type` and `task` selections.
- Route actual training, checkpoints, or app command construction to the sibling workflow sub-skills.

## Diagnostic Script Patterns

- Basic source-layout import and dependency-light checks:

```bash
python scripts/check_core_api.py --repo-root <PaddleHelix checkout> --check imports --check protein-tokenizer
```

- Tiny NPZ round-trip checks:

```bash
python scripts/check_core_api.py --repo-root <PaddleHelix checkout> --check dataset
```

- Optional RDKit/scaffold diagnostics:

```bash
python scripts/check_core_api.py --repo-root <PaddleHelix checkout> --check rdkit --check splitters
```

Use `--help` without a checkout to inspect parser behavior. Use `--simulate-npz-mismatch` or `--simulate-missing-smiles` with `--repo-root` to demonstrate user-facing diagnoses for hard cases without mutating external data.

## Evidence Labels

- `pahelix/datasets/inmemory_dataset.py`
- `pahelix/utils/data_utils.py`
- `pahelix/utils/protein_tools.py`
- `pahelix/utils/splitters.py`
- `pahelix/utils/compound_tools.py`
- `pahelix/utils/tests/data_utils_test.py`
- `pahelix/utils/tests/splitters_test.py`
- Environment handoff optional dependency findings
