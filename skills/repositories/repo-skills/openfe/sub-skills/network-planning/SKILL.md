---
name: network-planning
description: "Plan OpenFE components, atom mappings, ligand networks, and
  RBFE/RHFE alchemical networks before execution."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Network Planning

Use this sub-skill when a task is about building OpenFE inputs before simulation: components, atom mappings, ligand networks, RBFE/RHFE alchemical networks, or deciding whether to use API planning, CLI planning, or manual network construction.

## Start Here

1. Validate ligand/protein inputs with [validate_ligand_inputs.py](scripts/validate_ligand_inputs.py) before planning or diagnosing mapper failures.
2. Use [API Reference](references/api-reference.md) for constructors, mapper/scorer choices, ligand network functions, and RBFE/RHFE planner data flow.
3. Use [Workflows](references/workflows.md) for end-to-end planning recipes, difficult diagnostics, and protocol handoff decisions.
4. Use [Data Formats](references/data-formats.md) for SDF/MOL2/PDB/PDBx, GraphML ligand networks, alchemical-network JSON, and transformation JSON expectations.
5. Use [Troubleshooting](references/troubleshooting.md) for missing optional dependencies, invalid ligand names, unmapped edges, disconnected networks, charged transformations, malformed files, and immutable objects.

## Scope

This sub-skill covers:

- `SmallMoleculeComponent`, `ProteinComponent`, `ProteinMembraneComponent`, `SolventComponent`, `ChemicalSystem`, `LigandAtomMapping`, and `LigandNetwork` construction concepts.
- `LomapAtomMapper`, `KartografAtomMapper`, `PersesAtomMapper`, `lomap_scorers`, `perses_scorers`, and `openfe.setup.ligand_network_planning` functions.
- `RBFEAlchemicalNetworkPlanner`, `RHFEAlchemicalNetworkPlanner`, and the `RelativeAlchemicalNetworkPlanner` data flow from ligands to `AlchemicalNetwork`, including the difference between Python planner defaults and CLI planning defaults.
- Pre-execution route decisions: API vs CLI planning, topology choice, mapper/scorer tradeoffs, and when to hand a plan to protocol or CLI execution guidance.

Route elsewhere:

- Protocol settings, OpenMM backend choices, adaptive settings details, and simulation configuration -> [protocols](../protocols/SKILL.md).
- CLI flag syntax, `openfe plan-*`, `openfe quickrun`, repeat job construction, and `gather*` command use -> [cli-workflows](../cli-workflows/SKILL.md).
- Post-run estimates, uncertainties, failed edge summaries, and result aggregation -> [results-analysis](../results-analysis/SKILL.md).

## Safe Default Pattern

- Do input checks first; do not run OpenMM while diagnosing planning failures.
- Prefer unique, explicit ligand names before creating networks; duplicate or empty names can create ambiguous radial centers and duplicate transformation labels.
- Start with a maximal network to debug mapper coverage, then choose minimal spanning, redundant minimal spanning, radial, or explicit edges based on campaign needs.
- Treat OpenFE components, mappings, and networks as immutable; rebuild them from corrected inputs rather than mutating them in place.
- For charged transformations, identify the affected ligand pairs during planning and hand protocol-setting decisions to [protocols](../protocols/SKILL.md).
