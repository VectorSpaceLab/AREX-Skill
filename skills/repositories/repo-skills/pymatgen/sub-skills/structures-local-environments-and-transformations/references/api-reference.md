# API Reference: Structures, Local Environments, Graphs, and Transformations

This reference targets `pymatgen==2026.5.4`, `pymatgen-core==2026.5.18`, Python `>=3.11`, and a base install unless an optional backend is explicitly named.

## Core Object Patterns

Use these public imports for construction prerequisites:

```python
from pymatgen.core import Lattice, Molecule, Structure
```

| Object | Inspected signature | Use | Notes |
| --- | --- | --- | --- |
| `Lattice` | `Lattice(matrix, pbc=(True, True, True))` | Periodic cell. | Convenience constructors include `Lattice.cubic(...)` and `Lattice.from_parameters(...)`. Lengths are normally Angstrom and angles degrees. |
| `Structure` | `Structure(lattice, species, coords, charge=None, validate_proximity=False, to_unit_cell=False, coords_are_cartesian=False, site_properties=None, labels=None, properties=None)` | Mutable periodic crystal structure. | Coordinates are fractional unless `coords_are_cartesian=True`. Species strings may include oxidation states such as `"Fe2+"`. |
| `Molecule` | `Molecule(species, coords, charge=0.0, spin_multiplicity=None, validate_proximity=False, site_properties=None, labels=None, charge_spin_check=True, properties=None)` | Mutable non-periodic molecule. | Coordinates are Cartesian. Use immutable variants only when a workflow needs hashable/persistent objects. |

Common public patterns:

- `Structure.from_file(...)` and `Molecule.from_file(...)` read user-supplied files when the format is supported by the installed package stack.
- `.to(filename=...)`, `.as_dict()`, and `Class.from_dict(...)` are preferred for durable persistence; avoid pickle for long-lived materials data.
- `Structure` and `Molecule` are mutable: index assignment, adding/removing sites, translating sites, supercell generation, and oxidation-state decoration can change the object in place.

## Namespace Split with `pymatgen-core`

Several familiar `pymatgen.analysis.*` modules are compatibility stubs over `pymatgen-core` implementations:

| Public import route | Observed behavior | Practical guidance |
| --- | --- | --- |
| `pymatgen.analysis.local_env` | Re-exports `pymatgen.core.local_env`. | `CrystalNN.__module__` may show `pymatgen.core.local_env`; old analysis imports still work. |
| `pymatgen.analysis.graphs` | Re-exports `pymatgen.core.graphs`. | Use `from pymatgen.analysis.graphs import StructureGraph` in analysis examples; implementation module may show core. |
| `pymatgen.analysis.structure_matcher` | Re-exports `pymatgen.core.structure_matcher`. | `StructureMatcher` remains available through the analysis namespace. |
| `pymatgen.analysis.molecule_matcher` | Re-exports core molecule matcher. | Use for exact molecule matching without depending on atom order. |
| `pymatgen.analysis.molecule_structure_comparator` | Re-exports core molecule-structure comparator. | Use for rough paired-order molecule comparisons. |

Do not use old root imports such as `from pymatgen import Structure`; use `pymatgen.core` or the specific public submodule.

## Neighbor Strategies

Recommended import:

```python
from pymatgen.analysis.local_env import CrystalNN, MinimumDistanceNN, VoronoiNN
```

