# Reaction Prediction Troubleshooting

## Import and Install Failures

Symptoms:

- `ModuleNotFoundError: No module named 'dgllife'`
- DGL or Torch import errors
- RDKit import errors before dataset construction

Actions:

- Confirm the active environment imports `dgllife`, `dgl`, `torch`, and `rdkit` before running reaction workflows.
- Keep validation cheap first: `scripts/validate_reaction_inputs.py` uses only the Python standard library.
- If DGL-LifeSci imports but model code fails, inspect installed constructor signatures before assuming source-branch APIs.
- For CPU-only environments, avoid multi-GPU commands and expect slower preprocessing/training.

## Optional Dependency Issues

Symptoms:

- Candidate ranking prints or raises a MolVS-related warning.
- Strict and sanitized candidate ranking metrics differ unexpectedly.

Actions:

- MolVS is optional for molecule standardization comparisons during candidate ranking evaluation.
- If MolVS is unavailable, report strict RDKit results and mention sanitized MolVS metrics may be skipped or unreliable.
- Do not add MolVS as a hidden runtime requirement for simple reaction file validation.

## Invalid Reaction SMILES

Symptoms:

- `WLNCenterDataset` writes many `*_invalid_reactions.proc` rows.
- RDKit cannot parse reactants or products.
- Errors mention atom maps or `molAtomMapNumber`.

Actions:

- Validate text structure first: `python scripts/validate_reaction_inputs.py --reactions data.txt --require-atom-maps`.
- Check each row has exactly one `>>`, non-empty reactants, and non-empty products.
- Remove whitespace inside reaction SMILES.
- Ensure atom-map numbers are present and preferably consecutive from 1.
- Convert raw reactions with explicit hydrogens to canonical no-explicit-hydrogen SMILES before assigning atom maps when map numbering becomes non-consecutive.
- Let `WLNCenterDataset(..., check_reaction_validity=True, reaction_validity_result_prefix='train')` create valid/invalid splits before ranking.

## Candidate Bond Generation Problems

Symptoms:

- Candidate ranking has empty batches or no valid candidate products.
- `gfound` is low even when center prediction seems plausible.
- Candidate-bond files have fewer rows than processed reaction files.

Actions:

- Validate row alignment with `scripts/validate_reaction_inputs.py --reactions train_valid_reactions.proc --candidate-bonds train_candidate_bonds.txt --processed`.
- Confirm the candidate-bond file was generated from the same reaction file and line order used for ranking.
- Check candidate records use `atom1 atom2 change_type score;` and valid change types: `0.0`, `1.0`, `2.0`, `3.0`, `1.5`.
- Keep the center model compatible with the center config used to generate candidate bonds.
- If too few candidate bonds survive filtering, increase center top-k generation before ranking or review atom mapping quality.

## Large Reactions Ignored

Symptoms:

- Ranking dataset length changes after `.ignore_large(True)`.
- Some reactions never appear in ranking batches.

Actions:

- Check `size_cutoff`; default is `100` atoms in reactants.
- Do not compare raw reaction row counts to ranking samples after large-sample filtering.
- For small debugging fixtures, avoid `.ignore_large(True)` until row alignment and candidate parsing are confirmed.
- For production runs, report how many reactions were skipped by size cutoff.

## Config Mismatch

Symptoms:

- Shape mismatch loading `center_results/model_*.pkl` or `candidate_results/model_*.pkl`.
- Ranking model expects `node_in_feats=89` but receives another feature width.
- Center model returns scores with unexpected final dimension.

Actions:

- Center defaults from rexgen-direct: `node_in_feats=82`, `edge_in_feats=6`, `node_pair_in_feats=10`, `node_out_feats=300`, `n_layers=3`, `n_tasks=5`.
- Ranking defaults: `node_in_feats=89`, `edge_in_feats=5`, `node_hidden_feats=500`, `num_encode_gnn_layers=3`.
- Load checkpoints only into models constructed with the same feature dimensions and hidden sizes.
- Keep custom featurizers synchronized with model constructor dimensions.
- Route generic featurizer design to `../molecule-data-prep/SKILL.md` if the issue is not reaction-specific.

## Data Download and Long Training Skips

Symptoms:

- Instantiating `USPTOCenter` or `USPTORank` starts a download.
- `load_pretrained('wln_center_uspto')` or `load_pretrained('wln_rank_uspto')` tries to fetch checkpoints.
- Training commands run for a long time or consume GPU/CPU heavily.

Actions:

- Ask before running built-in USPTO workflows if downloads or long ML jobs were not explicitly requested.
- For planning tasks, provide command classes and required inputs instead of executing training.
- For smoke tests, use tiny custom files and low `-np`/`-nw` values.
- Avoid running cleanup scripts automatically because they can remove cached preprocessing files needed by a user's current experiment.

## Multiprocessing and Worker Failures

Symptoms:

- `BrokenPipeError: [Errno 32] Broken pipe` during center preprocessing.
- `RuntimeError: received 0 items of ancdata` during ranking data loading.
- Hangs or excessive memory use from many workers.

Actions:

- Reduce center preprocessing processes with `-np 1` or another small value.
- Reduce ranking DataLoader workers with `-nw 1` or another small value.
- In constrained environments, prefer CPU, single process, and tiny fixture validation before scaling up.
- For multi-GPU center training, custom datasets may need a first graph-construction pass before spawning worker processes.

## CLI and API Misuse

Symptoms:

- `WLNRankDataset` cannot find `train_valid_reactions.proc`.
- Ranking is attempted directly on raw reaction files.
- `mode` assertion fails.

Actions:

- Run center preprocessing first or construct `WLNCenterDataset` with validity checks to create `*_valid_reactions.proc`.
- Use raw files for `WLNCenterDataset`; use processed files plus candidate bonds for `WLNRankDataset`.
- Set rank dataset `mode` exactly to `train`, `val`, or `test`.
- Ensure `USPTORank` receives an explicit `candidate_bond_path`; it does not generate candidate bonds by itself.

## Helper Script Failures

Symptoms:

- `validate_reaction_inputs.py` exits nonzero.
- Reported malformed lines look syntactically valid to the user.

Actions:

- Remember the helper is a text-level gate; it may reject whitespace, malformed separators, or unsupported candidate records before chemistry-aware parsing.
- Re-run with a small `--max-rows` to isolate the first failures.
- Use `--processed` only for files that include graph edits after the reaction string.
- Use `--require-atom-maps` for WLN modeling inputs, but omit it only when intentionally triaging raw un-mapped data before mapping.
