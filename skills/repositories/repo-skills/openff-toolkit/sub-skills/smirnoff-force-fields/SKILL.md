---
name: smirnoff-force-fields
description: "Load, modify, inspect, serialize, label, and apply SMIRNOFF OFFXML
  force fields with OpenFF Toolkit ForceField APIs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# SMIRNOFF Force Fields

Use this sub-skill when a task centers on OpenFF Toolkit SMIRNOFF force fields: loading `.offxml` files, discovering installed force fields, inspecting or modifying parameter handlers, labeling molecules with assigned parameters, serializing edited force fields, combining sources, creating Interchange/OpenMM systems, or diagnosing SMIRNOFF parsing and handler errors.

## Route First

- Use `references/api-reference.md` for the verified `ForceField` signatures, handler concepts, label shapes, serialization APIs, and Interchange/OpenMM boundary.
- Use `references/workflows.md` for copy-ready recipes: load installed or local `.offxml`, inspect available force fields, label molecules, edit a parameter, serialize/reload, and apply a force field.
- Use `references/plugins-and-custom-parameters.md` for custom `ParameterHandler` classes and entry-point plugin loading with `load_plugins=True`.
- Use `references/troubleshooting.md` when parsing, handler registration, force-field package discovery, charge assignment, virtual-site, Interchange, or OpenMM conversion fails.
- Use `scripts/smoke_smirnoff_workflow.py` for a safe local smoke probe that builds a molecule/topology, loads a force field, optionally labels parameters, and attempts Interchange if installed.

## Boundaries

- For molecule construction, stereochemistry, conformers, file I/O, and mapped SMILES details, route to `../molecules-and-io/SKILL.md`.
- For topology construction, PDB/OpenMM topology conversion, positions, boxes, and system-level preparation depth, route to `../topology-and-systems/SKILL.md`.
- For optional backend installation, toolkit registries, charge toolkit availability, and dependency selection depth, route to `../toolkit-backends/SKILL.md`.
- Do not rely on original repository docs, tests, examples, or notebooks at runtime; this sub-skill bundles the SMIRNOFF patterns needed for future agents.

## Quick Start

```python
from openff.toolkit import ForceField, Molecule, Topology
from openff.toolkit.typing.engines.smirnoff import get_available_force_fields

print(get_available_force_fields())
force_field = ForceField("openff-2.3.0.offxml")
molecule = Molecule.from_smiles("CCO")
topology = Topology.from_molecules([molecule])
labels = force_field.label_molecules(topology)
print(force_field.registered_parameter_handlers)
print(labels[0].keys())
```

If `ForceField("openff-2.3.0.offxml")` cannot find the file, inspect `get_available_force_fields()` and install or point to a local `.offxml` file rather than changing the molecule/topology workflow.
