# Interaction Troubleshooting

This guide fixes interaction setup and parameter issues. If the failure happens while converting inputs, selecting residues, running trajectories, exporting results, or plotting, route to `../molecules-and-io/`, `../fingerprints/`, or `../visualization/` as appropriate.

## Unknown interaction `NameError`

Symptoms:

- `NameError: Unknown interaction(s) in 'interactions': ...`
- `NameError: Unknown interaction(s) in 'parameters': ...`

Recovery:

1. Run `python scripts/list_interactions.py --include-bridged`.
2. Check exact capitalization: use `HBAcceptor`, not `hbacceptor`; use `VdWContact`, not `VDWContact`.
3. Remove stale `parameters` keys for interactions that are no longer selected.
4. Add `--show-hidden` only when developing custom classes; hidden base names are not normal fingerprint choices.
5. For `WaterBridge`, include `--include-bridged` when listing names and pass a required nested parameter dictionary.

## Explicit vs implicit hydrogen mismatch

Symptoms:

- `ValueError` mentioning interactions requested in implicit-hydrogen form but parameterized for explicit-hydrogen form.
- Explicit H-bonds missing in heavy-atom-only structures.
- Implicit and explicit H-bond counts differ.

Recovery:

```python
# Wrong when implicit_hydrogens=True:
# prolif.Fingerprint(["HBDonor"], implicit_hydrogens=True,
#                    parameters={"HBDonor": {"distance": 4.0}})

# Correct:
fp = prolif.Fingerprint(
    ["HBDonor", "HBAcceptor"],
    implicit_hydrogens=True,
    parameters={"ImplicitHBDonor": {"distance": 4.0}},
)
```

Guidance:

- Use explicit `HBDonor`/`HBAcceptor` when hydrogens are present and meaningful.
- Use `implicit_hydrogens=True` or `ImplicitHBDonor`/`ImplicitHBAcceptor` when donor hydrogens are omitted or should be treated flexibly.
- If implicit H-bonds produce many hits, keep geometry checks enabled and inspect `*_atom_angle_deviation`, `*_plane_angle`, and `vina_hbond_potential` metadata.
- If geometry checks fail because local heavy-atom context is absent, first verify molecule preparation in `../molecules-and-io/`; only then consider `ignore_geometry_checks=True`.

## Water bridge setup errors

Symptoms:

- `ValueError: Must specify settings for bridged interaction 'WaterBridge'`.
- `ValueError: order must be greater than 0`.
- `ValueError: min_order cannot be greater than order`.
- `WaterBridge` does not appear in `Fingerprint.list_available()`.

Recovery:

```python
fp = prolif.Fingerprint(
    ["HBDonor", "WaterBridge"],
    parameters={"WaterBridge": {"water": water_selection, "order": 1}},
)
```

Checklist:

- Use `Fingerprint.list_available(show_bridged=True)` to see `WaterBridge`.
- Provide `parameters={"WaterBridge": {"water": ...}}`; `water` is required.
- Set `order >= 1`; set `min_order <= order`.
- Use MDAnalysis water AtomGroups for trajectory runs or ProLIF water Molecules/iterables for iterable pose workflows.
- Keep water selection and molecule splitting questions in `../molecules-and-io/`.
- For mixed normal and bridged fingerprints, validate both the normal interaction keys and `WaterBridge` nested keys.

## Invalid VdW tolerance or missing radii

Symptoms:

- `ValueError: `tolerance` must be 0 or positive`.
- `ValueError` mentioning van der Waals radius not found.

Recovery:

```python
fp = prolif.Fingerprint(
    ["VdWContact"],
    parameters={
        "VdWContact": {
            "tolerance": 0.0,
            "preset": "rdkit",  # or "csd"
            "vdwradii": {"Co": 2.4},
        }
    },
)
```

Guidance:

- Never pass negative `tolerance`; it expands matching only when non-negative.
- The `mdanalysis` preset is limited; try `rdkit` or `csd` for broader element coverage.
- Use `vdwradii` to override or add element symbols with first-letter uppercase keys.
- If atom symbols look wrong, inspect input conversion through `../molecules-and-io/` before overriding radii.

## Missing geometry metadata

