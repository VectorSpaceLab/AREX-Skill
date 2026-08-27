# SMIRNOFF Troubleshooting

Use this guide to diagnose failures while loading, modifying, labeling, serializing, or applying SMIRNOFF force fields.

## Force Field File Not Found

Symptoms:

- `ForceField("openff-2.3.0.offxml")` cannot locate the named OFFXML.
- `get_available_force_fields()` returns an empty list or lacks the requested file.

Likely cause: the package that provides OFFXML files is not installed or does not expose the `openforcefield.smirnoff_forcefield_directory` entry point.

Actions:

1. Run `get_available_force_fields()` and choose an available name.
2. Use `get_available_force_fields(full_paths=True)` to confirm discovery paths.
3. Use a local `.offxml` path when the file is not package-distributed.
4. Preserve the requested source filename in error reports; do not rewrite molecule/topology code for this failure.

## SMIRNOFF Version or Spec Errors

Symptoms:

- `SMIRNOFFVersionError` mentioning the file version and supported version range.
- Errors for missing section `version` attributes, unsupported aromaticity model, or invalid SMIRNOFF XML structure.

Actions:

- Prefer a toolkit version that supports the OFFXML spec version.
- Use `disable_version_check=True` only for force-field development or controlled migration, not for routine user workflows.
- Preserve the original OFFXML and write migrated output to a new file.
- If `allow_cosmetic_attributes=False` rejects non-spec attributes, reload with `allow_cosmetic_attributes=True` only when those attributes are intentionally cosmetic.

## Unknown or Missing Handler Tags

Symptoms:

- `KeyError: Cannot find a registered parameter handler class for tag ...`
- Loading a custom OFFXML fails for a custom top-level tag.

Actions:

- Check whether the tag is built in (`Bonds`, `Angles`, `vdW`, `VirtualSites`, etc.).
- For custom tags, load the force field with `load_plugins=True` after the plugin package is installed.
- If not installed as a plugin, pass the custom handler class through `parameter_handler_classes` and ensure it subclasses `ParameterHandler`.
- Do not rename unknown tags to built-in tags unless the science and attributes are equivalent.

## Duplicate or Incompatible Parameters

Symptoms:

- Duplicate parameter errors while adding parameters.
- Incompatible tag/handler errors while loading multiple sources or combining force fields.
- System creation succeeds for one source but fails after `combine`.

Actions:

- Inspect handler-level attributes such as cutoffs, methods, scale factors, and versions; repeated sections must be compatible.
- Remember source order: later sources append parameters with higher precedence.
- Label representative molecules before and after combining to confirm intended assignments.
- Keep both original sources and serialize combined output only after validation.

## Missing Parameters or Unassigned Valence Terms

Symptoms:

- System creation errors for missing bonds, angles, torsions, vdW, or charge terms.
- Labeling shows a handler with zero matches where coverage was expected.

Actions:

- Run `force_field.label_molecules(topology)` before `create_interchange` or `create_openmm_system`.
- Confirm the molecule has expected bond orders, formal charges, aromaticity, stereochemistry, and explicit/implicit hydrogens before topology construction.
- Avoid deleting broad/root parameters unless replacement coverage is proven.
- If a parameter edit changed `smirks`, label the same molecule before and after the edit.

## Toolkit or Charge Assignment Unavailable

Symptoms:

- Charge assignment fails for AM1-BCC, Wiberg bond orders, or NAGL charges.
- Errors mention unavailable OpenEye, AmberTools, NAGL, or toolkit registry wrappers.

Actions:

- Inspect the active toolkit registry and available wrappers.
- Use force fields compatible with available charge handlers.
- For simple smoke tests, use molecules/force fields that can run with available RDKit and built-in wrappers, or use precomputed `charge_from_molecules` when scientifically valid.
- Route environment installation and backend selection to the toolkit-backends sub-skill.

## Virtual Sites and Partial Charges

Symptoms:

- `get_partial_charges(molecule)` fails with a virtual-site charge error.
- Atom-only charges do not account for off-atom virtual-site charges.

Actions:

- Use `force_field.create_interchange(molecule.to_topology())` and inspect the electrostatics collection when virtual sites are present.
- Do not assign virtual-site force-field charges directly to `Molecule.partial_charges` as if they were atom-only charges.
- In labels, expect `VirtualSites` matches to map to lists of parameter types.

## Interchange or OpenMM Dependency Errors

Symptoms:

- `create_interchange` fails because `openff.interchange` is unavailable.
- `create_openmm_system` fails because OpenMM or Interchange export dependencies are unavailable.

Actions:

- First test `force_field.label_molecules(topology)` to separate assignment from export.
- Then test `force_field.create_interchange(topology)`.
- Only after Interchange succeeds, test `force_field.create_openmm_system(topology)`.
- Treat dependency installation as an environment/backend task rather than changing the OFFXML.

## Nonintegral Charges

Symptoms:

- System creation rejects charges that do not sum to an integer.

Actions:

- Check molecule formal charges and the force-field charge model.
- Set `allow_nonintegral_charges=True` only when the requested workflow explicitly allows it and the downstream engine can handle the result.
- Prefer fixing the molecule identity or charge source over suppressing the check.