| Class | Inspected signature | Use when | Watch for |
| --- | --- | --- | --- |
| `CrystalNN` | `CrystalNN(weighted_cn=False, cation_anion=False, distance_cutoffs=(0.5, 1), x_diff_weight=3.0, porous_adjustment=True, search_cutoff=7, fingerprint_length=None)` | General coordination analysis in crystals. | Oxidation states matter with `cation_anion=True`; distance/electronegativity heuristics can include/exclude borderline contacts. |
| `VoronoiNN` | `VoronoiNN(tol=0, targets=None, cutoff=13.0, allow_pathological=False, weight='solid_angle', extra_nn_info=True, compute_adj_neighbors=True)` | Raw Voronoi topology, solid-angle weights, and diagnostic neighbor metadata. | Raw contacts are not always chemical bonds; periodic-image contacts can look surprising. |
| `MinimumDistanceNN` | `MinimumDistanceNN(tol=0.1, cutoff=10, get_all_sites=False)` | Deterministic nearest-distance shell and simple sanity checks. | Sensitive to the shortest distance shell; may miss chemically meaningful longer bonds. |
| `JmolNN` | `JmolNN(tol=0.45, min_bond_distance=0.4, el_radius_updates=None)` | Radius-table covalent heuristic or simple graph construction. | Tolerance and radius assumptions are not universal. |
| `OpenBabelNN` | `OpenBabelNN(order=True)` | Molecule bond perception for workflows such as functional groups. | Requires OpenBabel Python bindings; do not assume in a base install. |

Common methods:

- `strategy.get_nn_info(structure, site_index)` returns neighbor dictionaries with a neighboring `site`, weights, and often periodic image information.
- `strategy.get_cn(structure, site_index)` returns that strategy's coordination number.
- `strategy.get_bonded_structure(structure)` returns a `StructureGraph` suitable for graph and dimensionality analysis.

## Structure and Molecule Graphs

Recommended import:

```python
from pymatgen.analysis.graphs import MoleculeGraph, StructureGraph
```

| Object | Inspected signature | Use | Notes |
| --- | --- | --- | --- |
| `StructureGraph` | `StructureGraph(structure, graph_data=None)` | Periodic graph over a `Structure`. | Usually create with `CrystalNN().get_bonded_structure(structure)` or `StructureGraph.with_local_env_strategy(...)`. |
| `MoleculeGraph` | `MoleculeGraph(molecule, graph_data=None)` | Graph over a `Molecule`. | Often created from a molecule plus an `OpenBabelNN` or explicit connectivity. |

Useful `StructureGraph` methods listed by the public docs include `get_connected_sites`, `get_coordination_of_site`, `get_subgraphs_as_molecules`, `diff`, `with_empty_graph`, `with_edges`, and `with_local_env_strategy`. Keep periodic image vectors when interpreting edges.

## Structure Matching

Recommended import:

```python
from pymatgen.analysis.structure_matcher import ElementComparator, SpeciesComparator, StructureMatcher
```

| Object | Inspected signature / behavior | Use |
| --- | --- | --- |
| `StructureMatcher` | `StructureMatcher(ltol=0.2, stol=0.3, angle_tol=5, primitive_cell=True, scale=True, attempt_supercell=False, allow_subset=False, comparator=None, supercell_size='num_sites', ignored_species=())` | Compare structures under lattice/site tolerances, primitive reduction, optional scaling, and comparator rules. |
| `SpeciesComparator` | `SpeciesComparator()` | Default strict species comparator; oxidation states can matter. |
| `ElementComparator` | `ElementComparator()` | Compare by element identity, ignoring oxidation state. |
| `FrameworkComparator` | `FrameworkComparator()` | Compare framework topology more loosely. |
| `OrderDisorderElementComparator` | `OrderDisorderElementComparator()` | Compare ordered/disordered variants by element where appropriate. |

Useful methods include `fit`, `fit_anonymous`, `get_mapping`, `get_rms_dist`, `get_transformation`, `group_structures`, and `get_s2_like_s1`. If a match fails, record comparator, oxidation-state representation, primitive/scaling choices, and tolerances before changing chemistry.

## Dimensionality

Recommended import:

```python
from pymatgen.analysis.dimensionality import get_dimensionality_larsen, get_structure_components
```

