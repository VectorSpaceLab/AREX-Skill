# Workflows: Structure and Local-Environment Analysis

These workflows are self-contained and use public pymatgen APIs. They avoid source-repo fixtures, network access, and maintainer scripts.

## 1. Build a Periodic Structure

```python
from pymatgen.core import Lattice, Structure

structure = Structure(
    Lattice.cubic(4.12),
    ["Cs+", "Cl-"],
    [[0, 0, 0], [0.5, 0.5, 0.5]],
)
print(structure.formula)
print(structure[0].species_string)
```

Checklist:

- Coordinates are fractional by default; pass `coords_are_cartesian=True` for Cartesian coordinates.
- Species strings such as `"Cs+"`, `"Cl-"`, and `"Fe2+"` add oxidation states and help cation/anion-aware workflows.
- Use `validate_proximity=True` when checking user-provided coordinates for unrealistically close sites.
- Keep lattice lengths in Angstrom and angles in degrees unless a specific parser/API says otherwise.

## 2. Build a Molecule

```python
from pymatgen.core import Molecule

methane = Molecule(
    ["C", "H", "H", "H", "H"],
    [
        [0.000000, 0.000000, 0.000000],
        [0.000000, 0.000000, 1.089000],
        [1.026719, 0.000000, -0.363000],
        [-0.513360, -0.889165, -0.363000],
        [-0.513360, 0.889165, -0.363000],
    ],
)
print(methane.composition.formula)
```

Use molecule workflows for non-periodic coordinates. If a user needs broad molecule file conversion or functional groups, first check optional OpenBabel availability.

## 3. Compare Neighbor Strategies

Start with `CrystalNN`, then compare a simpler distance rule and raw Voronoi contacts when a user reports a surprising coordination number.

```python
from pymatgen.analysis.local_env import CrystalNN, MinimumDistanceNN, VoronoiNN
from pymatgen.core import Lattice, Structure

structure = Structure(Lattice.cubic(4.12), ["Cs+", "Cl-"], [[0, 0, 0], [0.5, 0.5, 0.5]])
strategies = {
    "CrystalNN": CrystalNN(search_cutoff=6),
    "CrystalNN cation/anion": CrystalNN(cation_anion=True, search_cutoff=6),
    "MinimumDistanceNN": MinimumDistanceNN(cutoff=6),
    "VoronoiNN": VoronoiNN(cutoff=6),
}

site_index = 0
for label, strategy in strategies.items():
    info = strategy.get_nn_info(structure, site_index)
    print(label, "cn=", strategy.get_cn(structure, site_index), "rows=", len(info))
    for item in info:
        neighbor = item["site"]
        print(" ", neighbor.species_string, structure[site_index].distance(neighbor), item.get("image"), item.get("weight"))
```

Interpretation pattern:

1. State the exact strategy and parameters.
2. Print species, distance, periodic image, and weight.
3. Compare at least one alternative strategy.
4. Decide whether the final answer is a chemical coordination number, a distance-shell count, or a raw Voronoi contact list.

## 4. Build a Bonded Graph and Determine Dimensionality

`get_structure_components` and `get_dimensionality_larsen` require a bonded `StructureGraph`, not a bare `Structure`.

```python
from pymatgen.analysis.dimensionality import get_dimensionality_larsen, get_structure_components
from pymatgen.analysis.local_env import CrystalNN
from pymatgen.core import Lattice, Structure

structure = Structure(Lattice.cubic(4.12), ["Cs+", "Cl-"], [[0, 0, 0], [0.5, 0.5, 0.5]])
bonded = CrystalNN(search_cutoff=6).get_bonded_structure(structure)

print(type(bonded).__name__)
print(get_dimensionality_larsen(bonded))
for component in get_structure_components(bonded, inc_orientation=True, inc_site_ids=True):
    print(component["dimensionality"], component.get("orientation"), component.get("site_ids"))
```

When reporting dimensionality, include the neighbor strategy used to create the graph. Dimensionality changes caused by switching neighbor algorithms are model differences, not necessarily code errors.

