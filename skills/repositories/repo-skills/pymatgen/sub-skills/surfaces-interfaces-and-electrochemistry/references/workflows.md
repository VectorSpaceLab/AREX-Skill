# Workflows

These recipes assume installed pymatgen APIs and user-supplied structures, entries, or calculation outputs. They avoid source-repository paths and keep plotting optional.

## Wulff Shape From Facet Energies

Use when the user already has surface energies for a set of Miller facets.

```python
from pymatgen.analysis.wulff import WulffShape
from pymatgen.core import Lattice

lattice = Lattice.cubic(3.6)  # conventional unit-cell lattice
miller_list = [(1, 0, 0), (1, 1, 0), (1, 1, 1)]
surface_energies = [1.25, 1.45, 1.05]  # same unit and order as miller_list
wulff = WulffShape(lattice, miller_list, surface_energies)
print(wulff.area_fraction_dict)
print(wulff.weighted_surface_energy)
```

Checklist:

1. Use a conventional-cell lattice and Miller indices in the same convention.
2. Keep `miller_list` and `surface_energies` the same length and order.
3. Confirm the energy unit, commonly J/m² or eV/Å², is consistent across all facets.
4. Treat negative energies or a dominant unexpected facet as evidence of reference/units problems before interpreting shape metrics.

## Slab Surface Energy With `SlabEntry`

Use when the user has slab structures, slab energies, and a bulk reference entry.

```python
from pymatgen.analysis.surface_analysis import SlabEntry, SurfaceEnergyPlotter
from pymatgen.entries.computed_entries import ComputedStructureEntry

bulk_entry = ComputedStructureEntry(bulk_structure, bulk_energy)
slab_entries = [
    SlabEntry(slab_100, slab_100_energy, (1, 0, 0), label="clean"),
    SlabEntry(slab_111, slab_111_energy, (1, 1, 1), label="clean"),
]
for slab_entry in slab_entries:
    gamma = slab_entry.surface_energy(bulk_entry)
    print(slab_entry.miller_index, gamma)

plotter = SurfaceEnergyPlotter(slab_entries, bulk_entry)
wulff = plotter.wulff_from_chempot()
print(wulff.area_fraction_dict)
```

For non-stoichiometric slabs or adsorbates, substitute all chemical-potential variables before numerical ranking:

```python
from sympy import Symbol

reservoir_entries = [oxygen_reference_entry]
surface_energy_expr = slab_entry.surface_energy(bulk_entry, ref_entries=reservoir_entries)
gamma_at_mu = surface_energy_expr.subs({Symbol("delu_O"): -1.0})
```

Checklist:

1. Use compatible `ComputedStructureEntry` or `ComputedEntry` objects for bulk, slab, adsorbate, and reservoir energies.
2. Match calculation settings, cell conventions, reference states, and units across all energies.
3. Provide enough reservoir entries for non-stoichiometric systems; for an n-element bulk, the method expects n-1 elemental reservoirs.
4. If `surface_energy` returns a SymPy expression, substitute every `delu_*` symbol before comparing surfaces.

## Work-Function Analysis

Use direct construction when the user has an in-memory local-potential profile, or `from_files` when VASP outputs are present.

```python
from pymatgen.analysis.surface_analysis import WorkFunctionAnalyzer

analyzer = WorkFunctionAnalyzer(
    structure=slab_structure,
    locpot_along_c=list(local_potential_values),
    efermi=fermi_energy,
    shift=0,
    blength=3.5,
)
print(analyzer.work_function)
print(analyzer.vacuum_locpot)
print(analyzer.is_converged())
```

For VASP files:

```python
analyzer = WorkFunctionAnalyzer.from_files("POSCAR", "LOCPOT", "OUTCAR")
```

Checklist:

1. Confirm the slab has enough vacuum for a flat maximum in `locpot_along_c`.
2. Tune `shift` when the slab crosses the periodic boundary.
3. Tune `blength` when slab regions are split or merged incorrectly.
4. Treat `is_converged()` as a local-potential flatness diagnostic, not a complete convergence proof.

## ZSL Lattice Matching

Use when the user has two surface lattices and wants superlattice matches.

```python
from pymatgen.analysis.interfaces.zsl import ZSLGenerator

zsl = ZSLGenerator(max_area=200, max_length_tol=0.03, max_angle_tol=0.01)
film_vectors = film_slab.lattice.matrix[:2]
substrate_vectors = substrate_slab.lattice.matrix[:2]
matches = list(zsl(film_vectors, substrate_vectors, lowest=False))
for match in matches[:5]:
    print(match.match_area, match.film_transformation, match.substrate_transformation)
```

Checklist:

1. Pass only the two in-plane vectors for each surface.
2. Start with focused Miller indices before increasing `max_area` or relaxing tolerances.
3. Use `lowest=True` when the user wants only the first/smallest accepted match.
4. Try `bidirectional=True` when swapping film/substrate changes the match set in an unexpected way.

## Substrate Search

Use `SubstrateAnalyzer` when screening film/substrate facet combinations.

