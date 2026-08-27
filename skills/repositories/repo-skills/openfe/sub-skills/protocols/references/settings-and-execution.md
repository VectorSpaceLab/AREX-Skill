# Settings and Execution

Use this reference when you need to inspect defaults, customize settings, build protocols and transformations, or explain where API planning ends and expensive execution begins.

## Safe Defaults Inspection

Use `default_settings()` as the starting point for every protocol. The returned object is mutable, but the `Protocol` object constructed from it is immutable for provenance.

```python
from openfe.protocols import openmm_rfe

settings = openmm_rfe.RelativeHybridTopologyProtocol.default_settings()
settings.simulation_settings.production_length = "10 ns"
settings.engine_settings.compute_platform = "cuda"
protocol = openmm_rfe.RelativeHybridTopologyProtocol(settings)
```

If a protocol already exists, do not mutate `protocol.settings` and assume execution changes. Rebuild instead:

```python
settings = protocol.settings.model_copy(deep=True)
settings.simulation_settings.production_length = "20 ns"
protocol = type(protocol)(settings)
```

For safe command-line inspection without running OpenMM:

```bash
python scripts/inspect_protocol_defaults.py all --format summary
python scripts/inspect_protocol_defaults.py rbfe --format json
python scripts/inspect_protocol_defaults.py plain-md --format json --fields protocol_repeats engine_settings simulation_settings
```

## Protocol Alias Map

| Alias | Class | Settings object |
| --- | --- | --- |
| `rbfe`, `rfe`, `relative-hybrid-topology` | `openmm_rfe.RelativeHybridTopologyProtocol` | `RelativeHybridTopologyProtocolSettings` |
| `abfe`, `absolute-binding` | `openmm_afe.AbsoluteBindingProtocol` | `AbsoluteBindingSettings` |
| `ahfe`, `absolute-solvation`, `solvation` | `openmm_afe.AbsoluteSolvationProtocol` | `AbsoluteSolvationSettings` |
| `septop`, `separated-topologies` | `openmm_septop.SepTopProtocol` | `SepTopSettings` |
| `plain-md`, `md` | `openmm_md.PlainMDProtocol` | `PlainMDProtocolSettings` |

## Settings Groups to Review

| Group | Applies to | What to change carefully |
| --- | --- | --- |
| `protocol_repeats` | All protocols | Number of independent repeats inside one `ProtocolDAG`. Must be positive. Use repeats for independent simulation replicates rather than creating unrelated DAGs. |
| `forcefield_settings` or leg-specific forcefield settings | All protocols | Protein/small-molecule force fields, nonbonded method, hydrogen mass. Vacuum examples may need `nonbonded_method="nocutoff"`; do not mix with solvent expectations accidentally. |
| `thermo_settings` | All OpenMM protocols | Temperature and pressure. Pressure is only meaningful for periodic solvent/NPT contexts. |
| `partial_charge_settings` | Protocols with small molecules | `partial_charge_method`, `off_toolkit_backend`, conformer count, and NAGL model. Some combinations require AmberTools, OpenEye, NAGL, or Espaloma support. |
| `solvation_settings` or leg-specific solvation settings | Solvated protocols | `solvent_model`, `solvent_padding`, `box_shape`, `number_of_solvent_molecules`, `box_vectors`, `box_size`. Only one periodic cell definition strategy should be active. |
| `lambda_settings` / leg-specific lambda settings | Alchemical protocols | Lambda schedule and window count. Keep lengths monotonic and consistent with replica counts. |
| `simulation_settings` / leg-specific simulation settings | All simulation protocols | Equilibration/production lengths, minimization steps, `sampler_method`, `time_per_iteration`, `n_replicas`. Multistate sampler methods include HREX/repex, SAMS, and independent/no-swap styles depending on protocol. |
| `integrator_settings` / leg-specific integrator settings | All OpenMM protocols | Timestep, Langevin collision rate, barostat type/frequency. `MonteCarloMembraneBarostat` needs membrane-compatible systems and surface tension settings. |
| `engine_settings` / leg-specific engine settings | All OpenMM protocols | `compute_platform` (`cuda`, `opencl`, `cpu`, or `None`) and `gpu_device_index`. `None` lets OpenMMTools choose the fastest mixed-precision platform. |
| `output_settings` / leg-specific output settings | All protocols | Output NetCDF/trajectory/checkpoint names, checkpoint interval, structure names, logs, force-field cache. Checkpoint interval must be compatible with simulation iteration boundaries. |
| `analysis_settings` | SepTop and analysis-capable multistate protocols | Structural analysis selections, strides, and generated plot/NPZ behavior. Detailed interpretation belongs in `../../results-analysis/SKILL.md`. |

## Creating Transformations and ProtocolDAGs