## 5. Diagnose a CIF-Like Local Environment

```python
from pymatgen.analysis.local_env import CrystalNN, MinimumDistanceNN
from pymatgen.core import Structure

structure = Structure.from_file("input.cif")
if not structure.is_ordered:
    raise ValueError("Make an ordered approximation before local-environment analysis.")

site_index = 0
candidates = [
    ("CrystalNN", CrystalNN(search_cutoff=7)),
    ("CrystalNN cation/anion", CrystalNN(cation_anion=True, search_cutoff=7)),
    ("MinimumDistanceNN", MinimumDistanceNN(cutoff=10)),
]
for label, strategy in candidates:
    try:
        info = strategy.get_nn_info(structure, site_index)
    except Exception as exc:
        print(label, "failed:", type(exc).__name__, exc)
        continue
    print(label, "cn=", strategy.get_cn(structure, site_index))
    for item in info:
        neighbor = item["site"]
        print(neighbor.species_string, round(structure[site_index].distance(neighbor), 4), item.get("image"), item.get("weight"))
```

If `CrystalNN(cation_anion=True)` fails or gives no neighbors, add/check oxidation states only when chemically justified. Otherwise use a neutral strategy and explain uncertainty.

## 6. Use Chemenv for Named Coordination Environments

Use Chemenv when a user asks for geometry symbols, continuous symmetry measures, or a named coordination environment rather than just a coordination number.

```python
from pymatgen.analysis.chemenv.coordination_environments.chemenv_strategies import SimplestChemenvStrategy
from pymatgen.analysis.chemenv.coordination_environments.coordination_geometry_finder import LocalGeometryFinder
from pymatgen.analysis.chemenv.coordination_environments.structure_environments import LightStructureEnvironments
from pymatgen.core import Lattice, Structure

structure = Structure(Lattice.cubic(4.12), ["Cs+", "Cl-"], [[0, 0, 0], [0.5, 0.5, 0.5]])
lgf = LocalGeometryFinder()
lgf.setup_structure(structure)
structure_environments = lgf.compute_structure_environments(
    only_indices=[0],
    only_cations=True,
    max_cn=12,
    timelimit=20,
)
strategy = SimplestChemenvStrategy(distance_cutoff=1.4, angle_cutoff=0.3)
light = LightStructureEnvironments.from_structure_environments(strategy=strategy, structure_environments=structure_environments)
print(light.coordination_environments[0])
```

Chemenv guidance:

- Restrict `only_indices`, `only_symbols`, `min_cn`, `max_cn`, or `timelimit` for interactive diagnostics.
- `compute_coordination_environments(structure, indices=[...])` is a shorter route when only the final coordination environments are needed.
- Bond-valence valence detection can fail; pass explicit valences or use `valences="undefined"` when oxidation states are unknown.
- Exclude maintainer-only Chemenv development scripts; use public package APIs instead.

## 7. Analyze Collinear Magnetic Ordering

```python
from pymatgen.analysis.magnetism.analyzer import CollinearMagneticStructureAnalyzer
from pymatgen.core import Lattice, Structure

structure = Structure(
    Lattice.cubic(4.17),
    ["Ni", "Ni", "O", "O"],
    [[0, 0, 0], [0.5, 0.5, 0.5], [0.5, 0, 0], [0, 0.5, 0.5]],
    site_properties={"magmom": [5, -5, 0, 0]},
)

analyzer = CollinearMagneticStructureAnalyzer(structure, make_primitive=False)
print(analyzer.is_collinear)
print(analyzer.is_magnetic)
print(analyzer.ordering)
print(analyzer.magnetic_species_and_magmoms)
```

If moments are absent but known magnetic species are expected, choose an overwrite mode deliberately:

```python
analyzer = CollinearMagneticStructureAnalyzer(
    structure,
    overwrite_magmom_mode="replace_all_if_undefined",
    make_primitive=False,
)
```

