# Network Planning API Reference

This reference distills the OpenFE setup APIs used before execution. It intentionally avoids CLI flag syntax and simulation settings; route those to sibling sub-skills from `SKILL.md`.

## Imports

```python
import openfe
from openfe import (
    AlchemicalNetwork,
    ChemicalSystem,
    LigandAtomMapping,
    LigandNetwork,
    ProteinComponent,
    SmallMoleculeComponent,
    SolventComponent,
    Transformation,
)
from openfe import setup
from openfe.setup import ligand_network_planning, lomap_scorers, perses_scorers
```

Use `openfe.SmallMoleculeComponent`, `openfe.ProteinComponent`, `openfe.SolventComponent`, and `openfe.ChemicalSystem` for public component/system construction. Use `openfe.setup` for mapper classes, scorer modules, ligand-network planning functions, and RBFE/RHFE planner classes. The top-level `openfe` namespace also re-exports these setup names, but `openfe.setup` keeps planning code clearer.

## Components and Chemical Systems

| Object | Purpose | Key construction notes |
| --- | --- | --- |
| `SmallMoleculeComponent(rdkit, name="")` | Ligands and cofactors. | Build from an RDKit `Mol`, `SmallMoleculeComponent.from_rdkit(mol)`, or `SmallMoleculeComponent.from_sdf_file(path)`. Use explicit unique names when file titles are empty, duplicated, or placeholder-like. |
| `ProteinComponent(rdkit, name="")` | Protein structures from PDB-like inputs. | Use `ProteinComponent.from_pdb_file(path)` or `ProteinComponent.from_pdbx_file(path)` when available. |
| `ProteinMembraneComponent(...)` | Explicitly solvated protein-membrane complex for membrane RBFE. | Use the dedicated component type instead of `ProteinComponent` when the input contains a fully solvated membrane system; do not add a separate `SolventComponent` to the complex leg. |
| `SolventComponent(...)` | Abstract solvent and ion environment. | Keyword-only defaults represent water with `Na+`/`Cl-`, neutralization enabled, and 0.15 M ion concentration. |
| `ChemicalSystem(components, name="")` | A named state made from components. | Use semantic component labels such as `ligand`, `solvent`, `protein`, and `cofactor1`. Planner-generated names commonly append `_vacuum`, `_solvent`, or `_complex` to ligand names. |
| `Transformation(stateA, stateB, protocol, mapping=None, name=None, validate=False)` | One alchemical edge between two chemical systems. | Relative ligand transformations normally include a `LigandAtomMapping`. Protocol construction/settings belong to [protocols](../../protocols/SKILL.md). |
| `AlchemicalNetwork(edges=None, nodes=None, name=None)` | A campaign graph of transformations. | Planner output for RBFE/RHFE. Nodes should be connected through transformations; do not treat lone chemical systems as useful campaign nodes. |

Components, mappings, and ligand networks are immutable in normal use. If a ligand name, atom mapping, or network topology is wrong, rebuild the object from corrected inputs.

## Atom Mappers and Mappings

`LigandAtomMapper.suggest_mappings(componentA, componentB)` returns an iterable of `LigandAtomMapping` objects. The mapping dictionary is available as `mapping.componentA_to_componentB`; missing atom indices are unmapped. Useful inspection methods include `mapping.get_distances()`, `mapping.draw_to_file(...)`, and `mapping.view_3d()`.

| Mapper | Typical use | Important parameters and dependency notes |
| --- | --- | --- |
| `LomapAtomMapper(time=20, threed=True, max3d=1.0, element_change=True, seed="", shift=False)` | RDKit/LOMAP MCS mapping; often robust for congeneric series. | `threed` and `max3d` use conformer geometry; `element_change=False` can make chemically conservative maps but may fail transformations; `shift=True` can help unaligned test-like ligands. Requires `lomap` and RDKit. |
| `KartografAtomMapper(atom_max_distance=0.95, atom_map_hydrogens=True, map_hydrogens_on_hydrogens_only=False, map_exact_ring_matches_only=True, allow_partial_fused_rings=True, allow_bond_breaks=False, ...)` | Geometry-aware mapping. Current CLI planning defaults instantiate Kartograf with `map_hydrogens_on_hydrogens_only=True` in addition to the listed conservative ring/distance settings. | Tight distance/ring settings can reject plausible pairs; loosening them may create less conservative mappings. Requires `kartograf`. |
| `PersesAtomMapper(allow_ring_breaking=True, preserve_chirality=True, use_positions=True, coordinate_tolerance=0.25 * angstrom)` | Legacy Perses mapping workflows. | Requires `perses`; emits deprecation warnings and is planned for removal in a future OpenFE major version. Prefer Lomap or Kartograf unless a Perses-specific comparison is required. |

When multiple mappers are supplied to ligand-network planners, provide a scorer if you want the best scored mapping. Without a scorer, planner behavior can choose the first valid mapper and warn.

## Scorers

Scorers accept a `LigandAtomMapping` and return a normalized numeric score where larger is better.

| Module | Functions |
| --- | --- |
| `openfe.setup.lomap_scorers` | `default_lomap_score`, `mcsr_score`, `mncar_score`, `atomic_number_score`, `hybridization_score`, `sulfonamides_score`, `heterocycles_score`, `transmuting_methyl_into_ring_score`, `transmuting_ring_sizes_score`, `ecr_score`, `tmcsr_score` |
| `openfe.setup.perses_scorers` | `default_perses_scorer(mapping, use_positions=False, normalize=True)`; requires `perses`, and normalization with positions is not implemented. |

