# Troubleshooting: Structures, Local Environments, and Transformations

Use this guide when imports look wrong, neighbor strategies disagree, structure matching fails, dimensionality errors mention graphs, Chemenv/prototype backends are missing, magnetic analysis surprises you, or units/coordinate assumptions are unclear.

## Import or Signature Mismatch After the Core Split

Symptoms:

- `from pymatgen.analysis.local_env import CrystalNN` works, but `CrystalNN.__module__` is `pymatgen.core.local_env`.
- `StructureGraph`, `StructureMatcher`, or molecule matchers appear under `pymatgen.core.*`.
- Old snippets with `from pymatgen import Structure` fail.

Recovery:

1. Explain that current `pymatgen` uses `pymatgen-core` for core objects and compatibility-backed analysis modules.
2. Use supported imports:

   ```python
   from pymatgen.core import Lattice, Molecule, Structure
   from pymatgen.analysis.local_env import CrystalNN, MinimumDistanceNN, VoronoiNN
   from pymatgen.analysis.graphs import StructureGraph
   ```

3. Treat a `pymatgen.core.*` implementation module as expected unless the import itself fails.
4. If import fails, check that the environment installed `pymatgen` for Python `>=3.11`; do not publish local environment paths in user-facing guidance.

## Missing or Ambiguous Oxidation States

Symptoms:

- `CrystalNN(cation_anion=True)` returns no neighbors or fewer neighbors than expected.
- Chemenv or bond-valence paths cannot infer valences.
- Magnetic analysis with `detect_valences=True` warns about valence assignment.
- `StructureMatcher` fails because one structure uses `Fe2+` and another uses `Fe`.

Recovery:

- Add oxidation states only when chemically justified:

  ```python
  structure = structure.copy()
  structure.add_oxidation_state_by_element({"Cs": 1, "Cl": -1})
  ```

- If valences are unknown, compare `CrystalNN(cation_anion=False)` with `MinimumDistanceNN` and clearly state uncertainty.
- For mixed-valence or disordered systems, ask for expected valences instead of inventing them.
- For structure matching, choose `ElementComparator` only when ignoring oxidation states is intended.

## Neighbor Strategy Disagreement

Symptoms:

- `CrystalNN`, `MinimumDistanceNN`, and `VoronoiNN` return different coordination numbers.
- A porous or open framework has extra weak contacts.
- Raw Voronoi rows include same-species or far periodic-image contacts.

Recovery workflow:

1. Print species, distance, image, and weight for each strategy:

   ```python
   for item in strategy.get_nn_info(structure, site_index):
       neighbor = item["site"]
       print(neighbor.species_string, structure[site_index].distance(neighbor), item.get("image"), item.get("weight"))
   ```

2. Check oxidation states if `cation_anion=True` or charge filtering is expected.
3. Record parameters such as `search_cutoff`, `distance_cutoffs`, `tol`, and `cutoff`.
4. Distinguish raw Voronoi contacts from chemically intended coordination.
5. Report a strategy-specific answer instead of claiming one universal coordination number.

Selection guide:

| Task | Prefer | Why |
| --- | --- | --- |
| General coordination in crystals | `CrystalNN` | Balances Voronoi geometry, distance, and electronegativity heuristics. |
| Simple deterministic shell | `MinimumDistanceNN` | Easy to explain and reproduce. |
| Diagnostic topology/weights | `VoronoiNN` | Shows raw Voronoi contacts and weights. |
| Radius-based covalent graph | `JmolNN` | Useful when a covalent-radius heuristic is intended. |

## Periodic Image and Site-Index Confusion

Symptoms:

- Neighbor rows include image vectors such as `(0, -1, 0)`.
- A neighbor appears to have the same unit-cell index as the center site.
- Graph edges cross the unit-cell boundary.

Recovery:

- Explain that periodic structures represent infinite crystals; images are required for correct distances and dimensionality.
- Preserve both the unit-cell site index and the image vector in reports.
- Use `item.get("image")` from near-neighbor dictionaries and `structure[site_index].distance(neighbor_site)` for distances.
- Do not drop cross-boundary graph edges unless the user explicitly wants a finite cluster approximation.

## Dimensionality Errors

Symptoms:

- `get_dimensionality_larsen(structure)` fails on a bare `Structure`.
- Dimensionality changes when switching `CrystalNN` to a distance-based strategy.
- A zero-dimensional component cannot be converted to a `MoleculeGraph`.

Recovery:

```python
from pymatgen.analysis.dimensionality import get_dimensionality_larsen, get_structure_components
from pymatgen.analysis.local_env import CrystalNN

bonded = CrystalNN().get_bonded_structure(structure)
print(get_dimensionality_larsen(bonded))
print(get_structure_components(bonded, inc_orientation=True, inc_site_ids=True))
```

- Always state how the bonded graph was created.
- Compare multiple graph-building strategies for ambiguous structures.
- Use `inc_molecule_graph=True` only when zero-dimensional molecular components are plausible.

## StructureMatcher Failures

Symptoms:

- Two visually similar structures do not match.
- One structure has oxidation states and the other is neutral.
- Matching changes after primitive reduction, scaling, supercell attempts, or ignored species.

Recovery:

