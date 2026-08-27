# Protocol Troubleshooting

Use this matrix to diagnose protocol selection, settings, OpenMM backend, parameterization, and resume failures. For CLI command errors route to `../../cli-workflows/SKILL.md`; for estimate/uncertainty interpretation route to `../../results-analysis/SKILL.md`.

| Symptom | Likely cause | Recovery steps |
| --- | --- | --- |
| `ValueError` about more than one alchemical component or non-small-molecule alchemical component | Wrong protocol for the topology, or `ChemicalSystem` states differ in protein/solvent/cofactor components instead of only the intended ligand | Re-check `stateA.component_diff(stateB)` conceptually. Use `RelativeHybridTopologyProtocol` only for one mapped small-molecule transformation. Use `PlainMDProtocol` for non-alchemical dynamics. Route component construction issues to `../../network-planning/SKILL.md`. |
| RBFE/RHFE creation fails due to missing or invalid mapping | `RelativeHybridTopologyProtocol` needs ligand atom mapping; mapping may not correspond to the transformed ligands | Build or repair ligand mappings in `../../network-planning/SKILL.md`. Do not switch to SepTop automatically unless the user wants separated topologies and the ligands have no net charge change. |
| SepTop rejects charge-changing ligands | `SepTopProtocol` does not support net charge changes between ligands | Use RBFE/RHFE with `RelativeHybridTopologyProtocol` and consider `_adaptive_settings()` for charge-changing transformations, or redesign the ligand pair/campaign. Explain added sampling cost and backend risk. |
| Absolute solvation rejects a protein or missing solvent | `AbsoluteSolvationProtocol` is for a molecule transferred between solvent and vacuum; no protein components are allowed and solvent must be present where expected | Use `AbsoluteBindingProtocol` for protein-ligand binding, `PlainMDProtocol` for ordinary MD, or rebuild the solvation states with exactly one small-molecule alchemical species. |
| ABFE/AHFE rejects a charged alchemical species | Absolute protocols currently do not support alchemical species with net charge | Use a neutral ligand, choose a different scientific protocol, or escalate to a domain expert. Do not bypass validation by editing internals. |
| Editing `settings` after constructing `protocol` has no effect | Protocol objects are immutable for provenance, and execution uses the settings captured at construction | Copy or recreate settings, apply changes, and instantiate a new protocol. Example: `settings = protocol.settings.model_copy(deep=True); settings.protocol_repeats = 1; protocol = type(protocol)(settings)`. |
| `protocol_repeats must be a positive value` | `protocol_repeats` was set to zero or a negative integer | Set a positive integer. For one simulation per scheduler job, use `protocol_repeats = 1` and generate separate repeat commands via `../../cli-workflows/SKILL.md`. |
| Lambda/window validation failure | Lambda arrays are non-monotonic, different lengths, or inconsistent with replica/window counts | Start from `default_settings()` again and change only required fields. For RBFE charge changes, prefer `_adaptive_settings()` over hand-editing window schedules. Keep `n_replicas` and lambda windows aligned. |
| Checkpoint interval or iteration length validation failure | `output_settings.checkpoint_interval` does not divide cleanly into multistate `time_per_iteration`, or a duration is negative/zero | Use positive durations with units or strings such as `"10 ns"`. Keep checkpoint intervals at integer multiples of multistate iteration lengths. Inspect defaults with `scripts/inspect_protocol_defaults.py`. |
| `compute_platform="foo"` or platform name error | `OpenMMEngineSettings.compute_platform` only accepts common OpenMM backend names | Use `"cuda"`, `"opencl"`, `"cpu"`, or `None`. Prefer CUDA for production if available; use CPU only for small smoke tests or when GPU is unavailable. |
| Warning: non-CUDA platform selected | CPU or OpenCL backend is in use and may be much slower | Confirm the scheduler/GPU allocation. If CUDA is expected, check environment modules, drivers, and OpenMM installation. If CPU is intentional, warn about speed and consider reducing test scope. |
| CUDA/PTX/driver/OpenMM failure at execution | CUDA runtime, GPU driver, OpenMM build, or device selection is incompatible | Do not retry blindly with production settings. Check available platforms with a safe environment diagnostic, try `compute_platform=None` or `"cpu"` only for minimal smoke tests, and ask the user before long reruns. For installation-level checks, use the root skill's environment helper if available. |
| Missing AmberTools, OpenEye, NAGL, Espaloma, or OpenFF backend errors | `partial_charge_settings` selected an optional charge method/toolkit backend that is not installed or licensed | Choose a supported backend/method combination: default `am1bcc` with AmberTools when available, OpenEye only when licensed, NAGL only when the model package is present, Espaloma only with supported backends. Route charge-generation CLI tasks to `../../cli-workflows/SKILL.md`. |
| `ModuleNotFoundError: openfe_analysis` while importing or inspecting SepTop | `SepTopProtocol` imports structural-analysis helpers from the separate `openfe-analysis` package through its protocol units; the project environment pins `openfe-analysis>=0.5.0` | Install or activate an OpenFE environment that includes `openfe-analysis>=0.5.0` before using `openmm_septop` or the defaults inspector for `septop`. If only non-SepTop protocols are needed, inspect those aliases separately and avoid importing `openfe.protocols.openmm_septop`. |
| JAX, PyMBAR, `openfe-analysis`, or timeseries warning appears during analysis | Analysis dependencies may emit numerical/backend warnings, structural-analysis warnings, or MBAR convergence assumptions may be weak | Distinguish warnings from hard protocol failures. Check whether `ProtocolDAGResult` units are `ok()`. For convergence interpretation, overlap plots, structural plots, and uncertainty discussion, route to `../../results-analysis/SKILL.md`. |
| Ligand RMSD/COM drift analysis indicates unstable binding pose | The ligand may have left the binding pocket or the input pose/equilibration is unstable | Treat the free-energy estimate as suspect. Review input pose preparation, restraints, equilibration length, and structural outputs. Route result artifact interpretation to `../../results-analysis/SKILL.md`. |
| Resume fails with system/checkpoint mismatch | Checkpoint was produced by a different protocol/settings/system, or files are partially written/corrupt | Resume only with the same transformation, work directory, output path, protocol settings, platform-compatible files, and cache/checkpoint set. If cache is corrupt, follow CLI recovery in `../../cli-workflows/SKILL.md`. |
| Job hits wall-time before completion | Sampling length/repeats are too large for allocation, checkpointing may be too sparse, or repeats were run serially | Use `protocol_repeats=1` for per-repeat jobs, unique result/work paths, and `quickrun --resume` for interrupted jobs. Command generation belongs in `../../cli-workflows/SKILL.md`. |
| Plain MD returns no estimate or uncertainty | `PlainMDProtocol` is a trajectory protocol, not a free-energy estimator | Use trajectory/PDB outputs for MD analysis. Choose an alchemical protocol if the user needs free-energy estimates. |

