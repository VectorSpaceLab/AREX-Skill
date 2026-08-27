---
name: formats-converters
description: "Navigate MDAnalysis format support, optional format dependencies,
  auxiliary data, fetchers, and converters to RDKit, OpenMM, and ParmEd."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# MDAnalysis Formats and Converters

Use this sub-skill when a task is about choosing an MDAnalysis file format, diagnosing optional format dependencies, attaching auxiliary data, fetching PDB files, or converting between MDAnalysis objects and RDKit, OpenMM, or ParmEd objects.

## Start Here

1. Identify whether the user is asking about file support, optional dependencies, auxiliary time series, network fetching, or conversion to another library.
2. Read [references/format-support.md](references/format-support.md) for supported coordinate/topology families, `format=` and `topology_format=`, optional dependency groups, and when not to rely on automatic guessing.
3. Read [references/converters-auxiliary.md](references/converters-auxiliary.md) for `AtomGroup.convert_to(...)`, RDKit/OpenMM/ParmEd object handling, `XVG`/`EDR` auxiliary workflows, and `fetch.from_PDB` behavior.
4. Use [references/troubleshooting.md](references/troubleshooting.md) when errors mention missing packages, unknown formats, unit/box limitations, fetch failures, or converter metadata loss.
5. Run `python scripts/format_dependency_check.py` from this sub-skill directory only when you need a local optional-dependency availability report.

## Route Elsewhere

- For normal `Universe(...)`, `Universe.load_new(...)`, trajectory iteration, and writing trajectories from `Universe` or `AtomGroup`, use `../universe-io/SKILL.md`.
- For atom selection syntax, topology attributes, topology guessing, fragments, bonds, and selection exporters, use `../selections-topology/SKILL.md`.
- For transformations before writing output trajectories, use `../transformations-writing/SKILL.md`.
- For analysis modules that consume loaded trajectories, use `../analysis-workflows/SKILL.md`.

## Key Decisions

- Prefer native MDAnalysis readers/writers when the format appears in the supported format tables; use `format=` or `topology_format=` to override ambiguous extensions or object guessing.
- Install the narrow optional package that owns the failed workflow instead of broad extras: `h5py` for H5MD, `chemfiles` for the Chemfiles backend, `gsd` for HOOMD GSD, `pytng` for TNG, `pyedr` for EDR auxiliary files, `pooch` for `fetch.from_PDB`, `rdkit` for RDKit conversion, `parmed` for ParmEd conversion, and `imdclient` for IMD streams.
- Treat external converters as interoperability helpers, not lossless round-trips: verify bonds, elements, charges, residue metadata, units, and coordinates after conversion.
- Avoid network fetches, live IMD streams, and heavyweight optional conversions in automated checks unless the user explicitly requested and the environment is appropriate.

## Bundled References

- [references/format-support.md](references/format-support.md): format matrix guidance, optional dependencies, explicit format selection, fetch format caveats.
- [references/converters-auxiliary.md](references/converters-auxiliary.md): converter APIs, RDKit failure recovery, OpenMM/ParmEd handling, auxiliary data recipes.
- [references/troubleshooting.md](references/troubleshooting.md): precise recovery steps for common format, dependency, fetch, unit, and converter failures.
