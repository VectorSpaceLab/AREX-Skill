# SMIRNOFF ForceField API Reference

This reference captures the OpenFF Toolkit SMIRNOFF APIs verified for the local package version used during skill generation. It is intended for agents using the public toolkit API, not for editing toolkit internals.

## Imports

```python
from openff.toolkit import ForceField, Molecule, Topology, unit
from openff.toolkit.typing.engines.smirnoff import get_available_force_fields
from openff.toolkit.typing.engines.smirnoff.parameters import BondHandler, vdWHandler
```

`ForceField` is exposed from `openff.toolkit` and backed by `openff.toolkit.typing.engines.smirnoff.forcefield.ForceField`.

## Verified ForceField Signatures

```python
ForceField(
    *sources,
    aromaticity_model="OEAroModel_MDL",
    parameter_handler_classes=None,
    parameter_io_handler_classes=None,
    disable_version_check=False,
    allow_cosmetic_attributes=False,
    load_plugins=False,
)
```

- `sources` may be installed OFFXML names, file paths, file-like objects, or strings containing SMIRNOFF XML.
- Multiple sources are parsed in order. Later compatible duplicate sections append parameters with higher precedence.
- Only the `OEAroModel_MDL` aromaticity model is supported by this toolkit branch.
- `disable_version_check=True` is for force-field development only; avoid it when preserving user input fidelity matters.
- `allow_cosmetic_attributes=True` retains non-spec attributes in loaded files and can preserve them through serialization.
- `load_plugins=True` loads installed `ParameterHandler` plugin entry points.

Other verified APIs:

```python
ForceField.create_interchange(
    topology,
    toolkit_registry=None,
    charge_from_molecules=None,
    partial_bond_orders_from_molecules=None,
    allow_nonintegral_charges=False,
)
ForceField.create_openmm_system(
    topology,
    *,
    toolkit_registry=None,
    charge_from_molecules=None,
    partial_bond_orders_from_molecules=None,
    allow_nonintegral_charges=False,
)
ForceField.label_molecules(topology)
ForceField.get_parameter_handler(tagname, handler_kwargs=None, allow_cosmetic_attributes=False)
ForceField.register_parameter_handler(parameter_handler)
ForceField.deregister_parameter_handler(handler)
ForceField.to_file(filename, io_format=None, discard_cosmetic_attributes=False)
ForceField.parse_sources(sources, allow_cosmetic_attributes=True)
ForceField.combine(other)
ForceField.get_partial_charges(molecule, **kwargs)
get_available_force_fields(full_paths=False)
```

## Installed Force Field Discovery

`get_available_force_fields(full_paths=False)` returns `.offxml` file names discovered through the `openforcefield.smirnoff_forcefield_directory` package entry point. With `full_paths=True`, it returns absolute file paths. The usual source of installed OFFXML files is the `openff-forcefields` package.

Discovery failure means no package has advertised OFFXML directories; it is not a `Molecule` or `Topology` error. Use a local `.offxml` path or install a force-field package in the active environment.

## Handler Model

A `ForceField` contains `ParameterHandler` objects keyed by SMIRNOFF tag names. Handlers own ordered `ParameterType` collections and know how to assign their parameters to a topology.

Common built-in handler tags/classes include:

- `Constraints` / `ConstraintHandler`
- `Bonds` / `BondHandler`
- `Angles` / `AngleHandler`
- `ProperTorsions` / `ProperTorsionHandler`
- `ImproperTorsions` / `ImproperTorsionHandler`
- `vdW` / `vdWHandler`
- `Electrostatics` / `ElectrostaticsHandler`
- `LibraryCharges` / `LibraryChargeHandler`
- `ToolkitAM1BCC` / `ToolkitAM1BCCHandler`
- `NAGLCharges` / `NAGLChargesHandler`
- `ChargeIncrementModel` / `ChargeIncrementModelHandler`
- `GBSA` / `GBSAHandler`
- `VirtualSites` / `VirtualSiteHandler`

