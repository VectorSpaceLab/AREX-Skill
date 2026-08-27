# Force Fields and Modeling Troubleshooting

This guide focuses on errors before production dynamics: force-field selection, `Modeller` preparation, residue-template matching, and parameterized input loading.

## `No template found for residue ...`

This means `ForceField.createSystem()` could not match a topology residue to any residue template after trying registered generators.

Use a staged diagnosis:

```python
unmatched = forcefield.getUnmatchedResidues(topology)
for residue in unmatched:
    print(residue.index, residue.name, [atom.name for atom in residue.atoms()])
```

Then try:

```python
templates = forcefield.getMatchingTemplates(topology)
```

If matching fails, the exception often includes specific clues. Interpret them as follows:

- `missing ... H atom`: run `Modeller.addHydrogens(forcefield)` or provide explicit variants for termini/protonation.
- `missing ... extra site`: run `Modeller.addExtraParticles(forcefield)` with the same target force field.
- `extra site too many`: remove or convert extra particles with `Modeller.addExtraParticles()` using the target force field, or rebuild water.
- `contains elements not supported by any template`: choose a force field that covers those residues, register a template generator, or load parameterized inputs.
- `set of atoms is similar ... but missing/too many`: check protonation, atom deletion, alternate locations, residue naming, and whether the chosen force field supports that residue.
- `missing ... bond` or `bond too many`: check `CONECT` records, topology construction, disulfide bonds, water H-H bonds, and external bonds.
- `externally bonded atoms ... missing`: the residue may be a chain fragment or missing terminal capping group. Consider `ignoreExternalBonds=True` for fragments, but resolve ambiguities with `residueTemplates`.
- `connectivity is different`: atom composition may match a template while the bond graph does not; inspect bonds, not just atom names.

## Missing Hydrogens and Terminal Variants

Symptoms:

- Template mismatch involving missing H atoms.
- Wrong protonation for HIS/ASP/GLU/LYS/CYS.
- Terminal residues fail after capping or truncation.

Fix pattern:

```python
modeller = Modeller(pdb.topology, pdb.positions)
variants = modeller.addHydrogens(forcefield, pH=7.0)
```

Use explicit `variants` when the default pH-based guess is not chemically appropriate. For a topology fragment, either cap termini chemically or use `ignoreExternalBonds=True` cautiously. If a force field uses nonstandard residue names or patched terminal residues, ensure the input topology represents the expected residue and bond structure.

GLYCAM carbohydrate workflows require GLYCAM naming and often need:

```python
Modeller.loadHydrogenDefinitions('glycam-hydrogens.xml')
```

## Water Model and Ion Mismatches

Symptoms:

- `No template found` for `HOH`.
- Missing extra site(s) for water.
- Ions fail to parameterize after `addSolvent()`.
- System builds with the wrong number of particles for the desired water model.

Checklist:

- Use family-specific water/ion XML with Amber19/Amber14/CHARMM36; do not use generic `tip3p.xml` when ion parameters are needed for those families.
- Ensure `addSolvent(model=...)` is compatible with the target water XML. Supported model names are `tip3p`, `spce`, `tip4pew`, `tip5p`, and `swm4ndp`.
- Run `modeller.addExtraParticles(forcefield)` before `createSystem()` for four-site, five-site, Drude, or other extra-particle models.
- If replacing water, call `modeller.deleteWater()` before adding new solvent.
- Choose ions supported by the loaded water/ion file. `addSolvent()` supports monovalent `Cs+`, `K+`, `Li+`, `Na+`, `Rb+`, `Cl-`, `Br-`, `F-`, and `I-`, but the force field may not parameterize all of them.

## Constraints and `rigidWater`

Symptoms:

- Unexpected number of constraints.
- Hydrogen mass repartitioning does not affect water hydrogens.
- Water flexibility differs from expectations.

Rules:

- `constraints=HBonds`, `AllBonds`, `HAngles`, or `None` controls optional constraints.
- Constraints explicitly defined inside the force field are always included.
- `rigidWater=True` makes water fully rigid regardless of `constraints`.
- `rigidWater=None` uses the water model's default behavior.
- `hydrogenMass` transfers mass from heavy atoms to bonded hydrogens but not water hydrogens when rigid water is used.
- `flexibleConstraints=True` adds force parameters for constrained degrees of freedom.

## Nonbonded Method, Cutoff, and Periodic Box Problems

Symptoms:

- PME errors on non-periodic topologies.
- `addSolvent()` complains no box size or padding was specified.
- Implicit solvent behaves unexpectedly with periodic options.

Checklist:

