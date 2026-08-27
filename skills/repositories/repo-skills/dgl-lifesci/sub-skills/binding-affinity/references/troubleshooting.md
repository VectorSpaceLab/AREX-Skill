# Binding Affinity Troubleshooting

Use this reference when DGL-LifeSci binding-affinity workflows fail during import, file validation, molecule loading, complex graph construction, model instantiation, data splitting, or training.

## Import and Install Failures

Symptoms:

- `ModuleNotFoundError` for `dgllife`, `dgl`, `torch`, `rdkit`, `sklearn`, `pandas`, `numpy`, or `scipy`.
- DGL backend errors appear before molecule loading.
- RDKit import succeeds in one environment but fails in another.

Fixes:

- Confirm the active Python environment contains DGL-LifeSci, DGL, PyTorch, RDKit, scikit-learn, NumPy/SciPy, and pandas.
- Start with CPU smoke checks; GPU is not required to validate file formats, conformations, graph schemas, or constructor signatures.
- Run `python scripts/check_complex_inputs.py --protein pocket.pdb --ligand ligand.sdf` before importing heavy training code.
- Keep environment paths and activation details out of reusable public skill content.

## Optional Dependency and Download Failures

Symptoms:

- `PDBBind(...)` tries to download an archive unexpectedly.
- Network access is unavailable or too slow.
- Full dataset extraction fills disk or is blocked.

Fixes:

- Pass `local_path` for user-provided PDBBind-style data.
- Ask before constructing a dataset without `local_path`, because that can trigger PDBBind downloads.
- For smoke checks, use a tiny local complex pair and `load_molecule` instead of a full PDBBind object.
- Keep download/cache directories project-owned and intentional when the user approves dataset downloads.

## Missing 3D Conformations

Symptoms:

- `load_molecule` returns a molecule but coordinates are `None`.
- Graph construction raises `Expect ligand_coordinates to be provided.` or `Expect protein_coordinates to be provided.`
- A ligand was supplied as SMILES or a 2D-only SDF.

Fixes:

- Require ligand and protein files with 3D coordinates for ACNN and PotentialNet.
- Run `python scripts/check_complex_inputs.py --protein pocket.pdb --ligand ligand.sdf --inspect-ligand` to detect missing ligand coordinates early.
- Do not pass `use_conformation=False` into binding graph construction workflows.
- If the user needs conformer generation from SMILES, route general molecule preparation to `../molecule-data-prep/SKILL.md` and make the conformer-generation method explicit before returning to binding graphs.

## RDKit Sanitization, Charges, and Hydrogen Issues

Symptoms:

- RDKit returns `None` for a molecule.
- Sanitization fails for a ligand or protein file.
- Gasteiger charge calculation warns or fails.
- Atom counts differ from expected values after hydrogen removal.

Fixes:

- Start with `sanitize=False`, `calc_charges=False`, and `remove_hs=False`, matching DGL-LifeSci binding defaults.
- Enable `sanitize=True` only when the user's chemistry workflow needs sanitized molecules and files are known to be clean.
- Remember that `calc_charges=True` enforces sanitization and may warn for difficult molecules.
- Use `remove_hs=True` consistently across ligand and protein inputs when the model/config expects hydrogen-stripped coordinates.
- If graph construction uses `strip_hydrogens=True`, compare graph atom counts to non-hydrogen atom counts rather than raw molecule atom counts.

## PDBBind Local Layout Failures

Symptoms:

- Dataset construction raises an index error while looking for `*core*data*` or `*refined*data*` files.
- Ligand or pocket files cannot be found after the index is parsed.
- The user points `local_path` at a single complex directory instead of a PDBBind root.
- `sequence` or `structure` split attributes are missing.

Fixes:

- Point `local_path` at the root containing index/label files and one subdirectory per PDB code.
- Ensure files follow names like `<pdb_code>_ligand.sdf`, `<pdb_code>_pocket.pdb`, and `<pdb_code>_protein.pdb`.
- Use `load_binding_pocket=True` only when pocket files exist; otherwise set it to `False` and provide full protein files.
- Use `pdb_version='v2015'` for v2015-style local data; use `v2007` only for v2007-format index files and agglomerative split needs.
- Treat `sequence` and `structure` splits as v2007 refined-set workflows, not general local-layout splits.

