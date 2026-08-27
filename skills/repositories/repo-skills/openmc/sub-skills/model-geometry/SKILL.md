---
name: model-geometry
description: "Construct and validate OpenMC Python model inputs: materials, CSG
  geometry, universes, lattices, sources, settings, plots, IDs, bounding boxes,
  and XML exports."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Model and geometry

Use this route when the task is to build or inspect OpenMC **input objects** in
Python. Keep the work at model-construction level: do not run transport, infer
nuclear-data availability, or analyze statepoints and tallies.

## Route by need

- For object APIs, type checks, IDs, CSG, lattices, transforms, and XML tags,
  read [api-reference.md](references/api-reference.md).
- For a novice pin cell, a repeated-universe/lattice model, custom or
  parameterized source, or XML-only validation, read
  [modeling-workflows.md](references/modeling-workflows.md).
- For failures, warnings, missing prerequisites, malformed XML, or finite
  bounding-box issues, read [troubleshooting.md](references/troubleshooting.md).
- To generate a deterministic, transport-free fixture, use
  [scripts/build_minimal_model.py](scripts/build_minimal_model.py). Run its
  `--help` first, then pass the required explicit `--output-dir`; it writes
  and validates `materials.xml`, `geometry.xml`, `settings.xml`, and
  `model.xml` for a material-filled sphere cell in an explicit universe.

## Operating contract

1. Choose explicit IDs or call `openmc.reset_auto_ids()` at the start of an
   isolated construction. Treat duplicate explicit-ID warnings as a model
   ownership problem; do not silence them.
2. Build the object graph in dependency order: materials and distributions,
   surfaces and half-spaces, cells, universes/lattices, root geometry, settings,
   optional plots, then `openmc.Model`.
3. Validate with Python-level assertions before any native execution: object
   types, fill/region relationships, lattice shape/indexing, source and
   settings values, finite/infinite bounding-box expectations, and XML parse
   results.
4. Use `Model.export_to_xml(directory=...)` for separate input files and
   `Model.export_to_model_xml(path=...)` for one combined model document. XML
   generation is not a transport run and does not require
   `OPENMC_CROSS_SECTIONS`; a later transport run has separate runtime/data
   prerequisites owned by `setup-runtime`.
5. Keep tally/result arithmetic, StatePoint/summary readers, data libraries,
   depletion, C API/library mode, build flags, and advanced solvers in their
   owning routes. Link back to those routes rather than expanding this one.

## Definition of done

A model-geometry task is complete when the requested Python graph is
constructible, invalid assignments fail with the expected exception class,
`geometry.bounding_box` and lattice/source choices are checked, and the
requested XML file(s) are written and parsed. The bundled fixture is a
transport-free smoke case and does not establish that a compiled executable,
native shared library, or cross-section data is available. Classify such
checks as optional/blocked instead of treating XML construction as failed.