1. Print formulas, species strings, lattice parameters, site counts, and whether both structures are ordered.
2. Record `StructureMatcher` settings: `ltol`, `stol`, `angle_tol`, `primitive_cell`, `scale`, `attempt_supercell`, `allow_subset`, `supercell_size`, `ignored_species`, and `comparator`.
3. Try `SpeciesComparator` for strict species/oxidation-state matching and `ElementComparator` only when oxidation states should be ignored.
4. Use `fit_anonymous` for prototype-like matching where species identity is intentionally ignored.
5. Avoid loosening tolerances until coordinate units and lattice conventions are confirmed.

## Chemenv Failures or Slow Runs

Symptoms:

- Chemenv takes too long on a large structure.
- Bond-valence analysis cannot determine valences.
- `only_cations=True` skips expected neutral/anion sites.
- A coordination environment is missing despite near-neighbor rows existing.

Recovery:

- Restrict the problem with `only_indices`, `only_symbols`, `min_cn`, `max_cn`, and `timelimit`.
- Use `valences="undefined"` or explicit valences when bond-valence analysis is not reliable.
- Set `only_cations=False` when analyzing anions or neutral structures.
- Compare `SimplestChemenvStrategy` against `MultiWeightsChemenvStrategy.stats_article_weights_parameters()` when environment assignment is borderline.
- Treat maintainer-only Chemenv geometry-development utilities as excluded reference material; do not run or link them from runtime workflows.

## Magnetic Analyzer Problems

Symptoms:

- `CollinearMagneticStructureAnalyzer` reports `NM` or `Unknown` unexpectedly.
- It raises on disordered structures.
- It complains about both species spin and `magmom` site properties.
- Non-collinear moments trigger warnings or incomplete interpretation.

Recovery:

- Prefer `site_properties={"magmom": [...]}` for analyzer workflows.
- Avoid representing moments both as species spin and site properties unless the workflow explicitly requires it.
- For missing moments, choose an overwrite mode deliberately, such as `replace_all_if_undefined`.
- Make an ordered approximation before analyzing disordered structures.
- Tune `threshold`, `threshold_nonmag`, and `threshold_ordering` when tiny moments drive ordering labels.
- Explain that this analyzer is for collinear magnetism; do not use it as final non-collinear authority.

## Prototype and Symmetry Backend Failures

Symptoms:

- `method="aflow"` fails because the `aflow` executable is absent.
- `method="moyopy"` fails because `moyopy` is not installed.
- `method="spglib"` returns an explanation string or changes label with tolerance.
- A deprecated prototype matcher emits a warning.

Recovery:

- Start with `get_protostructure_label(structure, method="spglib", raise_errors=False)`.
- Record `init_symprec`, `fallback_symprec`, and any standardization/primitive-reduction choices.
- Use `raise_errors=False` for diagnostics so the returned string can explain invalid Wyckoff multiplicities or symmetry failures.
- Use `aflow` or `moyopy` only when the user already has the backend available or explicitly requests it.
- Prefer `PrototypeDatabaseMatcher` for new database-matching code.

## Functional Group and Molecule Matching Issues

Symptoms:

- Functional-group extraction errors mention OpenBabel.
- Molecule graph construction fails.
- Molecule matching thresholds differ from older examples.

Recovery:

- Treat OpenBabel bindings as optional; base installs may not include them.
- If OpenBabel is missing, ask for explicit bond connectivity or use molecule matching routes that do not require functional-group perception.
- Revalidate RMSD or tolerance thresholds when comparing against old molecule-matcher examples.
- Confirm molecule coordinates are Cartesian and in Angstrom-like units.

## Malformed Structures

Symptoms:

- `validate_proximity=True` raises during construction.
- Coordination numbers are unrealistic.
- Cartesian coordinates were passed as fractional coordinates or vice versa.
- Disordered occupancies are rejected downstream.

Recovery:

- Confirm whether coordinates are fractional or Cartesian before constructing the structure.
- Print composition, lattice lengths/angles, site count, first few sites, and `structure.is_ordered` before analysis.
- Use `coords_are_cartesian=True` when user coordinates are Cartesian.
- Convert units to Angstrom before local-environment or graph analysis.
- Make ordered approximations only when the user accepts the modeling choice.

## Units and Conventions

Pymatgen generally assumes Angstrom for lengths, degrees for lattice angles, eV for energies, and Bohr magnetons for magnetic moments unless a specific API says otherwise. Objects usually do not enforce units.

Recovery:

- Ask for input units when distances or lattices look implausible.
- Convert bohr, nm, or pm coordinates to Angstrom before constructing structures.
- Keep magnetic moments in Bohr magnetons for `magmom` site properties.
- Route thermodynamic/electrochemical unit issues to the owning entries or surfaces/electrochemistry sub-skill.

## Optional Extras and External Programs

Base install supports core structures, common local-environment routes, graphs, dimensionality, magnetism, and `spglib` prototype labels in the inspected baseline. Do not assume these unless confirmed:

- OpenBabel bindings for functional groups and broad molecule file support.
- `moyopy` for prototype labels.
- External `aflow` executable for AFLOW-backed prototype labels.
- Visualization, GUI, or long-running maintainer Chemenv utilities.

When optional support is missing, provide a fallback: use `spglib`, choose another neighbor strategy, request explicit bond connectivity, restrict Chemenv analysis, or limit the answer to portable structure/graph analysis.