Use `force_field.registered_parameter_handlers` to see which handlers are instantiated for a loaded force field. `force_field["vdW"]` is shorthand for `force_field.get_parameter_handler("vdW")` after that handler exists.

## Parameter Collections

Most handlers expose a `.parameters` collection. Typical operations:

```python
vdw = force_field.get_parameter_handler("vdW")
first_parameter = vdw.parameters[0]
parameter_by_smirks = vdw.parameters["[#1:1]-[#6X4]"]
parameter_by_smirks.epsilon *= 1.05
```

Important safety notes:

- Parameter order affects assignment because more specific or later parameters can have higher precedence depending on handler semantics.
- Editing a `smirks` string checks syntactic/valence compatibility, but it does not prove the hierarchy still assigns every intended molecule.
- Deleting a broad/root parameter can create missing-parameter failures during system creation.
- Duplicate parameters or repeated incompatible handler attributes raise errors before or during parsing/combination.

## Label Shapes

`force_field.label_molecules(topology)` returns one entry per molecule in the topology:

```python
labels = force_field.label_molecules(topology)
first_molecule_labels = labels[0]
vdw_labels = first_molecule_labels.get("vdW", {})
```

Each molecule-label entry is a dictionary from handler tag to a match dictionary. Match keys are atom-index tuples or match-key objects; values are the applied `ParameterType`. For `VirtualSites`, a match may map to a list of `ParameterType` objects because more than one virtual-site parameter can apply at a site.

Useful fields on most returned `ParameterType` values include:

- `.id` when the OFFXML parameter has an `id` attribute.
- `.smirks` for the matching SMIRKS pattern.
- Handler-specific physical attributes such as `.k`, `.length`, `.angle`, `.epsilon`, `.sigma`, `.rmin_half`, `.periodicity`, `.phase`, or `.charge_increment`.

## Serialization and Cosmetic Attributes

```python
force_field.to_file("edited.offxml")
force_field.to_file("edited.xml", io_format="xml")
force_field.to_file("edited.offxml", discard_cosmetic_attributes=True)
roundtrip = ForceField("edited.offxml", allow_cosmetic_attributes=True)
```

`.offxml` is treated as XML. Use `allow_cosmetic_attributes=True` when reading non-standard attributes that should be retained. Use `discard_cosmetic_attributes=True` when writing a clean spec-only file.

## Combining Sources

```python
combined = ForceField("openff-2.3.0.offxml").combine(ForceField("tip3p.offxml"))
# Equivalent assignment intent to ForceField("openff-2.3.0.offxml", "tip3p.offxml") when sections are compatible.
```

Combination is order-dependent. Later data is loaded into the first force field and can add higher-precedence parameters. Incompatible duplicate handler settings raise compatibility errors instead of silently merging.

## Applying Force Fields

`create_interchange` is the primary toolkit application boundary:

```python
interchange = force_field.create_interchange(topology)
```

It requires `openff.interchange`. `create_openmm_system` delegates through `create_interchange(...).to_openmm(combine_nonbonded_forces=True)` and also requires OpenMM-compatible dependencies.

Charge-related options:

```python
molecule.partial_charges = force_field.get_partial_charges(molecule)
system = force_field.create_openmm_system(
    molecule.to_topology(),
    charge_from_molecules=[molecule],
)
```

Use `charge_from_molecules` to reuse precomputed charges. Use `partial_bond_orders_from_molecules` to reuse appropriate partial bond orders. Set `allow_nonintegral_charges=True` only when the chemistry and downstream engine can tolerate non-integral total charges.

## Virtual Sites and Charges

Virtual sites live under the `VirtualSites` handler. They can affect electrostatics and labeling. `get_partial_charges(molecule)` raises a virtual-site-specific error when the force field applies virtual sites, because atom-only charges cannot unambiguously include off-atom site charges. In that case, create an `Interchange` and inspect its electrostatics collection rather than assigning atom-only charges to a `Molecule`.
