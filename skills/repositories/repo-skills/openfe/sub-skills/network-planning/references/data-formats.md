# Network Planning Data Formats

This reference covers inputs and planning artifacts. It does not cover result JSON semantics or gather TSV interpretation; use [results-analysis](../../results-analysis/SKILL.md) for post-run outputs.

## Ligand Inputs

OpenFE planning commonly uses ligand files that become `SmallMoleculeComponent` objects.

| Format | Typical use | Notes |
| --- | --- | --- |
| `.sdf` | One or more small molecules in one file. | SDF titles/properties can become molecule names. Empty entries, invalid records, missing hydrogens, missing conformers, duplicate names, or placeholder names should be fixed before planning. |
| `.mol2` | One small molecule per file in common CLI loading paths. | The MOL2 molecule-name line can be a placeholder such as `*****`; replace ambiguous names before radial or RBFE/RHFE planning. |
| RDKit `Mol` | Programmatic construction. | Use `SmallMoleculeComponent.from_rdkit(mol)` or `SmallMoleculeComponent(mol, name=...)`. Preserve coordinates and stereochemistry when rebuilding names. |

For CLI-style molecule directory loading, treat directories as non-recursive collections of `.sdf` and `.mol2` files. If no recognized files exist, planning cannot start.

## Protein and Cofactor Inputs

| Format | Typical use | Notes |
| --- | --- | --- |
| `.pdb` | `ProteinComponent.from_pdb_file(...)` for RBFE. | The file should contain useful `ATOM`/`HETATM` records. Protein preparation quality affects simulation, but detailed OpenMM setup belongs in [protocols](../../protocols/SKILL.md). |
| `.pdbx` / `.cif` | PDBx/mmCIF protein input where supported. | Use the PDBx constructor when available. |
| Fully solvated membrane `.pdb` / `.pdbx` / `.cif` | `ProteinMembraneComponent.from_pdb_file(...)` or `from_pdbx_file(...)` for membrane RBFE complex legs. | The complex leg is explicitly solvated, so do not add a separate `SolventComponent` to that leg. Use a normal `SolventComponent` only for solvent-leg/RHFE contexts. |
| Cofactor `.sdf` / `.mol2` | Small molecules included with the protein complex. | Treat cofactors like small molecules for loading and charge-awareness, but remember they are not ligand-network nodes unless the user explicitly says so. |

## Names and Labels

Names are operational, not cosmetic:

- `generate_radial_network(..., central_ligand="name")` requires one and only one matching ligand name.
- `generate_network_from_names` raises errors for unknown requested names and duplicate ligand names.
- RBFE/RHFE planners build transformation names from planner name and chemical-system names; duplicate ligand names can create duplicate transformation labels and overwrite-risk errors.
- Empty names and placeholders such as `*****` should be replaced before planning.

Recommended naming checks:

```python
names = [ligand.name for ligand in ligands]
missing = [i for i, name in enumerate(names) if not name or name == "*****"]
duplicates = sorted({name for name in names if names.count(name) > 1})
```

## Ligand Network GraphML

`LigandNetwork.to_graphml()` serializes ligand-network nodes and `LigandAtomMapping` edges to a GraphML string. Use `LigandNetwork.from_graphml(text)` to read it back.

Common producers/consumers:

- API planning: `Path("ligand_network.graphml").write_text(network.to_graphml())`.
- Visualization tools consume GraphML ligand networks; exact `openfe view-ligand-network` syntax belongs in [cli-workflows](../../cli-workflows/SKILL.md).

GraphML troubleshooting:

- Malformed XML/GraphML usually means the file is not a `LigandNetwork.to_graphml()` output or was truncated.
- Old or incompatible GraphML may fail if serialized tokenization details changed across package versions.
- If the graph is disconnected, inspect whether the disconnected structure was intentional from explicit edges or a mapper/planner failure.

## Alchemical Network JSON

`AlchemicalNetwork.to_json(path)` writes a JSON representation of a planned campaign. `AlchemicalNetwork.from_json(path)` reads it back.

A planning output folder commonly contains:

```text
alchemicalNetwork/
  alchemicalNetwork.json
  ligand_network.graphml
  transformations/
    rbfe_ligandA_complex_ligandB_complex.json
    rbfe_ligandA_solvent_ligandB_solvent.json
```

The folder base name may determine the alchemical-network JSON filename in CLI-generated outputs. Transformation filenames come from `transformation.name` when present, falling back to a token key.

Use the JSON files as handoff artifacts for execution; do not interpret result estimates from them. Execution and quickrun command construction belong in [cli-workflows](../../cli-workflows/SKILL.md).

## Transformation JSON

A transformation JSON contains one `Transformation` with its two `ChemicalSystem` states, protocol object, and mapping where relevant. For relative ligand transformations, expect:

- `stateA` and `stateB` chemical systems with components such as `ligand`, `solvent`, `protein`, and `cofactor1`.
- A `LigandAtomMapping` between the ligand components.
- A protocol object selected during planning or by planner defaults.

If transformation JSON cannot be read, check whether it was truncated, generated by an incompatible package version, or is actually a result JSON rather than a transformation JSON.

## Explicit Edge Formats

OpenFE can build ligand networks from explicit edge specifications:

| Source | Expected edge syntax | Loader |
| --- | --- | --- |
| Name tuples | Python list such as `[("benzene", "toluene")]` | `generate_network_from_names(ligands, mapper, names)` |
| Index tuples | Python list such as `[(0, 1), (2, 3)]` | `generate_network_from_indices(ligands, mapper, indices)` |
| Orion/NES-style file | Non-comment lines like `benzene >> toluene` | `load_orion_network(ligands, mapper, network_file)` |
| FEP+ `.edges`-style file | Lines like `hash:hash # benzene -> toluene` | `load_fepplus_network(ligands, mapper, network_file)` |

Malformed explicit edge files produce key/format errors. Unknown ligand names or duplicate ligand names should be fixed before retrying.

## Bundled Validator Output

`validate_ligand_inputs.py` emits either text or JSON summaries with:

- import status for OpenFE, RDKit, OpenFF Toolkit, OpenEye, LOMAP, Kartograf, Konnektor, and Perses;
- file existence and extension checks;
- SDF/MOL2 molecule counts when RDKit or lightweight fallback parsing can inspect them;
- ligand-name warnings for empty, placeholder, and duplicate names;
- protein atom-record counts for PDB-like files.

Use `--strict` to make warnings produce a failing exit code in automation.