| Function | Inspected signature | Input | Output/use |
| --- | --- | --- | --- |
| `get_dimensionality_larsen` | `get_dimensionality_larsen(bonded_structure)` | Bonded `StructureGraph`. | Integer highest dimensionality of bonded components. |
| `get_structure_components` | `get_structure_components(bonded_structure, inc_orientation=False, inc_site_ids=False, inc_molecule_graph=False)` | Bonded `StructureGraph`. | Component dictionaries with `dimensionality` and `structure_graph`; optional orientation, site ids, molecule graph. |
| `calculate_dimensionality_of_site` | `calculate_dimensionality_of_site(bonded_structure, site_index, inc_vertices=False)` | Bonded `StructureGraph` plus site index. | Dimensionality for one connected component. |
| `get_dimensionality_cheon` | `get_dimensionality_cheon(structure_raw, tolerance=0.45, ldict=None, standardize=True, larger_cell=False)` | Bare `Structure`. | String-like dimensionality labels; may need larger cells or bond overrides. |
| `get_dimensionality_gorai` | `get_dimensionality_gorai(structure, max_hkl=2, el_radius_updates=None, min_slab_size=5, min_vacuum_size=5, standardize=True, bonds=None)` | Bare `Structure`. | Integer dimensionality using slab/vacuum criteria and optional bond rules. |

Default route: construct a bonded graph with an explicitly named neighbor strategy, then call `get_structure_components(..., inc_orientation=True, inc_site_ids=True)` or `get_dimensionality_larsen(...)`.

## Chemenv Public Routes

Chemenv analyzes coordination environments using detailed Voronoi containers and continuous symmetry measures.

Recommended imports:

```python
from pymatgen.analysis.chemenv.coordination_environments.coordination_geometry_finder import LocalGeometryFinder
from pymatgen.analysis.chemenv.coordination_environments.chemenv_strategies import MultiWeightsChemenvStrategy, SimplestChemenvStrategy
from pymatgen.analysis.chemenv.coordination_environments.structure_environments import LightStructureEnvironments
```

| Object/method | Inspected signature | Use | Notes |
| --- | --- | --- | --- |
| `LocalGeometryFinder` | `LocalGeometryFinder(permutations_safe_override=False, plane_ordering_override=True, plane_safe_permutations=False, only_symbols=None)` | Main Chemenv entry point. | Broad searches can become expensive; restrict indices/symbols when possible. |
| `LocalGeometryFinder.setup_structure` | `setup_structure(structure)` | Attach a structure to the finder. | Setup may refine/symmetrize depending on parameters. |
| `compute_structure_environments` | `compute_structure_environments(..., only_cations=True, only_indices=None, maximum_distance_factor=2.0, minimum_angle_factor=0.05, max_cn=None, min_cn=None, valences='undefined', timelimit=None, ...)` | Compute full `StructureEnvironments`. | Use `only_indices`, `only_symbols`, `max_cn`, and `timelimit` for bounded diagnostics. |
| `compute_coordination_environments` | `compute_coordination_environments(structure, indices=None, only_cations=True, strategy=DEFAULT_STRATEGY, valences='bond-valence-analysis', initial_structure_environments=None)` | Directly get site coordination environments. | Bond-valence valence detection can fall back to `undefined`. |
| `SimplestChemenvStrategy` | `SimplestChemenvStrategy(structure_environments=None, distance_cutoff=1.4, angle_cutoff=0.3, additional_condition=1, continuous_symmetry_measure_cutoff=10, symmetry_measure_type='csm_wcs_ctwcc')` | Deterministic fixed distance/angle strategy. | Good for concise examples and reproducible diagnostics. |
| `MultiWeightsChemenvStrategy` | `MultiWeightsChemenvStrategy(..., ce_estimator={'function': 'power2_inverse_power2_decreasing', 'options': {'max_csm': 8.0}})` | More nuanced production Chemenv strategy. | `stats_article_weights_parameters()` supplies common defaults. |
| `LightStructureEnvironments.from_structure_environments` | `from_structure_environments(strategy, structure_environments, valences=None, valences_origin=None)` | Compact environment summary from computed environments. | Stores environments, neighbor sets, valences, and statistics. |

Prefer Chemenv when the user asks for named coordination environments and continuous symmetry measures, not just neighbor counts.

## Magnetism

Recommended import:

```python
from pymatgen.analysis.magnetism.analyzer import CollinearMagneticStructureAnalyzer, Ordering
```

