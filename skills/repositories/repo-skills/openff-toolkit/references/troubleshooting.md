# Cross-Cutting Troubleshooting

## Import or Installation Fails

Symptoms:
- `ModuleNotFoundError: No module named 'openff'`
- `PackageNotFoundError: openff.toolkit`
- compiled dependency import errors from RDKit, OpenMM, or OpenFF dependencies

Actions:
1. Prefer a conda-forge install of `openff-toolkit` instead of a minimal pip-only environment.
2. Run `../scripts/check_openff_toolkit.py --json` in the target Python.
3. If only `openff-toolkit-base` is installed, add the optional backend packages needed for the requested workflow.
4. If editing a source checkout, make sure runtime dependencies from the package recipe/environment are installed before installing the checkout.

## No Basic Cheminformatics Toolkit

Symptoms:
- warnings about no basic cheminformatics toolkits
- molecule IO, SMARTS matching, or SMILES conversion fails
- `ToolkitUnavailableException` for RDKit/OpenEye

Actions:
1. Read `../sub-skills/toolkit-backends/SKILL.md`.
2. Install RDKit for the usual free backend path.
3. Install OpenEye only when the user has the toolkit and license requirements.
4. Use explicit `toolkit_registry=` arguments for reproducibility when multiple wrappers are installed.

## Force Field File Not Found

Symptoms:
- `ForceField("openff-2.3.0.offxml")` cannot locate the file
- available force-field list is empty or missing expected OpenFF releases

Actions:
1. Run `python -c "from openff.toolkit.typing.engines.smirnoff import get_available_force_fields; print(get_available_force_fields())"`.
2. Install the OpenFF force-fields package or pass a direct `.offxml` path.
3. Do not edit molecule or topology code until force-field discovery is proven.
4. Use `../sub-skills/smirnoff-force-fields/references/troubleshooting.md` for SMIRNOFF-specific errors.

## PDB or System Preparation Fails

Symptoms:
- missing `unique_molecules`
- missing hydrogens or `CONECT` records
- unknown residues or unassigned atoms/bonds
- OpenMM residue/atom-name surprises

Actions:
1. Route to `../sub-skills/topology-and-systems/SKILL.md`.
2. Build exact OpenFF `Molecule` objects for chemically distinct HETATM species.
3. Verify explicit hydrogens, element columns, connectivity, and residue/atom naming.
4. Keep hierarchy metadata expectations package-specific; conversion tools may impose stricter assumptions than OpenFF objects do internally.

## Charge Assignment Fails

Symptoms:
- `ChargeMethodUnavailableError`
- `IncorrectNumConformersError`
- missing AmberTools, OpenEye, or NAGL
- nonintegral charge or virtual-site charge assignment errors

Actions:
1. Identify the requested charge method and wrapper requirements.
2. Use `../sub-skills/toolkit-backends/scripts/check_toolkit_backends.py --json` to inspect installed wrappers.
3. Use BuiltIn `zeros` or `formal_charge` only when scientifically appropriate.
4. For SMIRNOFF charge assignment during parameterization, read `../sub-skills/smirnoff-force-fields/references/troubleshooting.md`.

## Interchange or OpenMM Export Fails

Symptoms:
- `create_interchange()` fails after molecule/topology creation
- `create_openmm_system()` fails due missing OpenMM or Interchange pieces
- valence parameters are unassigned

Actions:
1. Confirm molecule and topology construction first.
2. Confirm the force field loads and `label_molecules()` covers the molecules.
3. Install Interchange/OpenMM dependencies required by the target export.
4. Use the SMIRNOFF sub-skill to troubleshoot missing parameters, charge handling, and handler/version issues.

## Choosing the Right Sub-Skill

- If the object is a single `Molecule`, start with molecule IO.
- If the object is a collection/system/PDB, start with topology and systems.
- If the object is an `.offxml` or `ForceField`, start with SMIRNOFF force fields.
- If the error names RDKit, OpenEye, AmberTools, NAGL, wrapper, registry, charge method, or unsupported format, start with toolkit backends.