A `Protocol` contains method settings, not chemistry. The chemistry is connected by a `Transformation` or by calling the protocol's `create(...)` method directly.

```python
from openfe import Transformation

transformation = Transformation(
    stateA=state_a,
    stateB=state_b,
    protocol=protocol,
    mapping=mapping,  # required for RBFE/RHFE, omitted for AFE and Plain MD
    name="ligand_a_to_ligand_b_complex",
)
dag = transformation.create()
```

Equivalent lower-level API:

```python
dag = protocol.create(stateA=state_a, stateB=state_b, mapping=mapping)
```

`ProtocolDAG` creation validates the system topology and returns `ProtocolUnit` work. It may create no trajectory data by itself, but it can still perform meaningful validation and object construction. Actual simulation execution starts with `execute_DAG(...)` or the CLI `openfe quickrun`.

```python
import openfe

dag_result = openfe.execute_DAG(
    dag,
    shared_basedir=work_dir,
    scratch_basedir=work_dir,
    keep_shared=True,
)
protocol_result = protocol.gather([dag_result])
```

Do not run `execute_DAG` during planning unless the user explicitly requested simulation execution and accepted the compute/file-writing cost. For CLI execution and scheduler command generation, route to `../../cli-workflows/SKILL.md`.

## What a ProtocolDAG Contains

- `RelativeHybridTopologyProtocol`: one thermodynamic-cycle leg per `ProtocolDAG`; repeats create multiple setup/simulation/analysis units for that leg.
- `AbsoluteBindingProtocol`: complex and solvent legs in one `ProtocolDAG`; repeats duplicate both legs.
- `AbsoluteSolvationProtocol`: solvent and vacuum legs in one `ProtocolDAG`; repeats duplicate both legs.
- `SepTopProtocol`: complex and solvent legs in one `ProtocolDAG`; repeats duplicate both legs, and restraint atom selection is repeated.
- `PlainMDProtocol`: setup and MD simulation units; repeats create multiple independent setup/simulation pairs.

## Backend and Platform Settings

`OpenMMEngineSettings.compute_platform` accepts common values `"cuda"`, `"opencl"`, `"cpu"`, or `None`. The runtime maps case-insensitive names to OpenMM platform names.

- CUDA/OpenCL use mixed precision; CUDA also enables deterministic forces.
- Non-CUDA platforms trigger a performance warning because CPU/OpenCL may be much slower than CUDA.
- `gpu_device_index` is a list of GPU indices for CUDA/OpenCL. Use it only when the scheduler or user explicitly assigns devices.
- `None` asks OpenMMTools to choose the fastest mixed-precision platform. This is useful for portable examples but can hide scheduler misconfiguration.
- For gas-phase/vacuum MD on CPU, setting `OPENMM_CPU_THREADS=1` may improve performance; treat this as execution-environment guidance, not skill runtime configuration.

## Charge-Changing RBFE Case

For an RBFE plan where ligand A and B have different net charges:

1. Confirm that the task is RBFE/RHFE and not SepTop. SepTop currently rejects net charge changes.
2. Prefer `RelativeHybridTopologyProtocol._adaptive_settings(stateA, stateB, mapping)` when full systems and mapping are available.
3. Verify that the adapted settings enabled explicit charge correction and increased sampling: `alchemical_settings.explicit_charge_correction`, `lambda_settings.lambda_windows`, `simulation_settings.n_replicas`, and `simulation_settings.production_length`.
4. If the user already customized defaults, pass `initial_settings=custom_settings` so adaptation preserves those choices where possible.
5. Warn that adaptive settings are experimental and more expensive; backend stability and wall-time limits should be planned before execution.

## Checkpoint, Resume, and Wall-Time Boundaries

- Protocol settings define checkpoint filenames and intervals, but API-level resume requires an `extends`/existing `ProtocolDAGResult` path supported by the protocol implementation and compatible checkpoint files.
- CLI resume behavior is handled by `openfe quickrun --resume`, which uses a cached `ProtocolDAG` plan under the work directory. Command syntax and cache recovery belong in `../../cli-workflows/SKILL.md`.
- Resuming can fail when checkpoint files are missing/corrupt or when the checkpoint system differs from the current protocol settings, including particles, constraints, forces, or barostat configuration.
- Wall-time mitigation is usually a workflow issue: lower `protocol_repeats` per job, use unique result/work directories, checkpoint frequently enough, and submit repeats independently. Use `../../cli-workflows/SKILL.md` for command generation.

## Result Boundary

`protocol.gather([dag_result])` creates a `ProtocolResult`. Free-energy protocols expose `get_estimate()` and `get_uncertainty()`; `PlainMDProtocol` returns `None` for those and exposes trajectory/PDB paths instead. Detailed JSON decoding, gathering across networks, plots, and uncertainty interpretation belong in `../../results-analysis/SKILL.md`.
