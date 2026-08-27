# MDAnalysis Package Overview

MDAnalysis is organized around a few recurring concepts. Use this overview to choose the right sub-skill before writing code.

## Core Object Model

- `MDAnalysis.Universe` combines topology information with zero or more coordinate/trajectory sources.
- `Universe.atoms`, `Universe.residues`, and `Universe.segments` expose `AtomGroup`, `ResidueGroup`, and `SegmentGroup` objects.
- `AtomGroup` objects carry topology attributes such as names, residue IDs, residue names, masses, charges, bonds, elements, and positions when present.
- `Universe.trajectory` is an iterable reader over `Timestep` objects; positions and dimensions usually update as frames are read.
- `MDAnalysis.Writer(...)`, coordinate writer classes, and `AtomGroup.write(...)` produce coordinate or trajectory outputs when the format supports writing.

## Verified Public Entry Points

The generated skill verified these live signatures for the source baseline:

- `Universe(topology=None, *coordinates, all_coordinates=False, format=None, topology_format=None, transformations=None, guess_bonds=False, vdwradii=None, fudge_factor=0.55, lower_bound=0.1, in_memory=False, context='default', to_guess=('types', 'masses'), force_guess=(), in_memory_step=1, **kwargs)`
- `Universe.empty(n_atoms, n_residues=1, n_segments=1, n_frames=1, atom_resindex=None, residue_segindex=None, trajectory=False, velocities=False, forces=False)`
- `Universe.load_new(filename, format=None, in_memory=False, in_memory_step=1, **kwargs)`
- `AtomGroup.select_atoms(sel, *othersel, periodic=True, rtol=1e-05, atol=1e-08, updating=False, sorted=True, rdkit_kwargs=None, smarts_kwargs=None, **selgroups)`
- `AnalysisBase.run(start=None, stop=None, step=None, frames=None, verbose=None, n_workers=None, n_parts=None, backend=None, unsupported_backend=False, progressbar_kwargs=None)`

For complete route-specific signatures, read the nearest sub-skill reference rather than keeping large API tables in the root skill.

## Install Surface

- Base install covers the core package, NumPy, SciPy, matplotlib, `GridDataFormats`, `mmtf-python`, `joblib`, `tqdm`, `threadpoolctl`, `packaging`, `filelock`, and `mda-xdrlib`.
- `extra_formats` adds optional format/converter packages such as `netCDF4`, `h5py`, `chemfiles`, `parmed`, `pooch`, `pyedr`, `pytng`, `gsd`, `rdkit`, and `imdclient`.
- `analysis` adds optional analysis-related packages such as `biopython`, `seaborn`, `scikit-learn`, `tidynamics`, `networkx`, `waterdynamics`, `pathsimanalysis`, and `mdahole2`.
- `parallel` adds `dask` for supported parallel analysis backends.
- Install narrow optional packages for the failing workflow when possible; do not default to all extras for a single format or converter error.

## Sub-skill Ownership

- `universe-io`: loading, constructing, trajectory iteration, reader/writer factories, synthetic universes, and basic output.
- `selections-topology`: selection strings, grouping semantics, topology attributes, updating selections, fragments, bonds, and selection exporters.
- `analysis-workflows`: built-in analysis modules, custom `AnalysisBase` classes, results containers, slicing, and backend decisions.
- `transformations-writing`: on-the-fly transformations, wrap/unwrap/fit/center operations, transformed outputs, and writer safety.
- `formats-converters`: format support, optional dependencies, converters, auxiliary time series, and network-backed fetch helpers.

## Evidence Translation Rules

- Use examples and tests as evidence for intent, but keep runtime examples self-contained.
- Prefer `Universe.empty` and tiny NumPy arrays for skill-owned scripts.
- Treat optional package failures as narrow dependency decisions.
- Avoid hard-coding force-field assumptions unless the selected topology/trajectory format provides the relevant attributes.
- Validate with `n_atoms`, selected group lengths, frame counts, result shapes, and explicit warnings/errors rather than relying on visual inspection.
