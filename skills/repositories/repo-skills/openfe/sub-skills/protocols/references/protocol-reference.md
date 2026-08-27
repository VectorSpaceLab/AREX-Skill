# Protocol Reference

This reference helps choose the OpenFE protocol class and understand the topology constraints each protocol validates before a simulation can be created or run.

## Protocol Selection Matrix

| Task | Protocol class | Typical systems | Mapping requirement | Key constraints and notes |
| --- | --- | --- | --- | --- |
| Relative binding or hydration free energies for similar ligands | `openfe.protocols.openmm_rfe.RelativeHybridTopologyProtocol` | Two `ChemicalSystem` states that differ by one small-molecule ligand; shared protein/solvent context determines RBFE vs RHFE leg | Requires a ligand atom mapping between the transforming ligands | Hybrid topology based on Perses-style common core plus dummy atoms. Each `ProtocolDAG` is one thermodynamic-cycle leg, so RBFE/RHFE campaigns need both environment legs. Net charge changes are supported through more cautious settings when adaptive settings are used. |
| Absolute binding free energy | `openfe.protocols.openmm_afe.AbsoluteBindingProtocol` | Ligand in solvent vs ligand bound to protein plus solvent | No ligand atom mapping | Builds solvent and complex legs in the same `ProtocolDAG`. Uses Boresch-style restraints in the complex leg. Alchemical species with net charge are not currently supported. Disappearing molecules are expected in state A and must be small molecules. |
| Absolute solvation or hydration free energy | `openfe.protocols.openmm_afe.AbsoluteSolvationProtocol` | Ligand in solvent vs ligand removed from solvent/vacuum leg | No ligand atom mapping | Builds solvent and vacuum legs in the same `ProtocolDAG`. Water is the documented solvent target. No protein components, no charged alchemical species, and only one small-molecule alchemical species are supported. |
| Relative binding free energy for chemically diverse ligands | `openfe.protocols.openmm_septop.SepTopProtocol` | Two ligands in complex and solvent contexts | No ligand atom mapping | Separated-topology protocol: both ligand topologies are present, avoiding common-core mapping. It does not support net charge changes between ligands. Complex and solvent legs are included in one `ProtocolDAG`, with restraints in both legs. |
| Conventional MD trajectory generation | `openfe.protocols.openmm_md.PlainMDProtocol` | One `ChemicalSystem`, in solvent or vacuum | Mapping ignored | Not an alchemical free-energy method. `stateA` and `stateB` must be the same object. Produces trajectory/checkpoint/log artifacts and no free-energy estimate. |

## Choosing Between Similar Protocols

- Use `RelativeHybridTopologyProtocol` when ligands are similar enough for an atom mapping and you want RBFE/RHFE edge estimates. It depends strongly on mapping quality and common-core assumptions.
- Use `SepTopProtocol` when ligands are chemically diverse or mapping is undesirable, but avoid it for ligand pairs with net charge changes.
- Use `AbsoluteBindingProtocol` when the scientific question is a ligand's absolute binding free energy to a protein target, not a pairwise ligand difference.
- Use `AbsoluteSolvationProtocol` when the target is transferring a single molecule between vacuum and water/solvent.
- Use `PlainMDProtocol` for equilibration/trajectory tasks and system sanity checks, not for `estimate`/`uncertainty` free-energy output.

## Common Imports

```python
from openfe.protocols import openmm_rfe, openmm_afe, openmm_septop, openmm_md

rbfe_settings = openmm_rfe.RelativeHybridTopologyProtocol.default_settings()
abfe_settings = openmm_afe.AbsoluteBindingProtocol.default_settings()
ahfe_settings = openmm_afe.AbsoluteSolvationProtocol.default_settings()
septop_settings = openmm_septop.SepTopProtocol.default_settings()
md_settings = openmm_md.PlainMDProtocol.default_settings()
```

Construct the protocol only after settings are final:

```python
rbfe_settings.simulation_settings.production_length = "10 ns"
protocol = openmm_rfe.RelativeHybridTopologyProtocol(rbfe_settings)
```

## Protocol-Specific Defaults Worth Inspecting

- `protocol_repeats`: default is three repeats for the alchemical protocols and one repeat for `PlainMDProtocol`. Repeats are independent runs inside one `ProtocolDAG` and are preferred over manually creating separate DAGs for independent repeats.
- `simulation_settings` / `solvent_simulation_settings` / `complex_simulation_settings` / `vacuum_simulation_settings`: contain lengths, replica/window counts, and sampler choices for multistate protocols.
- `lambda_settings`, `solvent_lambda_settings`, `complex_lambda_settings`: define lambda schedules. For RBFE, `lambda_settings.lambda_windows` should remain consistent with multistate replica choices.
- `alchemical_settings`: holds soft-core and charge-correction behavior where supported.
- `engine_settings.compute_platform` and `engine_settings.gpu_device_index`: select OpenMM backend and GPU devices. The default platform setting is CUDA when available.
- `partial_charge_settings`: controls OpenFF charge method and toolkit backend. Optional charge backends may be missing in lightweight environments.
- `output_settings` and leg-specific output settings: control checkpoint, NetCDF, trajectory, structure, and force-field cache filenames.

Run the bundled inspector for a safe summary:

```bash
python scripts/inspect_protocol_defaults.py rbfe --format summary
python scripts/inspect_protocol_defaults.py septop --format json --output septop-defaults.json
```

## Adaptive Settings Caveats

Some protocol classes expose `_adaptive_settings(...)`, but the leading underscore is intentional: it is experimental and subject to change.

- `RelativeHybridTopologyProtocol._adaptive_settings(stateA, stateB, mapping, initial_settings=None)` can adjust RBFE settings for charge-changing transformations by enabling explicit charge correction, using 22 lambda windows/replicas, and increasing production length to 20 ns per window. It can also reduce protein solvation padding to 1 nm and choose membrane-compatible barostat behavior when a membrane component is present.
- `AbsoluteBindingProtocol._adaptive_settings(stateA, stateB, initial_settings=None)` and `SepTopProtocol._adaptive_settings(stateA, stateB, initial_settings=None)` adapt membrane protein systems to use `MonteCarloMembraneBarostat` for the complex leg.
- Do not use `_adaptive_settings()` as a black box replacement for protocol choice. It does not make unsupported transformations valid; for example, SepTop still rejects net charge changes.
- If using adaptive settings after user customization, pass `initial_settings` so adaptation starts from the customized settings copy rather than from defaults.

## Topology Validation Expectations

Protocol validation happens during `protocol.create(...)`, `Transformation.create()`, or execution if validation was deferred. Common failures include:

- RBFE/RHFE: more than one alchemical component per state, alchemical component is not a `SmallMoleculeComponent`, missing or incompatible ligand mapping, solvent/protein mismatch across states.
- ABFE/AHFE: charged alchemical species, disappearing molecule in the wrong state, protein present in an absolute solvation task, missing solvent where required, unsupported non-small-molecule alchemical component.
- SepTop: ligand net charge difference, unsupported non-small-molecule alchemical components, missing protein/solvent context for binding legs, restraint reference atom selection issues.
- Plain MD: `stateA is not stateB`, multiple base solvent components, unsupported solvent/barostat combination, or mapping supplied unnecessarily.

For component creation, atom mapping, and ligand-network generation, route to `../../network-planning/SKILL.md`.