## Config and API Misuse

Symptoms:

- `ValueError` for unsupported `subset`, `model`, or split name.
- ACNN receives a PotentialNet graph tuple, or PotentialNet receives one ACNN heterograph.
- `PotentialNet` fails because `f_in`, `f_bond`, or `n_etypes` do not match graph features.
- ACNN constructor fails from mismatched `hidden_sizes`, `weight_init_stddevs`, or `dropouts` lengths.

Fixes:

- Use `subset='core'` or `subset='refined'` only.
- Keep graph construction and model choice paired: ACNN with `ACNN_graph_construction_and_featurization`; PotentialNet with `PN_graph_construction_and_featurization`.
- Set PotentialNet `f_in` from `complex_bigraph.ndata['h'].shape[1]` and `n_etypes = len(distance_bins) + 5`.
- Ensure `f_bond >= f_in`; the implementation pads input features up to `f_bond`.
- Make `dropouts` a list of three floats for PotentialNet.
- Make ACNN `weight_init_stddevs` length `len(hidden_sizes) + 1` and `dropouts` length `len(hidden_sizes)`.
- Use `torch.tensor([...])` or a compatible tensor for ACNN `features_to_use` when filtering atomic numbers.

## Graph Construction Failures

Symptoms:

- Assertions about `max_num_ligand_atoms` or `max_num_protein_atoms` being too small.
- KNN graph construction produces unexpectedly few or many edges.
- Graphs are missing expected fields such as `atomic_number`, `mask`, `distance`, `h`, or `e`.

Fixes:

- Leave `max_num_ligand_atoms` and `max_num_protein_atoms` as `None` for local smoke checks; only set them after measuring maximum atom counts across a dataset.
- For ACNN, verify node data `atomic_number` and `mask`, and edge data `distance` on ligand/protein/complex relations.
- For PotentialNet, verify `complex_bigraph.ndata['h']`, `complex_bigraph.edata['e']`, and `complex_knn_graph.edata['e']`.
- Tune `neighbor_cutoff`, `max_num_neighbors`, and `distance_bins` deliberately; these alter the spatial graph, not just model hyperparameters.

## Memory, CPU, and GPU Limits

Symptoms:

- Dataset preprocessing hangs or consumes all CPUs.
- DataLoader workers crash while handling RDKit molecules or DGL graphs.
- GPU out-of-memory occurs on the first epoch.
- Device mismatch errors occur between graphs, labels, and model parameters.

Fixes:

- Use `num_processes=1` for dataset preprocessing and `num_workers=0` or `1` for DataLoader debugging.
- Prefer pocket files over full proteins for initial runs.
- Reduce `batch_size` before reducing model sizes.
- Keep ACNN zero padding enabled for stable batched behavior, but remember it increases memory for large atom-count outliers.
- Move every graph in the PotentialNet tuple, labels, and model parameters to the same device before forward/loss.
- Validate on CPU before moving to GPU.

## Split and Evaluation Pitfalls

Symptoms:

- Refined-set training accidentally includes core-set complexes that are later used for testing.
- Temporal split produces unexpected train/validation/test sizes.
- R2 looks unstable on tiny validation or test splits.

Fixes:

- Keep `remove_coreset_from_refinedset=True` for refined-to-core evaluation unless intentionally testing leakage behavior.
- Verify `frac_train + frac_val + frac_test == 1.0` for random/scaffold/stratified/temporal splits.
- Use stratified and scaffold splits only after molecule loading succeeds; they depend on labels or ligand molecules.
- Treat R2 on very small splits as a smoke signal, not a reliable model-quality estimate.

## Helper Script Failures

Symptoms:

- `check_complex_inputs.py` reports an unsupported extension.
- Ligand inspection fails even though the file exists.
- The script reports no ligand conformation.

Fixes:

- Rename or convert files to `.sdf`, `.mol2`, `.pdbqt`, or `.pdb` before using DGL-LifeSci `load_molecule`.
- Use `--sanitize` only when the molecule file is chemically clean enough for RDKit sanitization.
- Use `--allow-missing-conformation` only for metadata-only checks; do not proceed to ACNN or PotentialNet graph construction without coordinates.
- Add `--no-conformation` only when the task intentionally does not need binding graph construction.
