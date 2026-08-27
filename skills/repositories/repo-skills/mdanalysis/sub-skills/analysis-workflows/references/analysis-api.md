# Analysis API Reference

This reference is for agents using MDAnalysis 2.11-style analysis APIs. It distills the public behavior of `MDAnalysis.analysis.base`, `results`, `backends`, and common analysis modules.

## Core AnalysisBase Contract

| API | Use | Key outputs and constraints |
| --- | --- | --- |
| `AnalysisBase(trajectory, verbose=False, **kwargs)` | Base class for trajectory analyses. Pass a trajectory reader, usually `u.trajectory` or `atomgroup.universe.trajectory`. | Subclasses implement `_prepare()`, `_single_frame()`, and optionally `_conclude()` and `_get_aggregator()`. |
| `analysis.run(start=None, stop=None, step=None, frames=None, verbose=None, n_workers=None, n_parts=None, backend=None, unsupported_backend=False, progressbar_kwargs=None)` | Execute the analysis. | Returns `self`; fills `analysis.frames`, `analysis.times`, `analysis.n_frames`, and `analysis.results`. |
| `frames=[...]` | Analyze explicit frame indices or a boolean mask. | Cannot be combined with `start`, `stop`, or `step`; repeated indices are preserved. Boolean masks are converted to selected frame numbers. |
| `start/stop/step` | Analyze a trajectory slice. | Uses trajectory slice semantics after `check_slice_indices`; `stop=0` is a valid empty run for many analyses. |
| `Results` | Results container stored on `analysis.results`. | Dict-like and attribute-like: `results["rmsd"]` and `results.rmsd` are equivalent for valid keys. |
| `ResultsGroup` | Aggregator for parallel runs. | Use lookup functions such as `ndarray_vstack`, `ndarray_hstack`, `ndarray_sum`, `ndarray_mean`, `float_mean`, or `flatten_sequence`. |

During `_single_frame()`, subclasses can use `self._frame_index` for the row in the result array, `self._ts` for the current timestep, `self._sliced_trajectory` for the active iterator, and `self.results` for accumulation. Allocate arrays in `_prepare()` using `self.n_frames`, fill row `self._frame_index` in `_single_frame()`, and normalize or convert lists in `_conclude()`.

## Backend Rules

| Backend surface | Accepted values | Practical rule |
| --- | --- | --- |
| `AnalysisBase.run(backend=...)` | `None`/`"serial"`, `"multiprocessing"`, `"dask"`, or a `BackendBase` instance. | Serial is default. Check `SomeAnalysis.get_supported_backends()` before selecting multiprocessing or dask. |
| `n_workers` | Positive integer; default is 1 unless the backend object carries its own worker count. | Do not pass conflicting `n_workers` both in a backend instance and in `run()`. |
| `n_parts` | Number of computation chunks; defaults to `n_workers`. | If more workers than frames are requested, MDAnalysis may reduce parts and warn. |
| `progressbar_kwargs` / `verbose=True` | Serial backend only. | Non-serial backend plus progress output raises `ValueError`. |
| Custom backends | Subclass `MDAnalysis.analysis.backends.BackendBase` with `apply(func, computations)`. | Pass `unsupported_backend=True` only after comparing results with a supported backend. |
| Distance backends | Many `MDAnalysis.lib.distances` functions accept `backend="serial"`, `"OpenMP"`, or `"distopia"`. | `distopia` is optional and must be explicitly installed/selected; precision can differ slightly. |

Analysis backend support is class-specific. Examples verified in this scope: `RMSD`, `Contacts`, `InterRDF`, and `HydrogenBondAnalysis` expose split-apply-combine support; `RMSF` is serial-only in its current implementation.

## Common Analysis Result Shapes

