# ForceField API and Bundled Data

This reference distills OpenMM force-field and model-parameterization behavior for future agents. It is self-contained and should be used instead of relying on the original source tree.

## Core Imports

```python
from openmm import *
from openmm.app import *
from openmm.unit import *
```

Common live signatures:

- `ForceField(*files)` loads one or more bundled or user-provided XML files.
- `PDBFile(file, extraParticleIdentifier='EP')` loads PDB topology and positions.
- `Modeller(topology, positions)` edits topology and coordinates before simulation.
- `Simulation(topology, system, integrator, platform=None, platformProperties=None, state=None)` consumes the final topology/system/positions in a simulation workflow.

## Choosing Bundled Force Fields

Most OpenMM workflows load one main biopolymer XML plus one water/ion or implicit-solvent XML. Files listed here are package data names passed to `ForceField(...)`, not file-system paths.

### Current Amber Families

Use Amber19 for modern protein/nucleic/lipid systems when appropriate:

```python
forcefield = ForceField('amber19-all.xml', 'amber19/tip3pfb.xml')
```

Important Amber19 components:

- `amber19-all.xml`: convenience bundle for protein `ff19SB`, DNA `OL21`, RNA `OL3`, and lipid `lipid21`.
- `amber19/protein.ff19SB.xml`, `amber19/DNA.OL21.xml`, `amber14/RNA.OL3.xml`, `amber19/lipid21.xml`: finer-grained components.
- `amber19/tip3p.xml`, `amber19/tip3pfb.xml`, `amber19/tip4pew.xml`, `amber19/tip4pfb.xml`, `amber19/spce.xml`, `amber19/opc.xml`, `amber19/opc3.xml`: water plus compatible ions.
- `amber14/GLYCAM_06j-1.xml`: carbohydrates and glycosylated proteins; input residue names must follow GLYCAM naming. Use `Modeller.loadHydrogenDefinitions('glycam-hydrogens.xml')` before adding GLYCAM hydrogens.

Amber14 remains available:

```python
forcefield = ForceField('amber14-all.xml', 'amber14/tip3p.xml')
```

Amber14 components include `amber14/protein.ff14SB.xml`, `amber14/DNA.OL15.xml`, `amber14/DNA.bsc1.xml`, `amber14/RNA.OL3.xml`, `amber14/lipid17.xml`, and the same style of `amber14/...` water/ion files.

Avoid mixing generic water files such as `tip3p.xml` with Amber19/Amber14 systems that contain ions. The Amber-family water files include ion parameters; the generic files may not.

### CHARMM Families

Modern CHARMM36 support uses:

```python
forcefield = ForceField('charmm36_2024.xml', 'charmm36_2024/water.xml')
```

Common CHARMM files:

- `charmm36_2024.xml`: protein, DNA, RNA, lipids, carbohydrates, and small molecules.
- `charmm36_2024/water.xml`, `spce.xml`, `tip3p-pme-b.xml`, `tip3p-pme-f.xml`, `tip4pew.xml`, `tip4p2005.xml`, `tip5p.xml`, `tip5pew.xml`: solvent/ion files designed for `charmm36_2024.xml`.
- Older `charmm36.xml` pairs with solvent files under `charmm36/`.

Do not mix `charmm36_2024/` solvent XML with the older `charmm36.xml` family, or vice versa. CHARMM uses patches extensively. Patched residues such as ACE/NME termini must appear as single residues that match the expected patched template; if structures come from CHARMM-GUI-like workflows, loading the PSF directly is often more reliable than trying to infer all residue and bond details from PDB.

### Polarizable and AMOEBA Families

AMOEBA explicit solvent usually loads a single force-field file:

```python
forcefield = ForceField('amoeba2018.xml')
```

Implicit Generalized Kirkwood variants add a `_gk` file such as `amoeba2018_gk.xml`. Older `amoeba2013.xml` and `amoeba2009.xml` are compatibility options, not preferred defaults.

CHARMM polarizable files include `charmm_polar_2023.xml`, `charmm_polar_2019.xml`, and `charmm_polar_2013.xml`. Polarizable CHARMM/Drude workflows require extra particles in the topology and a Drude-capable integrator in the simulation layer.

### Implicit Solvent XML

For Amber/CHARMM-style `ForceField` workflows, implicit solvent is selected by adding an implicit XML:

```python
forcefield = ForceField('amber19-all.xml', 'implicit/gbn2.xml')
system = forcefield.createSystem(topology, nonbondedMethod=NoCutoff)
```

Available implicit files include:

- `implicit/hct.xml`: HCT GBSA.
- `implicit/obc1.xml`: OBC I.
- `implicit/obc2.xml`: OBC II.
- `implicit/gbn.xml`: GBn.
- `implicit/gbn2.xml`: GBn2.

Implicit solvent supports `NoCutoff`, `CutoffNonPeriodic`, and `CutoffPeriodic`; periodic artifacts usually make non-periodic settings preferable.

### Generic and Older Files

OpenMM also bundles older force fields and generic water models for compatibility: `amber96.xml`, `amber99sb.xml`, `amber99sbildn.xml`, `amber99sbnmr.xml`, `amber03.xml`, `amber10.xml`, OBC variants, and generic `tip3p.xml`, `tip3pfb.xml`, `tip4pew.xml`, `tip4pfb.xml`, `tip5p.xml`, `spce.xml`, `swm4ndp.xml`, `opc.xml`, `opc3.xml`.

Use older files mainly for reproducing older results or tests. When using Amber19/Amber14/CHARMM36, prefer their family-specific water/ion files over generic water files.

## `ForceField.createSystem()` Options

Typical explicit-solvent call:

