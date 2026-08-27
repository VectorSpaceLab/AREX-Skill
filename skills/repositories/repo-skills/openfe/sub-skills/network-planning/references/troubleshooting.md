# Network Planning Troubleshooting

Use this matrix before running simulations. If the symptom is about protocol settings, OpenMM platforms, quickrun execution, or result interpretation, route to the sibling sub-skill named in the recovery step.

## Input and Dependency Failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: rdkit` or SDF/MOL2 counts unavailable | RDKit is missing from the active environment. | Use `validate_ligand_inputs.py` to confirm; install an OpenFE-compatible environment. Do not debug mapping quality until RDKit can parse molecules. |
| `ModuleNotFoundError: openfe` | OpenFE is not installed in the runtime environment. | Check environment installation/imports with the root environment helper when available; do not proceed with planner APIs. |
| `ModuleNotFoundError` for a transitive package while importing `openfe` | The OpenFE environment is incomplete even if the source tree is present. | Fix the OpenFE-compatible environment first; planner imports should come from `openfe` / `openfe.setup`, not direct source-tree paths. |
| `ModuleNotFoundError: openff`, OpenFF Toolkit, AmberTools, NAGL, Espaloma, or OpenEye errors | Charge generation or molecule conversion dependencies are missing. | For planning-only diagnostics, continue if RDKit can read molecules. For charge generation or CLI planning, route exact settings and commands to [cli-workflows](../../cli-workflows/SKILL.md) and protocol/charge implications to [protocols](../../protocols/SKILL.md). |
| `ModuleNotFoundError: kartograf` or `konnektor` | Current mapper/planner path depends on optional mapping/network packages. | Switch to an available mapper only if scientifically acceptable, or install the missing optional dependency. `Konnektor` is required by ligand-network planning functions. |
| `ModuleNotFoundError: lomap` | `LomapAtomMapper`, LOMAP scorers, or `generate_lomap_network` cannot run. | Use `KartografAtomMapper` only if available and appropriate; otherwise install LOMAP. |
| Perses import errors or deprecation warnings | `PersesAtomMapper`/`perses_scorers` require Perses and are deprecated. | Prefer Lomap or Kartograf unless reproducing legacy Perses behavior is the task. |

## Ligand File and Name Failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Validator says no recognized molecule files | Directory contains no non-recursive `.sdf` or `.mol2` files, or a file has the wrong extension. | Move or point to recognized files; do not rely on recursive directory search unless you implement it explicitly. |
| RDKit returns zero valid molecules or `None` for a file | Empty/corrupt SDF/MOL2, unsupported chemistry, malformed records, or sanitization/conformer problems. | Confirm with `validate_ligand_inputs.py --json`; regenerate or repair ligand files before mapping. |
| Ligand names are empty, duplicated, or `*****` | SDF title/MOL2 molecule name is missing or generic. | Rebuild `SmallMoleculeComponent` objects with unique names from a manifest, file stems, or trusted properties before radial/RBFE/RHFE planning. |
| `Multiple ligands called ...` | `generate_radial_network` found more than one matching center name. | Rename ligands or pass the exact central component object instead of a string. |
| `No ligand called ... available` | Requested radial center name is absent. | Print all ligand names and correct the user request or input file names. |
| Duplicate transformation label or overwrite-risk error | Duplicate ligand names or duplicate ligand-network edges created identical state names. | Fix ligand names and remove duplicated edges; rebuild the ligand network and alchemical network. |

## Mapping and Network Failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `StopIteration` from `next(mapper.suggest_mappings(...))` | The mapper returned no mapping for the ligand pair. | Try a maximal diagnostic network; compare `LomapAtomMapper` and `KartografAtomMapper`; inspect whether the transformation is chemically reasonable. |
| `No mapping found between the central ligand ...` | Radial planner cannot map one or more ligands to the hub. | Choose a different hub, allow a less constrained mapper only if valid, or remove/review unmapped ligands. |
| `Unable to create edges for the following nodes ...` | Minimal spanning/redundant planner cannot connect one or more ligands. | Run `generate_maximal_network` to identify isolated ligands; inspect missing pairs directly; fix inputs or split the campaign. |
| `KeyError: score` from minimal spanning planning | A scorer was omitted or mappings lack `score` annotations. | Pass `scorer=openfe.setup.lomap_scorers.default_lomap_score` or a custom scorer returning larger-is-better floats. |
| Warning that multiple mappers were supplied without a scorer | The planner cannot rank mapper outputs. | Provide a scorer, or intentionally use one mapper to avoid arbitrary first-valid selection. |
| Network is disconnected after explicit names/indices | The requested edges leave isolated nodes or separate components. | Decide whether this sparse graph is intentional. For a single campaign, add edges until `network.is_connected()` is true. |
| Mappings look chemically implausible despite existing | Mapper constraints are too loose, ligand protonation/tautomer state is inconsistent, or atom types/coordinates are poor. | Compare distances, ring/element changes, and scores; curate ligand states before protocol handoff. |

## Charged and Difficult Transformations

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Mixed formal charges in a ligand set | Some transformations change net charge and may need explicit charge-correction decisions. | Identify charged pairs during planning, record them in the handoff, and route protocol settings to [protocols](../../protocols/SKILL.md). |
| Dummy-charge or explicit-charge-correction questions | This is a protocol configuration issue, not a ligand-network topology issue. | Keep the planning handoff factual: pair names, mapper, score, formal charges, and selected network topology. Then route to [protocols](../../protocols/SKILL.md). |
| CLI planning emits charge-generation messages or fails on charge backend | CLI planning assigns charges before writing transformation JSONs. | Route command/YAML settings and backend troubleshooting to [cli-workflows](../../cli-workflows/SKILL.md). |

## Serialization and Handoff Failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `LigandNetwork.from_graphml(...)` fails | File is malformed, truncated, not GraphML, or incompatible with current tokenization. | Regenerate from `network.to_graphml()` if possible; otherwise rebuild from original ligands and edge list. |
| `AlchemicalNetwork.from_json(...)` or `Transformation.from_json(...)` fails | File is malformed, from an incompatible version, or is result JSON rather than planning JSON. | Confirm the file layout in [Data Formats](data-formats.md); route result JSONs to [results-analysis](../../results-analysis/SKILL.md). |
| Planning JSON exists but quickrun command fails | Execution command, cache, work directory, or OpenMM backend problem. | Route to [cli-workflows](../../cli-workflows/SKILL.md) for command construction and to [protocols](../../protocols/SKILL.md) for backend/settings. |
| User tries to edit a component, mapping, or network in place | OpenFE/gufe objects are designed as immutable tokenizable objects. | Rebuild corrected objects and regenerate downstream networks/transformations. |

## Fast Triage Checklist

1. Run `python scripts/validate_ligand_inputs.py --molecules <path> --strict`.
2. Confirm at least two unique named ligands.
3. Directly map a failing pair and inspect whether `suggest_mappings` returns anything.
4. Build a maximal network to find isolated ligands.
5. Choose topology after mapper coverage is understood.
6. Record charged pairs and duplicate-name fixes in the protocol/CLI handoff.
7. Do not run OpenMM to diagnose input, mapper, or GraphML/JSON planning failures.
