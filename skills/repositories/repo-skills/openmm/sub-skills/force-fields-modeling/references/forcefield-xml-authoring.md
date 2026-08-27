# ForceField XML Authoring

OpenMM force fields are XML files loaded by `ForceField(*files)`. They define atom types, residue templates, optional patches, and one or more force blocks that create OpenMM `Force` objects. This reference covers practical ffxml authoring and validation; it does not replace the custom-force sub-skill for deriving new mathematical potentials.

## Top-Level Structure

Every ffxml file has a root `ForceField` element:

```xml
<ForceField>
  <AtomTypes>
    ...
  </AtomTypes>
  <Residues>
    ...
  </Residues>
  <Patches>
    ...
  </Patches>
  ... force tags ...
</ForceField>
```

`AtomTypes`, `Residues`, `Patches`, and force tags can appear in any order, but keeping this order improves readability.

## Atom Types and Classes

Atom types are specific identifiers used to assign parameters; atom classes group related types for compact parameter tables.

```xml
<AtomTypes>
  <Type name="protein-N" class="N" element="N" mass="14.00672"/>
  <Type name="protein-H" class="H" element="H" mass="1.007947"/>
  <Type name="protein-CA" class="CT" element="C" mass="12.01078"/>
</AtomTypes>
```

Rules:

- `name` values must be unique within the loaded `ForceField`.
- `class` values may repeat across many types.
- `element` is the chemical element symbol.
- `mass` is in atomic mass units.
- Force parameter rules can refer to atoms by `type` or by `class`. Do not specify both a type and class for the same atom position in one parameter rule.

## Residue Templates

Residue templates map topology residues to atom types. Matching is based on element composition and bonding, not merely residue or atom names.

```xml
<Residues>
  <Residue name="LIG">
    <Atom name="C1" type="lig-C"/>
    <Atom name="O1" type="lig-O"/>
    <Atom name="H1" type="lig-H"/>
    <Bond atomName1="C1" atomName2="O1"/>
    <Bond atomName1="C1" atomName2="H1"/>
  </Residue>
</Residues>
```

Important child tags:

- `Atom`: atom name and atom type.
- `Bond`: intramolecular bond, preferably using `atomName1` and `atomName2` rather than deprecated index forms.
- `ExternalBond`: atom bonded to another residue, common for polymer residues.
- `Constraint`: force-field-required constraints that should always be present, independent of user `createSystem(constraints=...)` choices.
- `VirtualSite`: extra site definition for water models, lone pairs, and related particles.
- `AllowPatch`: declares patches that may modify the residue template.

Template mismatch is a common failure point. Verify atom count, elements, bonds, external bonds, hydrogens, and extra particles against actual topology residues.

## Virtual Sites and Extra Particles

Virtual-site examples use an `Atom` in the residue plus a `VirtualSite` rule:

```xml
<Residue name="HOH">
  <Atom name="O" type="tip4p-O"/>
  <Atom name="H1" type="tip4p-H"/>
  <Atom name="H2" type="tip4p-H"/>
  <Atom name="M" type="tip4p-M"/>
  <VirtualSite type="average3" siteName="M" atomName1="O" atomName2="H1" atomName3="H2"
               weight1="0.786646558" weight2="0.106676721" weight3="0.106676721"/>
  <Bond atomName1="O" atomName2="H1"/>
  <Bond atomName1="O" atomName2="H2"/>
</Residue>
```

Supported virtual-site `type` values include `average2`, `average3`, `outOfPlane`, and `localCoords`, corresponding to the standard OpenMM virtual site classes. Topologies must contain the extra particle before `createSystem()`; use `Modeller.addExtraParticles(forcefield)` for model-building workflows.

## Patches

Patches create modified templates from base templates, such as termini or disulfides.

```xml
<Patches>
  <Patch name="NTER">
    <RemoveAtom name="H"/>
    <RemoveBond atomName1="N" atomName2="H"/>
    <AddAtom name="H1" type="H"/>
    <AddAtom name="H2" type="H"/>
    <AddAtom name="H3" type="H"/>
    <AddBond atomName1="N" atomName2="H1"/>
    <AddBond atomName1="N" atomName2="H2"/>
    <AddBond atomName1="N" atomName2="H3"/>
    <RemoveExternalBond atomName="N"/>
    <ChangeAtom name="N" type="N3"/>
  </Patch>
</Patches>
```

Patch operations include `AddAtom`, `ChangeAtom`, `RemoveAtom`, `AddBond`, `RemoveBond`, `AddExternalBond`, and `RemoveExternalBond`.

Declare applicability either from residue templates:

```xml
<Residue name="ALA">
  <AllowPatch name="NTER"/>
  <AllowPatch name="CTER"/>
</Residue>
```

or from the patch:

```xml
<Patch name="NTER">
  <ApplyToResidue name="ALA"/>
</Patch>
```

Multi-residue patches use `residues="2"` and atom names prefixed with residue index, such as `1:SG` and `2:SG` for a disulfide. Multi-residue `AllowPatch` names include the patch name and index, such as `Disulfide:1`.

## Standard Force Tags

Each force tag translates XML parameter rules into an OpenMM force object. Units are OpenMM's standard ffxml units: distances in nm, energies in kJ/mol, angles in radians unless otherwise noted.

### `HarmonicBondForce`

```xml
<HarmonicBondForce>
  <Bond class1="C" class2="O" length="0.123" k="400000"/>
</HarmonicBondForce>
```

Rules apply to bonded atom pairs. Use `type1/type2` or `class1/class2`.

### `HarmonicAngleForce`

```xml
<HarmonicAngleForce>
  <Angle class1="H" class2="O" class3="H" angle="1.824218" k="836.8"/>
</HarmonicAngleForce>
```