```python
system = forcefield.createSystem(
    topology,
    nonbondedMethod=PME,
    nonbondedCutoff=1.0*nanometer,
    constraints=HBonds,
    rigidWater=True,
)
```

Important parameters:

- `topology`: final OpenMM `Topology`, after `Modeller` edits.
- `nonbondedMethod`: one of `NoCutoff`, `CutoffNonPeriodic`, `CutoffPeriodic`, `Ewald`, `PME`, or `LJPME`.
- `nonbondedCutoff`: cutoff distance, commonly `1*nanometer` for PME examples.
- `constraints`: `None`, `HBonds`, `AllBonds`, or `HAngles`; force-field-required constraints are always added.
- `rigidWater`: `True` makes water fully rigid; `None` uses the water model's default behavior.
- `removeCMMotion`: adds `CMMotionRemover` by default.
- `hydrogenMass`: repartitions mass from heavy atoms to bonded hydrogens, except water hydrogens when `rigidWater` is used.
- `residueTemplates`: maps specific `Residue` objects to template names when multiple templates can match, such as alternate ion oxidation states.
- `ignoreExternalBonds`: useful for topology fragments whose chains are not chemically terminated; may introduce template ambiguity.
- `switchDistance`: enables Lennard-Jones switching when supported.
- `flexibleConstraints`: includes parameters for constrained degrees of freedom.
- `drudeMass`: mass assigned to Drude particles in Drude force fields.
- Additional keyword arguments may be force-field-specific, such as implicit solvent dielectric or SASA options.

Match nonbonded settings to the topology:

- Use `PME` or `LJPME` only when the topology has periodic box vectors.
- If adding solvent with `Modeller.addSolvent()`, use the same edited topology and positions for `createSystem()` and later `Simulation`.
- For implicit solvent files, avoid PME and typical explicit-solvent periodic assumptions.

## Diagnosing Template Matching Before Simulation

OpenMM exposes experimental helper APIs that are useful for debugging prepared systems:

```python
unmatched = forcefield.getUnmatchedResidues(topology)
for residue in unmatched:
    print(residue.index, residue.name)
```

```python
templates = forcefield.getMatchingTemplates(topology)
for residue, template in zip(topology.residues(), templates):
    print(residue.index, residue.name, template.name)
```

`generateTemplatesForUnmatchedResidues(topology)` can create empty residue templates with atom names, elements, and connectivity copied from unmatched residues. Treat these as scaffolds: atom types and parameters still must be assigned and registered.

Use `registerTemplateGenerator(generator)` for small molecules or modified residues when an external parameterization tool can generate templates on demand. The generator is called as `success = generator(forcefield, residue)` and must either register templates/parameters or return `False` without modifying the `ForceField`.

## Parameterized Input Formats

When a setup package already parameterized the system, do not use `ForceField(*xml)` for the same topology. Load the parameterized files and call their own `createSystem()` method.

### AMBER

```python
inpcrd = AmberInpcrdFile('input.inpcrd')
prmtop = AmberPrmtopFile('input.prmtop', periodicBoxVectors=inpcrd.boxVectors)
system = prmtop.createSystem(nonbondedMethod=PME, nonbondedCutoff=1*nanometer, constraints=HBonds)
```

AMBER periodic box vectors should usually come from the coordinate/restart file. OpenMM supports new-style `prmtop` files; old-style AMBER 7-predecessor files are not supported. For AMBER implicit solvent, pass `implicitSolvent=HCT`, `OBC1`, `OBC2`, `GBn`, or `GBn2` to `prmtop.createSystem()` rather than loading implicit XML.

### GROMACS

```python
gro = GromacsGroFile('input.gro')
top = GromacsTopFile('input.top', periodicBoxVectors=gro.getPeriodicBoxVectors(), includeDir='gromacs-topology-include-directory')
system = top.createSystem(nonbondedMethod=PME, nonbondedCutoff=1*nanometer, constraints=HBonds)
```

GROMACS `.top` files often include external force-field files. Set `includeDir` to the directory containing those includes when they are not in the default GROMACS installation location.

### CHARMM

```python
psf = CharmmPsfFile('input.psf')
pdb = PDBFile('input.pdb')
params = CharmmParameterSet('topology.rtf', 'parameters.prm', 'stream.str')
system = psf.createSystem(params, nonbondedMethod=PME, nonbondedCutoff=1*nanometer, constraints=HBonds)
```

Both CHARMM and XPLOR PSF variants are supported. Load all needed `.rtf`, `.top`, `.prm`, `.par`, `.inp`, and `.str` parameter files into `CharmmParameterSet`. Prefer PSF-based loading when PDB residue naming or bond records are not enough to reconstruct patched CHARMM topology.

### Tinker

```python
tinker = TinkerFiles('system.xyz', ['system.key', 'amoeba.prm'])
system = tinker.createSystem(nonbondedMethod=PME, nonbondedCutoff=0.7*nanometer, vdwCutoff=0.9*nanometer)
```

OpenMM's Tinker path is for AMOEBA-style systems. The `TinkerFiles` object provides `topology` and `positions` for later simulation setup.

## Small Molecules and Nonstandard Residues

For small molecules, OpenMM's built-in biopolymer force fields usually need help from `openmmforcefields` or another parameterization workflow. Two common patterns are:

- Register a template generator, such as a SMIRNOFF or GAFF generator, on a `ForceField`.
- Use a `SystemGenerator` that combines biopolymer force fields, small-molecule force fields, and a parameter cache.

Exact molecule identity, protonation, stereochemistry, tautomer state, and atom/bond topology must match between the molecule object and the OpenMM topology. If they do not, template generation or matching will fail even if the residue name looks correct.
