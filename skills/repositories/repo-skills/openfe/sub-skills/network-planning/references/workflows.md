# Network Planning Workflows

Use these workflows for planning and diagnosis before any OpenMM execution. They are API-oriented; command-line flag syntax belongs in [cli-workflows](../../cli-workflows/SKILL.md), protocol settings in [protocols](../../protocols/SKILL.md), and estimates/results in [results-analysis](../../results-analysis/SKILL.md).

## Workflow 1: Safe Input Preflight

Run the bundled helper before debugging mapper or planner failures:

```bash
python scripts/validate_ligand_inputs.py --molecules ligands.sdf --protein receptor.pdb
python scripts/validate_ligand_inputs.py --molecules ligands/ --json
```

The helper checks path existence, recognized extensions, import availability for planning-related packages, molecule counts when RDKit is available, protein atom records, empty files, duplicate ligand names, and unnamed/placeholder ligand names. It does not run simulations, assign charges, download files, or write output unless the shell redirects stdout.

Use the output to answer:

- Are the files present and recognized as SDF/MOL2/PDB/PDBx/mmCIF?
- Are there at least two named ligands for relative planning?
- Are ligand names unique enough to become transformation labels?
- Are RDKit/OpenFE/OpenFF/Kartograf/LOMAP/Konnektor/Perses imports available for the intended mapper path?

## Workflow 2: Build Components Without Execution

1. Load ligands into `SmallMoleculeComponent` objects.
2. Ensure every ligand has a unique, stable `name`.
3. Load protein or protein-membrane components for RBFE; omit protein for RHFE.
4. Use `SolventComponent()` unless the user specifically requests solvent/ion changes.
5. Do not configure protocol settings here; route those details to [protocols](../../protocols/SKILL.md).

```python
from rdkit import Chem
import openfe

ligands = []
for path in ligand_paths:
    if path.suffix.lower() == ".sdf":
        ligand = openfe.SmallMoleculeComponent.from_sdf_file(path)
    elif path.suffix.lower() == ".mol2":
        mol = Chem.MolFromMol2File(str(path), removeHs=False)
        ligand = openfe.SmallMoleculeComponent.from_rdkit(mol)
    else:
        raise ValueError(f"Unsupported ligand extension: {path}")
    if not ligand.name or ligand.name == "*****":
        ligand = openfe.SmallMoleculeComponent(ligand.to_rdkit(), name=path.stem)
    ligands.append(ligand)

protein = openfe.ProteinComponent.from_pdb_file(protein_path)
solvent = openfe.SolventComponent()
```

For a fully solvated membrane complex, load `openfe.ProteinMembraneComponent` for the complex leg and do not add a separate `SolventComponent` to that leg. Keep the ordinary `SolventComponent()` for RHFE or solvent-leg planning decisions.

If rebuilding a ligand solely to fix a name, preserve the original coordinates, stereochemistry, and any pre-assigned partial charges carried by the RDKit molecule.

## Workflow 3: Choose Mapper and Scorer

Use mapper choice as a scientific and diagnostic decision:

| Situation | Mapper/scorer starting point |
| --- | --- |
| Current OpenFE CLI-like default behavior | `KartografAtomMapper(atom_max_distance=0.95, atom_map_hydrogens=True, map_hydrogens_on_hydrogens_only=True, map_exact_ring_matches_only=True, allow_partial_fused_rings=True, allow_bond_breaks=False)` with `lomap_scorers.default_lomap_score`. |
| Python convenience planner default | `RBFEAlchemicalNetworkPlanner()` / `RHFEAlchemicalNetworkPlanner()` default to `LomapAtomMapper(time=20, threed=True, max3d=1.0, element_change=True, shift=False)` unless `mappers=[...]` is supplied. |
| Congeneric series with reliable 3D alignment | `LomapAtomMapper(threed=True, max3d=1.0)` and `default_lomap_score`. |
| 2D-only or poorly aligned ligands | Try `LomapAtomMapper(threed=False)` or adjust Kartograf distance constraints, then inspect mappings. |
| Hard-to-map pair | Generate a maximal network or map one pair directly; compare Lomap vs Kartograf. |
| Legacy Perses comparison | `PersesAtomMapper` and `perses_scorers.default_perses_scorer`, only when the optional dependency is available and deprecation is acceptable. |

Direct pair diagnostic:

```python
mapper = openfe.setup.LomapAtomMapper(threed=True, element_change=True)
for mapping in mapper.suggest_mappings(ligand_a, ligand_b):
    print(mapping.componentA.name, mapping.componentB.name)
    print(mapping.componentA_to_componentB)
    print(openfe.setup.lomap_scorers.default_lomap_score(mapping))
```

If no mappings are returned, try a less constrained mapper only for diagnosis, then decide whether the transformation is scientifically acceptable.

## Workflow 4: Choose Ligand Network Topology

Start with the user’s scientific question and validation needs:

- Use `generate_maximal_network` when diagnosing mapper coverage because it exposes which ligand pairs can map at all.
- Use `generate_minimal_spanning_network` for a compact connected campaign with high-scoring edges.
- Use `generate_minimal_redundant_network` when redundant paths are valuable for robustness or cycle closure.
- Use `generate_radial_network` when one known reference ligand should be the hub.
- Use `generate_network_from_names` or `generate_network_from_indices` when the edge list is dictated by prior work, an external planning tool, or a human-curated design.

