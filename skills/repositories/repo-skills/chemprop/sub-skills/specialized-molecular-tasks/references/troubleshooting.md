# Specialized Task Troubleshooting

## Atom Maps and `--reorder-atoms`

Symptoms:

- Atom target values appear attached to the wrong atoms.
- The same mapped molecule gives different atom predictions after equivalent SMILES reordering.
- Atom descriptor rows do not align with mapped atom targets.

Fixes:

- Use `--reorder-atoms` when atom target lists are ordered by atom map number rather than by SMILES/RDKit atom order.
- Remember that `--reorder-atoms` does not reorder bonds. For bond targets, prefer matrix-form targets when SMILES order varies, or regenerate bond lists in the exact RDKit bond order used by Chemprop.
- Do not combine `--reorder-atoms` with `--use-cuikmolmaker-featurization`; the CLI rejects that combination.

## List and List-of-List Target Parsing

Symptoms:

- `ValueError` or parsing failures for atom/bond target cells.
- Bond target length mismatches.
- Bounded bond targets fail when using matrix-style values.

Fixes:

- Quote CSV cells that contain commas, such as `"[0.1, -0.1]"`.
- Ensure every atom target list has one value per atom and every bond target list has one value per bond.
- For bond matrix targets, use a square `n_atoms x n_atoms` list-of-lists; Chemprop extracts values for actual bonds.
- For bounded bond targets containing `<` or `>`, use list-form bond targets. Bounded matrix bond parsing is not supported.
- Empty molecule/bond cases should use parseable empty lists such as `[]`, not blank cells.

## Constraint Mapping

Symptoms:

- Chemprop raises an error that constraints require `--constraints-to-targets`.
- Constrained predictions do not sum to the intended molecule-level quantity.
- The wrong atom/bond target receives a constraint.

Fixes:

- Provide `--constraints-path` as a CSV with one row per input row and no SMILES column.
- Provide one `--constraints-to-targets` entry for each constraints CSV column, in the same order.
- Use target column names passed to `--atom-target-columns` or `--bond-target-columns`, such as `atom_charge bond_energy`.
- Keep the target-column order stable. Internally, target indices are derived from the order of `--atom-target-columns` and `--bond-target-columns`.
- Use `nan` or leave an unconstrained target without a matching constraint rather than mapping to an invented target.

## Reaction Modes and Columns

Symptoms:

- Reaction commands parse but model behavior does not match training.
- Prediction fails because input component columns differ from training.
- Balanced reactions behave unexpectedly.

Fixes:

- Use `--reaction-columns` for reaction SMILES and `--smiles-columns` for non-reaction molecule components.
- Repeat the same reaction columns, molecule columns, and `--rxn-mode` at prediction/fingerprint time.
- Prefer `--rxn-mode` in commands; `--reaction-mode` is an alias.
- Add `--keep-h` when mapped hydrogens are part of the reaction representation.
- Use `_BALANCE` modes for imbalanced reaction mappings when the balanced feature construction is desired.

## Multicomponent Dimensions

Symptoms:

- `Inconsistent number of components` errors for `--message-hidden-dim` or `--depth`.
- `Single-component data only accepts one --message-hidden-dim value`.
- Errors when combining shared MPNNs and component-specific dimensions.

Fixes:

- Count components as the number of reaction columns plus SMILES columns, with a minimum of one.
- Supply one `--message-hidden-dim` / `--depth` value to broadcast, or exactly one value per component.
- Do not use `--mpn-shared` with multiple `--message-hidden-dim` or `--depth` values.
- Do not use shared MPNNs for mixed reaction+molecule data.
- For component-indexed feature paths, use zero-based indices that match the component order used by the command.

## Extra Features on Reaction Components

Symptoms:

- Warnings that `atom_features_extra` or `bond_features_extra` are unsupported for reactions.
- Reaction-component atom/bond feature files appear ignored.

Fixes:

- Avoid applying atom or bond extras to reaction components unless you have verified the specific behavior.
- Use molecule-level descriptors (`--descriptors-path`, `--descriptors-columns`, `--molecule-featurizers`) for reaction rows when possible.
- Apply atom/bond features to non-reaction molecule components in reaction-plus-solvent workflows using indexed paths.

## Spectral Task Flags

Symptoms:

- CLI rejects `--spectral-activation`, `--spectra-target-floor`, `--phase-features-path`, or `--spectra-phase-mask-path`.
- Spectral outputs are normalized unexpectedly.

Fixes:

- In Chemprop 2.2.3, do not generate those spectral CLI flags; they are not exposed by the parser.
- Expect spectral predictions to be positive and normalized to sum to `1` across target positions.
- Use `--task-type spectral` with spectral target columns and metrics such as `sid` and `earthmovers`.
- Use the Python API if custom spectral activation behavior is required.

## Bounded and Constrained Outputs

Symptoms:

- Bounded targets train but predictions violate a desired conservation law.
- Constrained predictions work during training but fail during prediction or evaluation.

Fixes:

- Use bounded losses only for censored values with `<`/`>` markers.
- Use constraints for sum/conservation requirements.
- Keep constraints CSV row order identical to the main input CSV row order.
- Include the same parser-critical input flags at prediction time that the model expects, especially specialized columns and extra descriptor paths.