Symptoms:

- Metadata has `indices` and `distance` but no expected angle/deviation keys.
- `best(...)` returns `None` for a residue pair expected to interact.
- Implicit H-bond metadata lacks `donor_atom_angles` or `acceptor_atom_angles`.

Recovery:

1. Confirm the selected interaction actually measures that geometry. Distance-only classes only store distance.
2. Call the direct method with `metadata=True` on one residue pair.
3. For implicit H-bonds, check whether `ignore_geometry_checks=True` was used or whether water residues bypassed part of the geometry checks.
4. Verify residues contain conformers, coordinates, bond orders, and neighboring heavy atoms.
5. If the issue is input chemistry or coordinates, route to `../molecules-and-io/`.

## False positives from omitted hydrogens

Symptoms:

- Explicit H-bond definitions are too sparse because hydrogens are absent.
- Implicit H-bond definitions are too permissive.
- Hydrogen-bond counts disagree with visualization or chemical expectation.

Recovery:

- For heavy-atom-only data, prefer implicit H-bonds rather than weakening explicit H-bond SMARTS.
- Keep `ignore_geometry_checks=False` unless a documented molecule-preparation limitation prevents geometry checks.
- Tighten `distance`, `tolerance_dev_daa`, and `tolerance_dev_dpa` before changing SMARTS.
- Inspect `vina_hbond_potential`; low values indicate weak or unlikely implicit H-bonds.
- If exact hydrogen orientations matter, prepare explicit hydrogens in `../molecules-and-io/` and use `HBDonor`/`HBAcceptor`.

## Overbroad residue search

Symptoms:

- Too many residue pairs are evaluated.
- Fingerprints include distal residues.
- Runtime is unexpectedly high after interaction setup.

Recovery:

- For full execution, use residue restrictions and execution guidance in `../fingerprints/`.
- Tune `vicinity_cutoff` only when automatic nearby-residue search is too broad or too narrow.
- Pass an `ignore` predicate only for chemically invalid pairs such as self-interactions or adjacent residues.
- Do not fix bad ligand/protein/water selections by adding interaction filters; repair selections in `../molecules-and-io/`.

## Count vs first-match confusion

Symptoms:

- User expects every hydrophobic contact but sees one contact per residue pair/interaction.
- Direct method returns one metadata dictionary instead of all matches.
- DataFrame values are booleans when counts are expected.

Recovery:

```python
fp = prolif.Fingerprint(["Hydrophobic"], count=True)
all_contacts = fp.hydrophobic.all(lig_res, prot_res, metadata=True)

# After running the fingerprint:
# df = fp.to_dataframe(count=True)
# cvs = fp.to_countvectors()
```

Guidance:

- `count=False` stores first matches and is faster.
- `count=True` stores all matching atom combinations and enables count exports.
- `Fingerprint.metadata` returns tuples of metadata; with `count=False`, the tuple wraps the first match.
- If counts disappear during export, route to `../fingerprints/` and verify `to_dataframe(count=True)` or countvector usage.

## Water bridge metadata surprises

Symptoms:

- `WaterBridge` entries have unfamiliar metadata keys.
- Higher-order bridges have suffixed distance/angle fields.
- Water residue identity appears duplicated or confusing.

Recovery:

- Use `interaction_data.metadata["water_residues"]` for the bridge path.
- Use `interaction_data.metadata["order"]` to filter bridge length.
- Use `ligand_role` and `protein_role` to understand H-bond direction at each end.
- For `order >= 2`, expect suffixed edge metrics for water-water and water-protein steps.
- If water identities are wrong, inspect water molecule/residue preparation in `../molecules-and-io/`.

## Decision checklist before escalating

- `list_interactions.py --include-bridged --details <names>` confirms the names and signatures.
- Top-level `parameters` keys exactly match selected class names.
- `implicit_hydrogens=True` uses implicit parameter keys.
- `WaterBridge` has `water`, valid `order`, and valid `min_order`.
- `VdWContact` has non-negative tolerance and adequate radii preset/overrides.
- `count=True` is set when multiple atom-level matches are expected.
- Input conversion, execution/export, and plotting concerns are routed to the appropriate sibling sub-skill.