Do not use this analyzer as final authority for non-collinear magnetism. Make an ordered approximation before analyzing disordered structures.

## 8. Label a Protostructure

```python
from pymatgen.analysis.prototypes import get_protostructure_label
from pymatgen.core import Lattice, Structure

structure = Structure(Lattice.cubic(4.0), ["Cs", "Cl"], [[0, 0, 0], [0.5, 0.5, 0.5]])
label = get_protostructure_label(structure, method="spglib", raise_errors=False)
print(label)
```

Backend choices:

- `method="spglib"`: preferred first route in base installs.
- `method="moyopy"`: only when `moyopy` is installed.
- `method="aflow"`: only when the external `aflow` executable is installed and the user explicitly wants that route.

If labels fail or change with tolerance, report `init_symprec`, `fallback_symprec`, whether the structure was reduced/standardized, and the returned explanation.

## 9. Match Two Structures and Diagnose Comparator Issues

```python
from pymatgen.analysis.structure_matcher import ElementComparator, SpeciesComparator, StructureMatcher
from pymatgen.core import Lattice, Structure

with_oxi = Structure(Lattice.cubic(4.12), ["Cs+", "Cl-"], [[0, 0, 0], [0.5, 0.5, 0.5]])
neutral = Structure(Lattice.cubic(4.12), ["Cs", "Cl"], [[0, 0, 0], [0.5, 0.5, 0.5]])

strict = StructureMatcher(comparator=SpeciesComparator())
by_element = StructureMatcher(comparator=ElementComparator())
print("species comparator:", strict.fit(with_oxi, neutral))
print("element comparator:", by_element.fit(with_oxi, neutral))
```

Diagnosis pattern:

1. Confirm oxidation-state representation and species strings in both structures.
2. Record comparator, `primitive_cell`, `scale`, `attempt_supercell`, `allow_subset`, `ignored_species`, and tolerances.
3. Use `ElementComparator` only when ignoring oxidation state is chemically intended.
4. Use `fit_anonymous` for prototype-like matching where species identity should be ignored.

## 10. Extract Functional Groups from a Molecule

```python
from pymatgen.analysis.functional_groups import FunctionalGroupExtractor
from pymatgen.core import Molecule

molecule = Molecule(["C", "O", "H", "H"], [[0, 0, 0], [1.2, 0, 0], [-0.6, 0.9, 0], [-0.6, -0.9, 0]])
extractor = FunctionalGroupExtractor(molecule)
print(extractor.get_heteroatoms())
print(extractor.get_all_functional_groups())
```

If OpenBabel is missing, do not force-install it. Ask for explicit bond connectivity, use molecule matching if sufficient, or explain that functional-group perception is unavailable in the current environment.

## 11. Serialize Structures and Analysis Inputs

```python
import json
from pymatgen.core import Structure

payload = structure.as_dict()
restored = Structure.from_dict(json.loads(json.dumps(payload)))
assert restored.composition == structure.composition
```

For nested pymatgen objects, use Monty JSON encoding:

```python
import json
from monty.json import MontyDecoder, MontyEncoder

json_text = json.dumps({"structure": structure}, cls=MontyEncoder)
restored = json.loads(json_text, cls=MontyDecoder)["structure"]
```

Prefer JSON/YAML dictionaries for handoff artifacts. Avoid pickle unless the user explicitly requests short-lived local Python-only serialization.

## 12. Run the Bundled Smoke Script

```bash
python scripts/structure_neighbor_smoke.py --help
python scripts/structure_neighbor_smoke.py
python scripts/structure_neighbor_smoke.py --strategy voronoi --json
python scripts/structure_neighbor_smoke.py --case matcher
```

Expected signal:

- The default case prints a CsCl structure, selected neighbor strategy, coordination number, neighbor rows, and component dimensionality.
- `--case compare` compares `CrystalNN`, `MinimumDistanceNN`, and `VoronoiNN` on the same tiny oxide-like structure.
- `--case matcher` demonstrates a species/oxidation-state comparator mismatch without reading files.
