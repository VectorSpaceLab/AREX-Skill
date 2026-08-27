# SMIRNOFF ForceField Workflows

These recipes are self-contained patterns for common agent tasks. They assume molecule/topology objects are already valid; for detailed molecule or topology preparation, use the sibling sub-skills named in `SKILL.md`.

## Inspect Available Installed Force Fields

```python
from openff.toolkit.typing.engines.smirnoff import get_available_force_fields

names = get_available_force_fields()
paths = get_available_force_fields(full_paths=True)
print(names)
```

If `names` is empty, use a local OFFXML path or install the package that supplies the desired OpenFF force fields. Do not diagnose this as a SMILES or topology problem.

## Load an Installed or Local OFFXML Force Field

```python
from openff.toolkit import ForceField

force_field = ForceField("openff-2.3.0.offxml")
print(force_field.registered_parameter_handlers)
```

For a local edited file:

```python
force_field = ForceField("my-force-field.offxml", allow_cosmetic_attributes=True)
```

For multiple compatible sources, list them in precedence order:

```python
force_field = ForceField("openff-2.3.0.offxml", "my-solvent.offxml")
```

## Build a Minimal Molecule/Topology for Parameter Inspection

```python
from openff.toolkit import Molecule, Topology

molecule = Molecule.from_smiles("CCO")
topology = Topology.from_molecules([molecule])
```

If stereochemistry, protonation, conformers, or file conversion matter, handle them before this workflow with the molecule-focused sub-skill.

## Label Assigned Parameters

```python
labels = force_field.label_molecules(topology)
for molecule_index, molecule_labels in enumerate(labels):
    print("molecule", molecule_index)
    for handler_name, assigned in molecule_labels.items():
        print(" ", handler_name, len(assigned))
        for match, parameter in list(assigned.items())[:5]:
            if isinstance(parameter, list):
                ids = [getattr(item, "id", None) for item in parameter]
            else:
                ids = getattr(parameter, "id", None)
            print("   ", match, ids)
```

Use this to verify which parameter IDs or SMIRKS actually apply after edits. Labeling is also useful for diagnosing missing coverage before attempting system creation.

## Modify a Parameter and Verify the Label Path

```python
from openff.toolkit import ForceField, Molecule, Topology, unit

force_field = ForceField("openff-2.3.0.offxml")
molecule = Molecule.from_smiles("CCO")
topology = Topology.from_molecules([molecule])

before = force_field.label_molecules(topology)[0]
vdw = force_field.get_parameter_handler("vdW")
parameter = next(iter(vdw.parameters))
original_epsilon = parameter.epsilon
parameter.epsilon = original_epsilon * 1.01

after = force_field.label_molecules(topology)[0]
print(getattr(parameter, "id", None), parameter.smirks, parameter.epsilon)
print(before.keys(), after.keys())
```

For production edits, prefer selecting by a known `id` or `smirks` instead of blindly editing the first parameter:

```python
for parameter in force_field.get_parameter_handler("Bonds").parameters:
    if getattr(parameter, "id", None) == "b1":
        parameter.k *= 1.05
        break
else:
    raise LookupError("Parameter id b1 was not found")
```

## Serialize and Reload an Edited Force Field

```python
from pathlib import Path
from openff.toolkit import ForceField

force_field = ForceField("openff-2.3.0.offxml", allow_cosmetic_attributes=True)
# make edits here
output = Path("edited.offxml")
force_field.to_file(str(output), discard_cosmetic_attributes=False)
roundtrip = ForceField(str(output), allow_cosmetic_attributes=True)
print(roundtrip.registered_parameter_handlers)
```

Use `discard_cosmetic_attributes=True` only when the output should be strict spec content without non-standard attributes.

## Create an Interchange Object

```python
try:
    interchange = force_field.create_interchange(topology)
except ModuleNotFoundError as error:
    raise RuntimeError("Install openff-interchange to create Interchange objects") from error
```

`Interchange` is the recommended OpenFF boundary for exporting to simulation engines. It can include virtual sites, electrostatics, vdW, and bonded collections in an engine-neutral representation.

## Create an OpenMM System

```python
try:
    system = force_field.create_openmm_system(topology)
except ModuleNotFoundError as error:
    raise RuntimeError("Install OpenMM and openff-interchange before requesting an OpenMM System") from error
```

`create_openmm_system` calls `create_interchange` internally and converts with `to_openmm(combine_nonbonded_forces=True)`. If conversion fails, first check whether `create_interchange` succeeds; this separates force-field assignment problems from OpenMM export problems.

## Reuse Precomputed Charges

```python
molecule.partial_charges = force_field.get_partial_charges(molecule)
system = force_field.create_openmm_system(
    molecule.to_topology(),
    charge_from_molecules=[molecule],
)
```

This is useful when charging is expensive or should be deterministic across many systems. If the force field uses virtual sites, inspect Interchange electrostatics instead of expecting atom-only `Molecule.partial_charges` to represent off-atom charges.

## Combine Force Fields Carefully

```python
base = ForceField("openff-2.3.0.offxml")
extra = ForceField("custom-fragment.offxml")
combined = base.combine(extra)
```

Validate combination by labeling representative molecules before serialization. Combination is order-dependent, and incompatible handler-level settings should be fixed at the source rather than suppressed.

## Run the Bundled Smoke Probe

From this sub-skill directory or by using the full script path:

```bash
python scripts/smoke_smirnoff_workflow.py --help
python scripts/smoke_smirnoff_workflow.py --smiles CCO --label
```

The script prints a JSON summary and reports missing optional packages actionably.
