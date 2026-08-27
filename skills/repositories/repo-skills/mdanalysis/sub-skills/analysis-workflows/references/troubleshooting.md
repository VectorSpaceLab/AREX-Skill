# Analysis Troubleshooting

## Frame Slicing and Result Shapes

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ValueError: start/stop/step cannot be combined with frames` | `run()` received both explicit `frames` and one of `start`, `stop`, or `step`. | Choose one slicing style. Use `frames` for explicit indices or boolean masks; use `start/stop/step` for regular slices. |
| Result has fewer rows than trajectory frames | The run used slicing or an empty slice such as `stop=0`. | Inspect `analysis.frames`, `analysis.times`, and `analysis.n_frames` before interpreting `results`. |
| Repeated frame results appear duplicated | `frames=[...]` can intentionally contain repeated indices. | Deduplicate frames yourself if repeated rows are not desired. |
| Deprecated warning for `rmsd`, `timeseries`, `hbonds`, `rdf`, `bins`, `edges`, or `count` | Direct result aliases are deprecated. | Use `analysis.results.<name>` or `analysis.results["<name>"]`. |

## Empty or Wrong Selections

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Empty result arrays or all-zero contact/H-bond counts | A selection produced no atoms or selected atoms that cannot satisfy the cutoff. | Check `len(u.select_atoms(sel))` for every selection and route syntax debugging to `../selections-topology/SKILL.md`. |
| `SelectionError` in RMSD/RMSF/alignment | Mobile and reference selections have different atom counts or incompatible atom ordering. | Print atom counts and representative names/resids for both selections; use ordered selections or a mobile/reference selection dictionary when needed. |
| `Contacts` rejects a selection object | `Contacts` accepts selection strings or static AtomGroups, not updating AtomGroups. | Pass selection strings or convert to a static `AtomGroup` before constructing `Contacts`. |

## Missing Topology Attributes

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| RMSD/alignment fails on masses | `weights="mass"` or default mass checking needs masses; synthetic/minimal topologies may lack masses or use mismatched masses. | Add masses during Universe construction, use `weights=None`, or increase `tol_mass` only when atom equivalence has been independently verified. |
| Hydrogen bond guessing fails or returns none | Guessing depends on charges/masses and sometimes bonds. Minimal topologies often lack these attributes. | Provide explicit `donors_sel`, `hydrogens_sel`, and `acceptors_sel`; or add/guess required topology attributes using the selections/topology sub-skill. |
| Hydrogen bond `lifetime()` raises that `.hbonds` is `None` | Lifetime was called before `run()`. | Call `h.run(...)` first and verify `h.results.hbonds` is not `None`. Empty arrays are allowed; `None` means not computed. |

## Periodic Boundary Conditions

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Distance/contact/RDF values ignore wraparound | `box=None` or timestep dimensions are missing. | Use `box=u.trajectory.ts.dimensions` for distance functions and set `pbc=True` for contacts/leaflet workflows that should use PBC. |
| RMSD/RMSF jumps unexpectedly under PBC | Molecules are split across boundaries or not aligned before RMSF. | Route transformations and make-whole/unwrap/fit pipelines to `../transformations-writing/SKILL.md` before RMSD/RMSF. |
| Density grid bounds or RDF normalization look wrong | Missing or inconsistent unit-cell dimensions. | Validate `ts.dimensions` across analyzed frames; use explicit density grid dimensions when trajectory boxes are unsuitable. |

## Backends and Optional Dependencies

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `Can not parallelize class ...` | The analysis class is serial-only, such as current `RMSF`. | Run serial or choose an analysis class with `"multiprocessing"`/`"dask"` in `get_supported_backends()`. |
| `module 'dask' is missing` | `backend="dask"` requires optional dask installation. | Use serial/multiprocessing or install the documented parallel extra/dependency in the user environment. Do not claim dask is part of base MDAnalysis. |
| Progress bar error with multiprocessing/dask | `verbose=True` or `progressbar_kwargs` was used with a non-serial backend. | Do a short serial run for ETA, then run the larger job with the parallel backend and no progress bar. |
| Pickling or serialization errors | Custom analysis stores non-serializable state or trajectory/transformation objects are not suitable for multiprocessing. | Validate serial first; reduce stored state in `__init__`; try `backend="dask"` if installed; otherwise keep serial. |
| `distance_array(..., backend="distopia")` fails | Optional `distopia` backend is not installed or does not support the function. | Use `backend="serial"` or `"OpenMP"`; select `distopia` only when installed and after tolerance-based validation. |

## Alignment and RMSD

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Mass mismatch error in `RMSD`, `alignto`, or `AlignTraj` | Matched atoms differ by more than `tol_mass`; mobile/reference selections may not be equivalent. | First fix selections/order. If matching is intentionally by geometry rather than mass, use `weights=None` and a larger `tol_mass` only with a documented rationale. |
| Group RMSD columns do not look fitted independently | `RMSD(groupselections=...)` computes group RMSDs after the main fit; groups are not independently superimposed. | Use separate RMSD runs if each domain/group needs its own optimal fit. |
| `AlignTraj` writes unexpected output | `filename`, `prefix`, `force`, and `in_memory` control writer behavior. | Use `in_memory=True` for no output file, or set an explicit filename and writer kwargs. Route write-format details to `../transformations-writing/SKILL.md`. |

## Module Path and API Drift

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Import from `MDAnalysis.analysis.hbonds...` fails or warns | Old hydrogen-bond module paths are deprecated/legacy. | Prefer `MDAnalysis.analysis.hydrogenbonds.hbond_analysis.HydrogenBondAnalysis`. |
| Old code passes `start`, `stop`, or `step` to an analysis constructor | Modern AnalysisBase analyses expect frame slicing in `run()`. | Instantiate with analysis-specific parameters only, then call `analysis.run(start=..., stop=..., step=...)`. |
| Old code reads direct attributes like `rdf.rdf` or `contacts.timeseries` | Result aliases remain only for backward compatibility. | Migrate to `analysis.results.rdf`, `analysis.results.timeseries`, etc. |
