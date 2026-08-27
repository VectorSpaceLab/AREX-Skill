# Molecule Data Prep Troubleshooting

## Import and Install Failures

Symptoms:

- `ModuleNotFoundError: No module named 'dgllife'`
- DGL import errors before any data code runs.
- RDKit import errors when parsing SMILES.

Fixes:

- Confirm the runtime has `dgllife`, `dgl`, `torch`, `rdkit`, `pandas`, `numpy`, `scipy`, and `scikit-learn` installed. For nearest-neighbor graph utilities, note that newer scikit-learn `NearestNeighbors.radius_neighbors` behavior can expose DGL-LifeSci 0.3.1 edge cases around self-distance removal; prefer tiny validation and record the package versions before changing production code.
- Match DGL and PyTorch builds to the available CPU/GPU backend. Data validation does not require GPU.
- For helper script checks, start with `python scripts/validate_molecule_inputs.py --help`; this should not require reading external datasets or downloading data.

## Optional Dependency and Complex-Data Failures

Symptoms:

- Protein-ligand file loading fails for `.mol2`, `.pdbqt`, `.sdf`, or `.pdb` files.
- Charge calculation or sanitization fails.
- Complex graph construction fails because coordinates are missing.

Fixes:

- Validate file existence and extension first.
- Try `load_molecule(..., sanitize=False, calc_charges=False, remove_hs=False, use_conformation=True)` before enabling more chemistry processing.
- Ensure ligand and protein molecules include conformers when using ACNN/PotentialNet graph helpers.
- Keep PDBBind downloads or full benchmark preparation out of tiny validation workflows unless explicitly requested.

## Invalid SMILES and Row-Level Data Errors

Symptoms:

- Dataset length is smaller than CSV/TXT row count.
- The validator reports `invalid SMILES` for specific rows.
- `MoleculeCSVDataset` writes invalid rows to `error_log` or silently filters them when `error_log` is omitted.

Fixes:

- Run `scripts/validate_molecule_inputs.py` on a small fixture and inspect row numbers.
- Remove empty SMILES strings and trim whitespace.
- Verify uncommon atom symbols, charges, ring closures, and bracket syntax with RDKit.
- Preserve a raw row id column in CSVs if predictions must be mapped back after invalid-row filtering.

## Missing Labels and Mask Mistakes

Symptoms:

- `KeyError` for a task column.
- Labels have an unexpected width.
- Missing labels become zeros and contaminate metrics.
- `task_pos_weights` gives unexpected values.

Fixes:

- Pass `task_names` explicitly whenever the CSV has non-label columns.
- Use `init_mask=True` for multitask datasets with missing labels.
- Use the returned `mask` from `dataset[i]` and from batches when updating `Meter`.
- Use `task_pos_weights(indices)` only for binary classification tasks and only with masks available.
- Use `--require-labels` in the validator when the workflow cannot tolerate missing task values.

## Graph and Feature Shape Mismatches

Symptoms:

- Model expects `g.ndata['h']` but the graph has `atomic_number` and `chirality_type`.
- Model expects edge features but `g.edata` is empty.
- Node feature width is not the expected 74.
- Self-loop or virtual-node options change edge/node feature widths.

Fixes:

- Match model family and featurizer family before training: canonical, AttentiveFP, PAGTN, or pretraining-style GIN.
- For canonical features, use `CanonicalAtomFeaturizer()` and check `g.ndata['h'].shape[1] == 74`.
- Add `CanonicalBondFeaturizer()` only when downstream code expects `g.edata['e']`.
- If using `add_self_loop=True`, ensure bond featurizers are configured with compatible self-loop handling.
- Rebuild caches after changing graph topology or featurizers.

## Cache File Pitfalls

Symptoms:

- Changing featurizers has no effect.
- Graphs load with old feature fields.
- A tiny experiment unexpectedly reads stale data.

Fixes:

- Set `load=False` while iterating on graph construction.
- Use a new `cache_file_path` for each topology/featurizer combination.
- Delete stale `.bin` graph caches before rerunning a changed pipeline.
- Keep caches outside the generated skill tree and in task-owned output directories.

## Split Failures

Symptoms:

- Fractions assertion: expected split fractions to sum to 1.
- Scaffold or molecular-weight splits fail on invalid molecules.
- Validation/test subsets are empty for tiny fixtures.
- Stratified split fails or produces poor balance.

Fixes:

- Check `frac_train + frac_val + frac_test == 1.0`.
- Validate SMILES before scaffold or molecular-weight splitting.
- Pass `random_state` to `RandomSplitter` for reproducible debugging.
- Pass labels shaped `(N, T)` and a valid `task_id` to `SingleTaskStratifiedSplitter`.
- For tiny fixtures, prefer `ConsecutiveSplitter` or `RandomSplitter` only as smoke checks.

## Helper Script Failures

Symptoms:

- `--format csv` without `--smiles-column` fails.
- `--tasks` references absent columns.
- `--format txt` is used with `--require-labels`.
- `--graph complete` is slow on large molecules.

Fixes:

- Provide `--smiles-column` for CSV inputs.
- Use comma-separated task names exactly matching CSV headers, for example `--tasks task1,task2`.
- Use CSV format for label validation.
- Limit validation scope with `--max-rows`.
- Use `--graph bigraph` for ordinary molecular graph checks and reserve `--graph complete` for complete-graph model contracts.

## Routing Misuse

Symptoms:

- A data-prep answer starts designing model layers or training loops.
- A reaction WLN dataset requires atom-map or candidate-bond handling.
- A pretrained checkpoint name or model zoo decision dominates the task.

Fixes:

- Route model architecture and full property training to `property-prediction`.
- Route pretrained model and `load_pretrained` decisions to `model-zoo-pretraining`.
- Route WLN reaction center/ranking data to `reaction-prediction`.
- Keep this sub-skill focused on inputs, graph construction, featurization, datasets, splitters, and validation.