```python
from pymatgen.analysis.interfaces.substrate_analyzer import SubstrateAnalyzer

analyzer = SubstrateAnalyzer(
    film_max_miller=1,
    substrate_max_miller=1,
    max_area=200,
    max_length_tol=0.03,
    max_angle_tol=0.01,
)
matches = list(analyzer.calculate(
    film=film_conventional_structure,
    substrate=substrate_conventional_structure,
    film_millers=[(1, 0, 0)],
    substrate_millers=[(1, 0, 0), (1, 1, 1)],
    lowest=True,
))
for match in matches:
    print(match.film_miller, match.substrate_miller, match.match_area)
```

Checklist:

1. Prefer conventional standard structures for both film and substrate.
2. Restrict `film_millers` and `substrate_millers` for early debugging, then broaden.
3. Supply an elasticity tensor and `ground_state_energy` only when strain-energy ranking is required and the tensor is in the expected orientation.
4. If no matches appear, inspect lattice conventions and relax `max_area_ratio_tol`, `max_length_tol`, `max_angle_tol`, and `max_area` gradually.

## Coherent Interface Construction

Use after choosing film/substrate structures and Miller indices.

```python
from pymatgen.analysis.interfaces.coherent_interfaces import CoherentInterfaceBuilder
from pymatgen.analysis.interfaces.zsl import ZSLGenerator

zsl = ZSLGenerator(max_area=200, max_length_tol=0.05, max_angle_tol=0.03, bidirectional=True)
builder = CoherentInterfaceBuilder(
    substrate_structure=substrate_structure,
    film_structure=film_structure,
    film_miller=(1, 0, 0),
    substrate_miller=(1, 0, 0),
    zslgen=zsl,
    termination_ftol=(0.25, 0.25),
    filter_out_sym_slabs=True,
)
print(builder.terminations)
print(len(builder.zsl_matches))
termination = builder.terminations[0]
interfaces = list(builder.get_interfaces(
    termination=termination,
    gap=2.0,
    vacuum_over_film=20.0,
    film_thickness=2,
    substrate_thickness=3,
    in_layers=True,
))
print(len(interfaces), interfaces[0].formula)
```

Checklist:

1. Confirm `builder.zsl_matches` is non-empty before generating many interface structures.
2. Use `termination_ftol=(film_ftol, substrate_ftol)` if film and substrate terminations need different grouping tolerances.
3. Set `filter_out_sym_slabs=False` when distinct termination combinations disappear unexpectedly.
4. Inspect returned `Interface` objects for atom counts, strain, gap, vacuum, and supercell size before launching expensive calculations.

## Pourbaix Diagram Construction

Use when the user has solid and ion formation energies in a consistent Pourbaix convention.

```python
from pymatgen.analysis.pourbaix_diagram import IonEntry, PourbaixDiagram, PourbaixEntry
from pymatgen.core.ion import Ion
from pymatgen.entries.computed_entries import ComputedEntry

solid_entries = [
    PourbaixEntry(ComputedEntry("Zn", 0.0), entry_id="Zn(s)"),
    PourbaixEntry(ComputedEntry("ZnO", formation_energy_zno), entry_id="ZnO(s)"),
]
ion_entries = [
    PourbaixEntry(IonEntry(Ion.from_formula("Zn[+2]"), ion_formation_energy), concentration=1e-6),
]
pbx = PourbaixDiagram(
    solid_entries + ion_entries,
    comp_dict={"Zn": 1.0},
    conc_dict={"Zn": 1e-6},
    filter_solids=True,
)
print([entry.name for entry in pbx.stable_entries])
print(pbx.get_stable_entry(pH=7, V=0).name)
```

Checklist:

1. Stop and ask for formation energies if the user provides raw total energies.
2. Include enough competing solids and ions to define meaningful domains.
3. Keep `comp_dict` to non-H/O elements; H and O are open species.
4. Use `conc_dict` for element-level ion concentration; solids ignore user concentration and use `1.0` internally.
5. Use `get_decomposition_energy(entry, pH, V)` only when the entry matches the diagram composition.

## Interfacial Reactivity

Use when the user has a compositional phase diagram and wants reaction kinks between two solid reactants.

```python
from pymatgen.analysis.interface_reactions import InterfacialReactivity
from pymatgen.analysis.phase_diagram import PhaseDiagram
from pymatgen.core import Composition

pd = PhaseDiagram(entries)  # entries span all elements in both reactants
reactivity = InterfacialReactivity(
    Composition("LiCoO2"),
    Composition("Li3PS4"),
    pd,
    norm=True,
    use_hull_energy=False,
)
for index, ratio, energy_eV_atom, reaction, energy_kJ_mol in reactivity.get_kinks():
    print(index, ratio, energy_eV_atom, reaction)
print(reactivity.minimum)
```

Checklist:

1. Build the phase diagram from entries covering the union of elements in `c1` and `c2`.
2. Use compatibility-prepared entries when the phase diagram combines DFT data sources.
3. Use `use_hull_energy=True` when exact ground-state entries are absent and hull endpoints are scientifically acceptable.
4. Use `GrandPotentialInterfacialReactivity` for open-element analyses.

## Headless Plotting Pattern

Use this before any Matplotlib-backed Wulff, Pourbaix, surface-energy, work-function, or interface-reactivity plot in a terminal or CI-like environment.

```python
import matplotlib
matplotlib.use("Agg", force=True)

plot = wulff.get_plot()
plot.savefig("wulff.png", dpi=200)
```

Do not call `.show()` from noninteractive scripts. Prefer returning the plot object or saving a user-requested output file.
