# Model Building Recipes

Use `Modeller` to make topology and coordinate edits before calling `ForceField.createSystem()`. Every editing method creates a new `Topology` and position array accessible as `modeller.topology` and `modeller.positions`.

## General Pattern

```python
pdb = PDBFile('input.pdb')
forcefield = ForceField('amber19-all.xml', 'amber19/tip3pfb.xml')
modeller = Modeller(pdb.topology, pdb.positions)

# Edit topology and positions here.

system = forcefield.createSystem(modeller.topology, nonbondedMethod=PME, nonbondedCutoff=1*nanometer, constraints=HBonds)
```

Use the edited topology and edited positions consistently. Do not build the `System` from the original topology after adding hydrogens, solvent, membranes, or extra particles.

## Add Missing Hydrogens

Basic call:

```python
variants = modeller.addHydrogens(forcefield)
```

Useful options:

- `pH=...`: selects common protonation variants for the requested pH.
- `variants=[...]`: explicit per-residue variant override; list length must equal the number of residues. Use `None` for residues that should follow default rules.
- `platform=...`: platform for hydrogen placement optimization.
- `residueTemplates={residue: 'TemplateName'}`: disambiguates matching templates.

Built-in variants include:

- Aspartic acid: `ASH` neutral, `ASP` negative.
- Cysteine: `CYS` neutral sulfhydryl, `CYX` disulfide/thiolate-like no sulfur hydrogen.
- Glutamic acid: `GLH` neutral, `GLU` negative.
- Histidine: `HID`, `HIE`, `HIP`, `HIN`.
- Lysine: `LYN` neutral, `LYS` positive.

Default behavior picks common variants at the requested pH, forces disulfide-bonded cysteine to `CYX`, and chooses neutral histidine tautomer by local hydrogen bonding. Existing atom positions are preserved. When variants are selected automatically, OpenMM adds missing hydrogens but does not remove existing ones. When a variant is explicitly specified, hydrogens can be added or removed to match it.

For nonstandard hydrogen definitions, load definitions before adding hydrogens:

```python
Modeller.loadHydrogenDefinitions('glycam-hydrogens.xml')
modeller.addHydrogens(forcefield)
```

## Add Solvent and Ions

Basic explicit-solvent workflow:

```python
modeller.addHydrogens(forcefield)
modeller.addSolvent(forcefield, model='tip3p', padding=1.0*nanometer, ionicStrength=0.1*molar)
```

`addSolvent()` fills a periodic box, removes waters that overlap the solute, neutralizes total solute charge by replacing water with ions when `neutralize=True`, then adds extra ion pairs for `ionicStrength`. Ions added for neutralization are not counted toward the requested bulk ionic strength.

Only one of `boxSize`, `boxVectors`, `padding`, or `numAdded` may be specified:

- `boxSize=Vec3(x, y, z)*nanometer`: rectangular cell dimensions.
- `boxVectors=(a, b, c)`: arbitrary periodic vectors.
- `padding=1*nanometer`: solute-centered box with requested spacing from periodic images.
- `numAdded=5000`: choose a box that adds a target number of solvent molecules plus ions.
- If none are specified, the existing topology's periodic box vectors are used; if absent, OpenMM raises an error.

Box-shape options for `padding` or `numAdded` are `cube`, `dodecahedron`, and `octahedron`. A rhombic dodecahedron is more compact than a cube for the same minimum image spacing.

Supported `model` values are `tip3p`, `spce`, `tip4pew`, `tip5p`, and `swm4ndp`. These are pre-equilibrated box templates. For related models with the same number of interaction sites, it can be reasonable to solvate with the closest supported template and then minimize using the actual force-field parameters.

Ion options:

- Positive ions: `Cs+`, `K+`, `Li+`, `Na+`, `Rb+`.
- Negative ions: `Cl-`, `Br-`, `F-`, `I-`.
- Only monovalent ions are supported by `addSolvent()`.
- Not every force-field XML has parameters for every ion; choose ions supported by the loaded water/ion file.

## Water Model Conversion and Extra Particles

Four- and five-site waters and Drude models require topology particles that are not ordinary atoms. Add or remove these after choosing the target force field:

```python
modeller.addExtraParticles(forcefield)
```

This is required for many water models with virtual sites, Drude particles, and related extra particles. It can also remove extra particles if converting from a model that has them to one that does not.

Typical conversion sequence:

```python
# Example: input contains ordinary 3-site water but target force field needs extra sites.
forcefield = ForceField('amber19-all.xml', 'amber19/tip4pew.xml')
modeller = Modeller(pdb.topology, pdb.positions)
modeller.addHydrogens(forcefield)
modeller.addExtraParticles(forcefield)
system = forcefield.createSystem(modeller.topology, nonbondedMethod=PME, constraints=HBonds)
```

If `createSystem()` reports that a water residue is missing one or more extra sites, call `addExtraParticles()` with the same force field used for `createSystem()`.

## Remove Existing Water

```python
modeller.deleteWater()
```

This removes water molecules but not necessarily ions or other small molecules. Use it when switching from explicit to implicit solvent, replacing an incompatible solvent box, or rebuilding solvent with a different water model.

## Add a Membrane

Use `addMembrane()` instead of `addSolvent()` for membrane systems. It adds lipid, solvent, and ions in one operation while preserving a membrane in the XY plane.

```python
modeller.addMembrane(
    forcefield,
    lipidType='POPC',
    minimumPadding=1.0*nanometer,
    ionicStrength=0.15*molar,
)
```

Common parameters:

- `lipidType`: supported bundled membrane types include phospholipid models represented by package data such as POPC, POPE, DOPC, DPPC, DMPC, DLPC, and DLPE.
- `membraneCenterZ`: target membrane center along Z.
- `minimumPadding`: minimum protein-to-box edge padding.
- `positiveIon`, `negativeIon`, `ionicStrength`, and `neutralize`: analogous to `addSolvent()`.
- `residueTemplates`: disambiguates residues during charge/radius determination.

The solute should already be oriented and positioned relative to the membrane before this call. OpenMM does not infer membrane-protein orientation.

## Save the Prepared Structure

For repeatable workflows, save the prepared model after all edits:

```python
with open('prepared.pdb', 'w') as handle:
    PDBFile.writeFile(modeller.topology, modeller.positions, handle)
```

Saving avoids repeating expensive or stochastic preparation and ensures later simulations start from the same topology and coordinates.

## Minimal Safe Preparation Blueprint

For a typical soluble biomolecule PDB lacking hydrogens and solvent:

```python
pdb = PDBFile('input.pdb')
forcefield = ForceField('amber19-all.xml', 'amber19/tip3pfb.xml')
modeller = Modeller(pdb.topology, pdb.positions)

modeller.addHydrogens(forcefield, pH=7.0)
modeller.addSolvent(
    forcefield,
    model='tip3p',
    padding=1.0*nanometer,
    ionicStrength=0.15*molar,
    neutralize=True,
)

system = forcefield.createSystem(
    modeller.topology,
    nonbondedMethod=PME,
    nonbondedCutoff=1.0*nanometer,
    constraints=HBonds,
    rigidWater=True,
)
```

Check compatibility points before running dynamics:

- The water/ion XML belongs to the same force-field family as the main XML.
- The `model` used in `addSolvent()` is compatible with the water XML, or intentionally a close pre-equilibrated template.
- The topology has periodic box vectors before using `PME`.
- All hydrogens and extra particles required by the target force field are present.
- `forcefield.getUnmatchedResidues(modeller.topology)` returns an empty list or all remaining residues are intentionally handled by template generators.