| Module/API | Constructor essentials | Result access | Shape and interpretation |
| --- | --- | --- | --- |
| `MDAnalysis.analysis.rms.RMSD(atomgroup, reference=None, select="all", groupselections=None, weights=None, weights_groupselections=False, tol_mass=0.1, ref_frame=0, **kwargs)` | Mobile atom group or universe; optional reference; `select` must produce equivalent mobile/reference atoms. | `rmsd.results.rmsd` | `(n_frames, 3 + n_groupselections)`. Columns are frame, time, fitted RMSD, then one RMSD per `groupselections` after the main fit. |
| `MDAnalysis.analysis.rms.RMSF(atomgroup, **kwargs)` | AtomGroup from an already aligned/whole trajectory. | `rmsf.results.rmsf` | `(n_atoms,)`; no PBC handling or structural superposition is performed by RMSF. |
| `MDAnalysis.analysis.align.AlignTraj(mobile, reference, select="all", filename=None, prefix="rmsfit_", weights=None, tol_mass=0.1, match_atoms=True, strict=False, force=True, in_memory=False, writer_kwargs=None, **kwargs)` | Mobile/reference universes or atom groups; writes aligned coordinates unless `in_memory=True` or `filename=None` behavior selects a null/in-memory path. | `aligner.results.rmsd` | `(n_frames,)` RMSD before/aligned per frame; watch file overwrite behavior and atom matching. |
| `MDAnalysis.analysis.contacts.Contacts(u, select, refgroup, method="hard_cut", radius=4.5, pbc=True, kwargs=None, **basekwargs)` | `select` is a pair of selection strings or static AtomGroups; `refgroup` is one pair or a list of pairs. | `contacts.results.timeseries` | `(n_frames, 1 + n_ref_pairs)`. First column is frame; following columns are contact fractions. |
| `MDAnalysis.analysis.distances.distance_array(reference, configuration, box=None, result=None, backend="serial")` | NumPy arrays or AtomGroups for coordinates; optional unit-cell dimensions. | Return value, optionally same object as `result`. | `(n_reference, n_configuration)` float64 distances. With `box`, minimum-image convention is applied. `result` must be float64 and exact shape. |
| `MDAnalysis.analysis.rdf.InterRDF(g1, g2, nbins=75, range=(0.0, 15.0), norm="rdf", exclusion_block=None, exclude_same=None, backend="serial", **kwargs)` | Two AtomGroups; optional pair exclusions. | `rdf.results.bins`, `rdf.results.edges`, `rdf.results.count`, `rdf.results.rdf` | `bins`, `count`, and `rdf` are length `nbins`; `edges` is length `nbins + 1`. `norm` is `"rdf"`, `"density"`, or `"none"`. |
| `MDAnalysis.analysis.hydrogenbonds.hbond_analysis.HydrogenBondAnalysis(universe, donors_sel=None, hydrogens_sel=None, acceptors_sel=None, between=None, d_h_cutoff=1.2, d_a_cutoff=3.0, d_h_a_angle_cutoff=150, update_selections=True)` | Universe plus explicit or guessed donor/hydrogen/acceptor selections. | `h.results.hbonds`; helpers `count_by_time()`, `count_by_type()`, `count_by_ids()`, `lifetime()` | `results.hbonds` has columns frame, donor index, hydrogen index, acceptor index, donor-acceptor distance, D-H-A angle. Empty result is possible. |

Prefer `analysis.results.<name>` over deprecated direct aliases such as `analysis.rmsd`, `analysis.timeseries`, `rdf.rdf`, or `h.hbonds`; those aliases emit deprecation warnings and are targeted for removal in MDAnalysis 3.0.

## Overview of Other Analysis Modules

| Module | Best use | Important caveats |
| --- | --- | --- |
| `MDAnalysis.analysis.pca.PCA` | Principal component analysis on selected atoms; use `run()` before `transform()`, `project_single_frame()`, `rmsip()`, or `cumulative_overlap()`. | Results include `results.p_components` and `results.variance`; transform/project methods fail until `run()` has populated results. |
| `MDAnalysis.analysis.msd.EinsteinMSD` | Mean-squared displacement with `msd_type` among `xyz`, `xy`, `yz`, `xz`, `x`, `y`, `z`. | Default `fft=True` requires optional `tidynamics`; use `fft=False` if it is unavailable or if trajectory sampling is non-linear. |
| `MDAnalysis.analysis.leaflet.LeafletFinder` | Split membrane headgroup atoms into connected components using a distance cutoff. | Requires a meaningful selection and cutoff; `pbc=True` uses box dimensions. `groups()` returns AtomGroups; `sizes()` reports component sizes. |
| `MDAnalysis.analysis.density.DensityAnalysis` | Build a 3D density grid for an AtomGroup. | `results.density` is a density object. Explicit `gridcenter` with `xdim`/`ydim`/`zdim` ignores padding and requires all dimensions. |

For less common modules, still follow the same pattern: instantiate with AtomGroups/selections, call `run()` with frame slicing, read `results`, and check module-specific optional dependencies before assuming availability.
