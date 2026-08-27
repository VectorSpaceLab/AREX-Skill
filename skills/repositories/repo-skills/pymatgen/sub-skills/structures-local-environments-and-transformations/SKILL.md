---
name: structures-local-environments-and-transformations
description: "Construct and analyze pymatgen structures, molecules, local
  environments, graphs, dimensionality, prototypes, magnetism, molecule groups,
  and safe transformation-adjacent workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Structures, Local Environments, and Transformations

Use this sub-skill when the task is about `Structure`, `Molecule`, `Lattice`, local coordination, near neighbors, `CrystalNN`, `VoronoiNN`, `MinimumDistanceNN`, `StructureGraph`, dimensionality, structure matching, molecule matching, functional groups, Chemenv coordination environments, prototypes, or collinear magnetic moments.

## Read First

- For supported imports, inspected signatures, namespace-split notes, and API selection guidance, read `references/api-reference.md`.
- For common in-memory recipes and diagnosis flows, read `references/workflows.md`.
- For predictable failures and recovery steps, read `references/troubleshooting.md`.
- To check a minimal runtime without source fixtures, run `python scripts/structure_neighbor_smoke.py --help`, then `python scripts/structure_neighbor_smoke.py`.

## Routing Boundaries

- Stay here for constructing/manipulating structures or molecules as prerequisites to local-environment, graph, dimensionality, prototype, magnetism, molecule-matching, functional-group, and Chemenv workflows.
- Route computed entries, compatibility corrections, phase-diagram entries, batteries, and Borg/VASP assimilation to `entries-thermodynamics-and-batteries`.
- Route slabs, surfaces, interfaces, Wulff shapes, Pourbaix, and interfacial reactivity to `surfaces-interfaces-and-electrochemistry`.
- Route full `pmg` command syntax, persistent config, environment reporting, and POTCAR setup to `cli-and-configuration`.

## Default Approach

1. Build or load a valid `Structure` or `Molecule`; confirm coordinates, units, ordering, and oxidation states before analysis.
2. Choose and name the neighbor/analysis model: start with `CrystalNN`, compare against `MinimumDistanceNN` or `VoronoiNN` when results are surprising.
3. Preserve site indices and periodic image information when reporting neighbors or graph edges.
4. Build a `StructureGraph` before calling graph or dimensionality functions.
5. Explain optional dependencies and backend choices before using Chemenv, OpenBabel-backed functional groups, `moyopy`, or external `aflow`.

## Important Compatibility Note

Current `pymatgen` installs and uses `pymatgen-core` for core objects and several compatibility-backed analysis modules. Use public imports from `pymatgen.core` and `pymatgen.analysis.*` as shown in `references/api-reference.md`; do not import `Structure` or `Molecule` from the root `pymatgen` package. If a class imported from `pymatgen.analysis.local_env`, `pymatgen.analysis.graphs`, or `pymatgen.analysis.structure_matcher` reports a `pymatgen.core.*` implementation module, treat that as expected compatibility behavior, not a bug.

## Bundled Runtime Assets

- `references/api-reference.md` covers core objects, neighbor strategies, graphs, structure matching, dimensionality, magnetism, prototypes, molecule workflows, Chemenv, and package-split caveats.
- `references/workflows.md` provides copy-adaptable recipes for structures, molecules, neighbor comparison, graph dimensionality, Chemenv, magnetism, prototypes, matching, and serialization.
- `references/troubleshooting.md` gives symptom-driven fixes for namespace split, oxidation states, neighbor disagreement, periodic images, malformed structures, optional extras, Chemenv/prototype backends, structure matching, and unit mistakes.
- `scripts/structure_neighbor_smoke.py` builds tiny in-memory structures and prints deterministic local-environment and dimensionality diagnostics; it performs no network access, fixture reads, destructive writes, GUI opens, or long scans.