Minimal spanning planning:

```python
from openfe import setup

network = setup.ligand_network_planning.generate_minimal_spanning_network(
    ligands=ligands,
    mappers=[setup.KartografAtomMapper()],
    scorer=setup.lomap_scorers.default_lomap_score,
    progress=False,
)
if not network.is_connected():
    raise RuntimeError("Planner produced a disconnected ligand network")
```

Radial planning around a named ligand:

```python
network = setup.ligand_network_planning.generate_radial_network(
    ligands=ligands,
    central_ligand="reference_ligand_name",
    mappers=[setup.LomapAtomMapper()],
    scorer=setup.lomap_scorers.default_lomap_score,
    progress=False,
)
```

A radial center name must match exactly one ligand. If the input set has duplicate names, fix the names before planning.

## Workflow 5: Plan RBFE/RHFE Alchemical Networks

Use the convenience planners when a standard relative free-energy campaign is enough and the user has not asked for manual `Transformation` construction.

RBFE concept:

```python
from openfe.setup.alchemical_network_planner import RBFEAlchemicalNetworkPlanner

planner = RBFEAlchemicalNetworkPlanner(
    mappers=[openfe.setup.KartografAtomMapper(
        atom_max_distance=0.95,
        atom_map_hydrogens=True,
        map_hydrogens_on_hydrogens_only=True,
        map_exact_ring_matches_only=True,
        allow_partial_fused_rings=True,
        allow_bond_breaks=False,
    )],
    mapping_scorer=openfe.setup.lomap_scorers.default_lomap_score,
    ligand_network_planner=openfe.setup.ligand_network_planning.generate_minimal_spanning_network,
)
alchemical_network = planner(
    ligands=ligands,
    solvent=openfe.SolventComponent(),
    protein=protein,
    cofactors=[],
)
ligand_network = planner._ligand_network
```

RHFE concept:

```python
from openfe.setup.alchemical_network_planner import RHFEAlchemicalNetworkPlanner

planner = RHFEAlchemicalNetworkPlanner()
alchemical_network = planner(ligands=ligands, solvent=openfe.SolventComponent())
ligand_network = planner._ligand_network
```

Expected planner output:

- RBFE: one solvent and one complex transformation per ligand-network edge.
- RHFE: one vacuum and one solvent transformation per ligand-network edge.
- Transformation names derive from planner name and chemical-system names; duplicate ligand names can become duplicate transformation labels.
- The default protocol is a relative hybrid topology protocol. Python convenience planners default to LOMAP mapping; CLI planning defaults to the Kartograf settings listed above. Simulation settings, repeats, OpenMM platforms, and adaptive charge-correction choices belong in [protocols](../../protocols/SKILL.md).

## Workflow 6: Diagnose Unnamed Duplicate Ligands Without OpenMM

Use this when RBFE planning fails or overwrites output because ligands are unnamed or duplicate named.

1. Run `python scripts/validate_ligand_inputs.py --molecules <input> --strict`.
2. Check warnings for empty names, placeholder names such as `*****`, and duplicate names.
3. Load the ligands and print `(index, ligand.name)` before mapping.
4. If names are duplicated, rebuild components with unique names from file stems, SDF properties, or a user-provided mapping table.
5. Re-run a maximal network to confirm mapper coverage before planning RBFE.
6. Only after a connected ligand network exists should the plan move to protocol or CLI execution.

Do not use OpenMM execution or `quickrun` to debug naming problems.

## Workflow 7: Plan a Mixed Charged Ligand Set

1. Validate all ligand files and names.
2. Identify formal charge changes by inspecting the RDKit/OpenFF molecules before selecting protocol settings.
3. Prefer a diagnostic maximal network first; charged pairs often need human review even when a mapper returns an edge.
4. Compare Lomap and Kartograf mappings for charged pairs, including `mapping.get_distances()` and score differences.
5. For RBFE convenience planning, note that the planner validates each transformation and can adapt relative hybrid topology settings for charge-changing transformations.
6. Route explicit charge correction, dummy-charge, solvent padding, and OpenMM settings to [protocols](../../protocols/SKILL.md).
7. Route exact `openfe plan-rbfe-network` YAML/flag syntax and partial-charge generation commands to [cli-workflows](../../cli-workflows/SKILL.md).

Keep the network-planning handoff concrete: list the charged ligand pairs, chosen mapper/scorer, topology, rejected edges, and questions for protocol configuration.

## Workflow 8: Export Planning Artifacts for Later Steps

For API-built outputs:

```python
from pathlib import Path

out = Path("alchemicalNetwork")
out.mkdir(exist_ok=True)
alchemical_network.to_json(out / "alchemicalNetwork.json")
(out / "ligand_network.graphml").write_text(ligand_network.to_graphml())
```

If writing transformation JSON files for CLI execution, mirror the planning output layout described in [Data Formats](data-formats.md). Exact quickrun command construction belongs in [cli-workflows](../../cli-workflows/SKILL.md).