`default_lomap_score` combines multiple LOMAP rules and is the standard scorer for minimal spanning and redundant minimal spanning networks.

## Ligand Networks

A `LigandNetwork` has `SmallMoleculeComponent` nodes and `LigandAtomMapping` edges. Use `network.nodes`, `network.edges`, `network.graph`, and `network.is_connected()` for inspection. Use `network.to_graphml()` and `LigandNetwork.from_graphml(text)` for GraphML exchange.

### Planning Functions

| Function | Use when | Notes |
| --- | --- | --- |
| `generate_maximal_network(ligands, mappers, scorer=None, progress=True, n_processes=1)` | Debug mapper/scorer coverage or inspect all possible pairwise mappings. | Attempts all ligand pairs for each mapper. For `N` ligands, expect up to `N(N-1)/2` edges per mapper before failures. |
| `generate_minimal_spanning_network(ligands, mappers, scorer, progress=True, n_processes=1)` | Build a connected campaign with as few high-scoring edges as possible. | Requires a scorer; missing scores can surface as a `KeyError` around `score`. Unmapped ligands cause an "Unable to create edges" failure. |
| `generate_minimal_redundant_network(ligands, mappers, scorer, progress=True, mst_num=2, n_processes=1)` | Add redundancy so each node has multiple high-scoring paths. | `mst_num=2` adds second-best tree edges; larger values increase cost and edge count. |
| `generate_radial_network(ligands, central_ligand, mappers, scorer=None, progress=False, n_processes=1)` | Build a star/hub-and-spoke network around a known reference ligand. | `central_ligand` can be a component, a unique ligand name, or a zero-based index. Duplicate or missing center names raise errors. |
| `generate_network_from_names(ligands, mapper, names)` | Force specific edges by ligand names. | Duplicate ligand names raise `ValueError`; unknown requested names raise `KeyError`; intentionally sparse edges can warn about disconnected networks. |
| `generate_network_from_indices(ligands, mapper, indices)` | Force specific edges by zero-based ligand indices. | Invalid indices raise `IndexError`; sparse edge lists can warn about disconnected networks. |
| `load_orion_network(ligands, mapper, network_file)` | Load an Orion/NES-style text edge list. | Each non-comment line must look like `name >> name`. |
| `load_fepplus_network(ligands, mapper, network_file)` | Load a Schrödinger FEP+ `.edges`-style file. | Lines must look like `hash:hash # name -> name`. |

## RBFE/RHFE Alchemical Network Planners

`RelativeAlchemicalNetworkPlanner(name="easy_rfe_calculation", mappers=None, mapping_scorer=default_lomap_score, ligand_network_planner=generate_minimal_spanning_network, protocol=None)` is the shared planning concept. When `mappers=None`, the Python convenience planners construct a default `LomapAtomMapper(time=20, threed=True, max3d=1.0, element_change=True, shift=False)`. Current CLI `plan-rbfe-network` and `plan-rhfe-network` defaults instead construct a conservative `KartografAtomMapper` through the CLI YAML/options layer. The concrete convenience planners are:

```python
from openfe.setup.alchemical_network_planner import (
    RBFEAlchemicalNetworkPlanner,
    RHFEAlchemicalNetworkPlanner,
)

rbfe = RBFEAlchemicalNetworkPlanner()
alchemical_network = rbfe(
    ligands=ligands,
    solvent=SolventComponent(),
    protein=protein_component,
    cofactors=[],
)

rhfe = RHFEAlchemicalNetworkPlanner()
alchemical_network = rhfe(ligands=ligands, solvent=SolventComponent())
```

Data flow:

1. Construct or receive `SmallMoleculeComponent` ligands, optional cofactors, a `SolventComponent`, and for RBFE a `ProteinComponent` or protein-membrane component.
2. Use mapper(s), mapping scorer, and ligand-network planner to create a `LigandNetwork`.
3. Generate chemical systems for each ligand and environment: RHFE creates vacuum and solvent systems; RBFE creates solvent and complex systems.
4. Convert each ligand-network edge into environment-specific `Transformation` edges using the chosen protocol.
5. Return an `AlchemicalNetwork` whose transformation names combine planner name and state names, such as `rbfe_ligandA_solvent_ligandB_solvent`.

Planner defaults create a `RelativeHybridTopologyProtocol` with default settings. If the task asks to customize protocol settings, OpenMM backend behavior, repeats, adaptive settings, or charge-correction settings, route to [protocols](../../protocols/SKILL.md).

## Common API Snippets

### Inspect a single mapping

```python
mapper = setup.LomapAtomMapper(threed=True, max3d=1.0)
mappings = list(mapper.suggest_mappings(ligand_a, ligand_b))
if not mappings:
    raise ValueError("No mapping found for this ligand pair")
mapping = mappings[0]
score = setup.lomap_scorers.default_lomap_score(mapping)
print(mapping.componentA_to_componentB, score, mapping.get_distances())
```

### Build a diagnostic maximal network

```python
mapper = setup.KartografAtomMapper()
network = setup.ligand_network_planning.generate_maximal_network(
    ligands=ligands,
    mappers=[mapper],
    scorer=setup.lomap_scorers.default_lomap_score,
    progress=False,
)
print(len(network.nodes), len(network.edges), network.is_connected())
```

### Build a production-style minimal spanning network

```python
network = setup.ligand_network_planning.generate_minimal_spanning_network(
    ligands=ligands,
    mappers=[setup.KartografAtomMapper()],
    scorer=setup.lomap_scorers.default_lomap_score,
    progress=False,
)
assert network.is_connected()
```