| Object | Inspected signature / values | Use |
| --- | --- | --- |
| `CollinearMagneticStructureAnalyzer` | `CollinearMagneticStructureAnalyzer(structure, overwrite_magmom_mode='none', round_magmoms=False, detect_valences=False, make_primitive=True, default_magmoms=None, set_net_positive=True, threshold=0, threshold_nonmag=0.1, threshold_ordering=1e-08)` | Analyze collinear magnetic moments from `site_properties['magmom']` or species spin. |
| `Ordering` | `FM`, `AFM`, `FiM`, `NM`, `Unknown` | Report ordering classification. |
| overwrite modes | `none`, `respect_sign`, `respect_zeros`, `replace_all`, `replace_all_if_undefined`, `normalize` | Control how missing/existing magmoms are replaced or normalized. |

Useful properties/methods include `is_magnetic`, `is_collinear`, `ordering`, `magmoms`, `magnetic_species_and_magmoms`, `types_of_magnetic_species`, `number_of_magnetic_sites`, `number_of_unique_magnetic_sites()`, `get_structure_with_spin()`, `get_nonmagnetic_structure(...)`, `get_ferromagnetic_structure(...)`, `get_exchange_group_info(...)`, and `matches_ordering(...)`.

## Prototypes

Recommended imports:

```python
from pymatgen.analysis.prototypes import get_protostructure_label
from pymatgen.analysis.prototypes.matcher import PrototypeDatabaseMatcher
```

| Object | Inspected signature | Use | Backend notes |
| --- | --- | --- | --- |
| `get_protostructure_label` | `get_protostructure_label(struct, method, raise_errors=False, **kwargs)` | Return an AFLOW-style label plus chemical system, or an explanation string when `raise_errors=False`. | `method` is `"spglib"`, `"moyopy"`, or `"aflow"`; use `spglib` first in base installs. |
| `get_protostructure_label_from_spglib` | `get_protostructure_label_from_spglib(struct, raise_errors=False, init_symprec=0.1, fallback_symprec=1e-05)` | Direct spglib route with fallback tolerance. | Good diagnostic path when labels are tolerance-sensitive. |
| `PrototypeDatabaseMatcher` | `PrototypeDatabaseMatcher(prototype_db, initial_ltol=0.2, initial_stol=0.3, initial_angle_tol=5)` | Match structures to prototype databases with anonymous structure matching. | Needs a DataFrame-like database and subclass/static methods for row extraction. |

`method="aflow"` requires an external `aflow` executable; `method="moyopy"` requires `moyopy`. Do not install or download these automatically.

## Molecules, Matching, and Functional Groups

Recommended imports:

```python
from pymatgen.analysis.functional_groups import FunctionalGroupExtractor
from pymatgen.analysis.molecule_matcher import MoleculeMatcher
from pymatgen.analysis.molecule_structure_comparator import MoleculeStructureComparator
```

| Route | Use | Caveats |
| --- | --- | --- |
| `MoleculeMatcher` | Match molecules without requiring identical atom order. | Implementation is compatibility-backed by `pymatgen-core`; old RMSD thresholds may need revalidation. |
| `MoleculeStructureComparator` | Rough molecule comparison when atom order is already paired. | Good for paired input diagnostics, not general graph isomorphism. |
| `FunctionalGroupExtractor(molecule, optimize=False)` | Identify heteroatoms, special carbons, linked marked atoms, and functional groups. | Accepts a filename, `Molecule`, or `MoleculeGraph`; OpenBabel-backed perception may be required. |

## Safe Transformation-Adjacent Patterns

This sub-skill does not enumerate all `pymatgen.transformations` classes. Mention transformations only as preparation for the analyses above:

- Add oxidation states before cation/anion-sensitive neighbor analysis when chemically justified.
- Make an ordered approximation before magnetic analysis if the input structure is disordered.
- Decide whether primitive reduction, standardization, or supercells should happen before matching, dimensionality, or prototype labeling.
- State whether results refer to the original structure or a transformed copy.