Rules apply to bonded triples.

### `PeriodicTorsionForce`

```xml
<PeriodicTorsionForce ordering="default">
  <Proper class1="" class2="CT" class3="CT" class4="" periodicity1="3" phase1="0.0" k1="0.5"/>
  <Improper class1="N" class2="C" class3="CT" class4="O" periodicity1="2" phase1="3.14159265359" k1="4.6"/>
</PeriodicTorsionForce>
```

Use `Proper` for bonded sequences and `Improper` for central-atom impropers. Empty type/class names are wildcards. Multiple terms use `periodicity2`, `phase2`, `k2`, etc. `ordering` can be `default`, `amber`, `charmm`, or `smirnoff` for different improper conventions.

### `RBTorsionForce`

```xml
<RBTorsionForce>
  <Proper class1="CT" class2="CT" class3="OS" class4="CT" c0="2.4" c1="4.8" c2="-0.8" c3="-6.4" c4="0" c5="0"/>
</RBTorsionForce>
```

Defines Ryckaert-Bellemans torsions using `c0` through `c5`.

### `CMAPTorsionForce`

```xml
<CMAPTorsionForce>
  <Map>0.0 0.1 0.2 0.3</Map>
  <Torsion map="0" class1="" class2="CT" class3="C" class4="N" class5=""/>
</CMAPTorsionForce>
```

The `Map` size is inferred from the number of listed energy values. `Torsion` rules match five bonded atoms.

### `NonbondedForce`

```xml
<NonbondedForce coulomb14scale="0.833333" lj14scale="0.5">
  <Atom type="lig-C" charge="0.1" sigma="0.34" epsilon="0.45"/>
</NonbondedForce>
```

Every atom type must receive a unique nonbonded parameter set. `createExceptionsFromBonds()` uses the 1-4 scale factors.

### `GBSAOBCForce`

```xml
<GBSAOBCForce>
  <Atom type="lig-C" charge="0.1" radius="0.19" scale="0.72"/>
</GBSAOBCForce>
```

Defines OBC generalized Born parameters.

### `LennardJonesForce`

```xml
<LennardJonesForce lj14scale="1.0" useDispersionCorrection="True">
  <Atom type="C" sigma="0.34" epsilon="0.45"/>
  <NBFixPair type1="C" type2="O" sigma="0.30" epsilon="0.20"/>
</LennardJonesForce>
```

This is an alternative Lennard-Jones implementation using custom forces. It enables NBFIX-style pair overrides but is usually slower than `NonbondedForce`. If combined with `NonbondedForce` for Coulomb terms, set Lennard-Jones epsilon to zero in `NonbondedForce` to avoid double-counting.

## Custom Force XML Wiring

OpenMM ffxml can create custom forces with XML tags such as:

- `CustomBondForce`
- `CustomAngleForce`
- `CustomTorsionForce`
- `CustomNonbondedForce`
- `CustomGBForce`
- `CustomHbondForce`
- `CustomManyParticleForce`

Pattern:

```xml
<CustomBondForce energy="scale*k*(r-r0)^2">
  <GlobalParameter name="scale" defaultValue="0.5"/>
  <PerBondParameter name="k"/>
  <PerBondParameter name="r0"/>
  <Bond class1="C" class2="O" r0="0.123" k="400000"/>
</CustomBondForce>
```

Rules:

- Every parameter declared by a `Per...Parameter` tag must be present on every corresponding parameter rule.
- Use `GlobalParameter` for constants shared across all interactions.
- Custom expressions support standard arithmetic, many math functions, and semicolon-separated intermediate definitions.
- For detailed expression design and validation, route to `custom-forces-integrators`.

## Template Generator Concepts

Use `ForceField.registerTemplateGenerator(generator)` when a residue lacks a static template but can be parameterized dynamically. The generator must have this shape:

```python
def generator(forcefield, residue):
    # register templates and parameters, or load an ffxml file
    return True  # or False if this generator cannot handle residue
```

The generator can call:

- `forcefield.registerResidueTemplate(template)` for a generated template.
- `forcefield.loadFile(file)` for generated or cached ffxml.
- Programmatic registration methods for atom types and parameters.

Generators should be deterministic for the same residue chemistry and should avoid partially modifying a `ForceField` when returning `False`.

## Validation Checklist

Before publishing or using an ffxml file:

1. Load it with `ForceField('file.xml')` to catch XML syntax and parser errors.
2. Build or load a tiny representative topology for every residue template.
3. Run `forcefield.getMatchingTemplates(topology)` to verify intended residue-template matches.
4. Run `forcefield.getUnmatchedResidues(topology)` and require an empty list unless generators are intentionally responsible for remaining residues.
5. Call `createSystem()` with representative `constraints`, `rigidWater`, and nonbonded settings.
6. Inspect force counts and particle count on the resulting `System`.
7. For water, virtual sites, or Drude particles, verify `Modeller.addExtraParticles(forcefield)` is included in the model-building workflow.
8. For ambiguous monoatomic ions or residues with multiple valid templates, document required `residueTemplates` overrides.

## Common Authoring Mistakes

- Defining residue atom names but forgetting bonds or external bonds.
- Matching atom names while the topology's elements or bonds do not match the template.
- Using generic water XML that lacks ion parameters required by solvation.
- Mixing CHARMM or Amber family water/ion files across incompatible main force-field versions.
- Forgetting `AllowPatch` or `ApplyToResidue`, causing terminal or disulfide variants not to match.
- Creating virtual-site templates without adding extra particles to the topology.
- Using both `typeN` and `classN` on the same atom position in a parameter rule.
- Omitting required per-interaction parameter attributes for custom force tags.
- Double-counting Lennard-Jones interactions by combining `LennardJonesForce` and full-epsilon `NonbondedForce`.
