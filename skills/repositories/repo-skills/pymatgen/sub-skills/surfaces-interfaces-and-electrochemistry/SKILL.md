---
name: surfaces-interfaces-and-electrochemistry
description: "Use pymatgen surface, interface, Pourbaix, Wulff-shape,
  work-function, substrate-matching, coherent-interface, and
  interfacial-reactivity workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Surfaces, Interfaces, and Electrochemistry

Use this sub-skill when a pymatgen task involves slabs, surface energies, Wulff shapes, work functions, coherent film/substrate interfaces, ZSL substrate matching, Pourbaix diagrams, or interfacial reaction energies.

## Start Here

- Read `references/api-reference.md` for imports, verified constructor signatures, expected objects, and data contracts.
- Read `references/workflows.md` for recipes covering Wulff shapes, slab surface energies, work functions, ZSL/substrate/coherent-interface matching, Pourbaix diagrams, and interfacial reactivity.
- Read `references/troubleshooting.md` before interpreting raw total energies, symbolic surface energies, missing ZSL matches, unexpected slab terminations, invalid Pourbaix entries, or plotting failures.
- Run `scripts/surface_pourbaix_smoke.py --help` to inspect the bundled no-network smoke check; run `scripts/surface_pourbaix_smoke.py --json` to verify tiny in-memory imports/calculations.

## Route Boundaries

- Use this sub-skill for workflow-specific plotting from `WulffShape`, `SurfaceEnergyPlotter`, `PourbaixPlotter`, and `InterfacialReactivity.plot`.
- Route structure construction, slab generation basics, oxidation-state setup, and local-geometry diagnostics to `../structures-local-environments-and-transformations/`.
- Route compatibility-corrected entries, formation energies, phase-diagram entry preparation, and battery workflows to `../entries-thermodynamics-and-batteries/`.
- Route live Materials Project, COD, OPTIMADE, or other network data retrieval to `../external-data-access/`.
- Route generic diffraction, spectrum, VTK, or visualization/backend questions to `../spectra-diffraction-and-visualization/`.

## Safety And Scientific Checks

- Do not treat raw DFT total energies as valid Pourbaix energies; `PourbaixEntry` assumes formation energies aligned to the Pourbaix hydrogen/oxygen/water convention.
- Do not compare surface energies unless slab, bulk, adsorbate, and reservoir references use compatible calculation settings and units.
- Treat negative Wulff/surface energies, missing exact endpoint entries, or symbolic chemical-potential expressions as diagnostics to resolve before ranking facets or reactions.
- Use noninteractive plotting backends in scripts, notebooks on remote systems, CI, and headless terminals.