## Rebuild Pattern for Immutable Protocols

When a user says a settings edit did not change the run, answer with this pattern:

```python
settings = old_protocol.settings.model_copy(deep=True)
settings.simulation_settings.production_length = "10 ns"
settings.engine_settings.compute_platform = "cuda"
new_protocol = type(old_protocol)(settings)
```

Then recreate the `Transformation` or `ProtocolDAG`; do not reuse a `ProtocolDAG` made from the old protocol.

## Backend Safety Checklist Before Execution

- Confirm the protocol is valid for the topology before spending GPU time.
- Confirm `engine_settings.compute_platform` matches the available backend; use `None` only when automatic fastest-platform choice is desired.
- Confirm optional charge toolkits selected in `partial_charge_settings` are installed and licensed if required.
- Confirm output filenames and work directories will not overwrite another repeat.
- Confirm checkpoint intervals and wall-time strategy are adequate for the expected production length.
- Confirm the user explicitly requested execution before running `execute_DAG` or `openfe quickrun`.

## Difficult Cases

### RBFE plan with net charge changes

Use `RelativeHybridTopologyProtocol`, not `SepTopProtocol`. If `stateA`, `stateB`, and the mapping are available, derive settings with `_adaptive_settings(...)` and then inspect the changes: explicit charge correction, 22 lambda windows/replicas, and 20 ns production length per window. State clearly that this is more expensive and experimental, and that CUDA/backend stability and wall-time planning should be solved before execution.

### Settings edited after protocol construction

Explain that the protocol captured its settings at construction time for provenance. Mutating the original settings object or a settings view afterward does not update an already created protocol, transformation, or DAG. Rebuild settings, instantiate a new protocol, recreate the transformation/DAG, then execute only if requested.
