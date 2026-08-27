# Structure Generation Troubleshooting

## Sanitization And Invalid Molecules

Symptoms:

- `dm.to_mol` returns `None`.
- Fragmentation or reactions produce `None` products.
- RDKit raises valence, kekulization, aromaticity, or property-cache errors.

Actions:

- Route through `molecule-io-prep` first: parse, keep largest fragment if appropriate, neutralize/standardize, and sanitize.
- Use `dm.fix_mol` or `dm.sanitize_mol` on generated fragments/products before downstream use.
- Filter `None` values after fragmentation, reaction application, and enumeration.
- Preserve atom maps and dummy atoms when reactions need them; do not standardize away `[1*]`, `[*:1]`, or atom-map labels before applying mapped reactions.

## Conformer Embedding Failures Or Timeouts

Symptoms:

- `dm.conformers.generate` raises `ValueError: Conformers embedding failed ...`.
- Large flexible molecules take too long.
- Energy minimization does not converge.

Actions:

- Start with `n_confs=1-5`, `minimize_energy=False`, `num_threads=1`, and a fixed `random_seed`.
- Retry with `use_random_coords=True`, `method="ETKDGv3"`, or targeted `embed_params`.
- For batch workflows, set `ignore_failure=True`, record failed SMILES, and skip `None` results.
- Add an `rms_cutoff` to prune near-duplicate conformers.
- Increase `energy_iterations` only after embedding succeeds; use `warning_not_converged` and `verbose=True` to diagnose minimization.

## Missing 3D Coordinates

Symptoms:

- `dm.conformers.sasa`, `get_coords`, `center_of_mass`, `rmsd`, or `align_conformers` raises because no conformers exist.

Actions:

- Check `mol.GetNumConformers() > 0` before 3D-only APIs.
- Generate conformers first with `dm.conformers.generate`.
- For 2D depiction alignment, use `dm.align.template_align` instead of 3D conformer APIs.
- For SASA, ensure FreeSASA support is available in the RDKit build; if unavailable, skip SASA and report that conformer generation still succeeded.

## Template Alignment And Reordering Mismatches

Symptoms:

- `template_align` returns a molecule but layout is not meaningful.
- `reorder_mol_from_template` returns `None`.
- Ambiguous matches occur for symmetric molecules or explicit hydrogens.

Actions:

- Ensure the template is a relevant substructure or close analog; otherwise MCS alignment may be weak or slow.
- Use `auto_align_many` to partition analogs by scaffold before aligning many molecules.
- Keep hydrogen representation consistent between molecule and template for atom reordering.
- Use `ambiguous_match_mode="hs-only"` when only hydrogens are ambiguous, or `"best-first"` when a deterministic best-effort order is acceptable.
- Set `enforce_atomic_num=True` and/or `enforce_bond_type=True` when mismatched graphs must be rejected strictly.

## Reaction SMARTS, RXN Blocks, And Product Issues

Symptoms:

- `rxn_from_smarts` or `rxn_from_block` fails to parse.
- `is_reaction_ok` returns `False`.
- `apply_reaction` returns an empty list.
- Products contain dummy atoms or fail sanitization.

Actions:

- Validate reaction SMARTS separately with `dm.reactions.is_reaction_ok(rxn, enable_logs=True)`.
- Check each reactant with `dm.reactions.can_react` and `find_reactant_position` before applying the reaction.
- Confirm reactants are passed in the expected tuple order and retain atom maps/dummy labels.
- For attachment chemistry, count handles with `num_attachment_points` and normalize handles with `convert_attach_to_isotope` when needed.
- Use `single_product_group=False` for deterministic complete product groups; avoid the random product-group selection in `select_reaction_output(single_product_group=True)` unless stochastic selection is intended.
- Use `rm_attach=True` only after dummy attachment atoms are no longer needed.

## Combinatorial Explosion

Symptoms:

- Structural isomer enumeration, stereoisomer enumeration, fuzzy scaffolding, fragment assembly, or reaction product generation grows unexpectedly.
- Workflows become slow or return very large lists.

Actions:

- Set `n_variants`, `timeout_seconds`, `depth`, and `allow_*` flags for isomer enumeration.
- Use `count_stereoisomers(..., precise=False)` before enumerating stereoisomers precisely.
- Set `max_n_mols` for `dm.fragment.build` and `assemble_fragment_order`.
- Keep `singlepass=True` for BRICS fragmentation unless full decomposition is necessary.
- Restrict fuzzy scaffolding with smaller molecule sets, `n_atom_cuttoff`, `additional_templates`, and MCS timeouts in `mcs_params`.
- For reaction libraries, pre-filter reactants with `can_react` and cap product groups before downstream scoring or visualization.