- Use `PME`, `Ewald`, or `LJPME` only when topology box vectors are present.
- After `addSolvent()` or `addMembrane()`, use `modeller.topology`, which has periodic box vectors.
- If input PDB lacks a box, pass `padding`, `boxSize`, `boxVectors`, or `numAdded` to `addSolvent()`.
- Specify at most one of `boxSize`, `boxVectors`, `padding`, and `numAdded`.
- For implicit solvent XML, use `NoCutoff`, `CutoffNonPeriodic`, or carefully justified `CutoffPeriodic`; do not use PME.
- Keep cutoff distances as unit-bearing quantities, such as `1.0*nanometer`.

## Membrane Preparation Issues

Symptoms:

- Lipids overlap the protein.
- Protein is inserted at an unexpected orientation.
- User expects separate solvation after membrane addition.

Rules:

- `addMembrane()` adds membrane, solvent, and ions in one call; do not call `addSolvent()` afterward unless intentionally rebuilding solvent.
- The membrane is in the XY plane and the solute must already be oriented/positioned correctly.
- Use `minimumPadding` and ion options similarly to solvent workflows.
- Ensure the selected force field supports both the protein and the chosen lipid type.

## AMBER Input Problems

Use `AmberPrmtopFile` and `AmberInpcrdFile` when the system is already parameterized.

Common fixes:

- Pass `periodicBoxVectors=inpcrd.boxVectors` to `AmberPrmtopFile` for periodic systems.
- Use `prmtop.createSystem(...)`, not `ForceField.createSystem(...)`.
- Old-style AMBER `prmtop` files are unsupported; regenerate a new-style topology if needed.
- For AMBER implicit solvent, pass `implicitSolvent=OBC2` or another AMBER implicit option to `prmtop.createSystem()`.

## GROMACS Input Problems

Use `GromacsGroFile` for coordinates and `GromacsTopFile` for topology.

Common fixes:

- Pass `periodicBoxVectors=gro.getPeriodicBoxVectors()` when the `.gro` has periodic vectors.
- Set `includeDir` when the `.top` references force-field includes outside the current working directory.
- Use `top.createSystem(...)`, not `ForceField.createSystem(...)`.
- Confirm all `#include` files and molecule type definitions are available and compatible.

## CHARMM Input Problems

Use PSF plus coordinates and a `CharmmParameterSet` when CHARMM-style setup has already defined topology and parameters.

Common fixes:

- Load all relevant `.rtf`, `.top`, `.prm`, `.par`, `.inp`, and `.str` files into `CharmmParameterSet`.
- Use `psf.createSystem(params, ...)`, not `ForceField.createSystem(...)`.
- For files from CHARMM-GUI-like tools, prefer the PSF path because PDB alone may not contain enough standard residue, patch, and bond information.
- Watch for malformed PDB `CONECT` records, missing disulfide bonds, and non-chemical water H-H bonds.

## Tinker Input Problems

Use `TinkerFiles('system.xyz', ['system.key', 'forcefield.prm'])` for supported AMOEBA-style Tinker systems.

Common fixes:

- Include all needed `.key` and `.prm` files in the list.
- Use `tinker.createSystem(...)` and `tinker.topology`/`tinker.positions` for later simulation setup.
- Do not assume arbitrary Tinker force fields are supported; OpenMM's route is AMOEBA-focused.

## Unsupported Small Molecules or Modified Residues

Symptoms:

- Standard protein/DNA/RNA force field loads, but ligand residues are unmatched.
- A residue name matches a template but atom/bond identity does not.

Options:

- Register a template generator, such as one from `openmmforcefields`, for small molecules.
- Use a `SystemGenerator` workflow when many small molecules require consistent parameterization and caching.
- Convert the entire system through AMBER, CHARMM, GROMACS, or Tinker and load parameterized files.
- Author a static ffxml residue template and validate it with `getMatchingTemplates()` and `createSystem()`.

Check exact protonation, tautomer, stereochemistry, atom names, elements, and bond order before blaming OpenMM template matching.

## App Data Lookup

`ForceField('name.xml')`, `Modeller.loadHydrogenDefinitions('name.xml')`, and water-box model names resolve package data bundled with OpenMM. If a file name fails:

- Confirm spelling and directory prefix, such as `amber19/tip3pfb.xml` rather than `tip3pfb.xml` when using Amber19 ions.
- Confirm the installed OpenMM package version includes that file.
- For custom XML files, pass a valid readable file path or file-like object from the user's working context.
- Avoid hard-coding machine-specific installation paths in reusable code.

## Quick Isolation Procedure

When a preparation workflow fails, reduce it to this order:

1. Load coordinates/topology only.
2. Load the intended `ForceField` XML set.
3. Print `getUnmatchedResidues(original_topology)`.
4. Add hydrogens and print unmatched residues again.
5. Add/remove extra particles and print unmatched residues again.
6. Add solvent or membrane only after the solute can be parameterized.
7. Call `createSystem()` on the edited topology.
8. If failure persists for one residue type, create a tiny topology or PDB fragment for just that residue and validate its template or generator.
