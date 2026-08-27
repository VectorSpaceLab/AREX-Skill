# API Reference

This reference covers pymatgen surface, interface, Pourbaix, Wulff-shape, work-function, substrate-matching, coherent-interface, and interfacial-reactivity APIs. It assumes a baseline pymatgen install; optional visualization/network extras are conditional.

## Surface And Wulff APIs

| Task | Import | Constructor or call | Main outputs |
| --- | --- | --- | --- |
| Build a Wulff shape | `from pymatgen.analysis.wulff import WulffShape` | `WulffShape(lattice, miller_list, e_surf_list, symprec=1e-5)` | `area_fraction_dict`, `weighted_surface_energy`, `anisotropy`, `shape_factor`, `miller_area_dict`, `get_plot()`, `get_plotly()` |
| Represent one slab calculation | `from pymatgen.analysis.surface_analysis import SlabEntry` | `SlabEntry(structure, energy, miller_index, correction=0.0, parameters=None, data=None, entry_id=None, label=None, adsorbates=None, clean_entry=None, marker=None, color=None)` | `surface_energy(ucell_entry, ref_entries=None)`, `gibbs_binding_energy(eads=False)`, `surface_area`, `miller_index`, `label` |
| Compare slab surface energies | `from pymatgen.analysis.surface_analysis import SurfaceEnergyPlotter` | `SurfaceEnergyPlotter(all_slab_entries, ucell_entry, ref_entries=None)` | `get_stable_entry_at_u(...)`, `wulff_from_chempot(...)`, `stable_u_range_dict(...)`, surface-energy and chemical-potential plotting helpers |
| Analyze a work function | `from pymatgen.analysis.surface_analysis import WorkFunctionAnalyzer` | `WorkFunctionAnalyzer(structure, locpot_along_c, efermi, shift=0, blength=3.5)` or `WorkFunctionAnalyzer.from_files(poscar_filename, locpot_filename, outcar_filename, shift=0, blength=3.5)` | `work_function`, `vacuum_locpot`, `ave_bulk_p`, `is_converged(min_points_frac=0.015, tol=0.0025)`, `get_locpot_along_slab_plot(...)` |

### Surface Data Contracts

- `WulffShape` expects a conventional-cell `Lattice`, a `miller_list`, and a same-length `e_surf_list` in consistent units. Negative or mixed-unit surface energies can produce unphysical shapes even if object construction succeeds.
- `SlabEntry.surface_energy` uses the slab energy, bulk unit-cell entry, slab surface area, and optional reservoir entries. Stoichiometric clean slabs usually return a float; non-stoichiometric or adsorbed slabs can return a SymPy expression with symbols such as `delu_O`.
- `SurfaceEnergyPlotter` accepts either a list of `SlabEntry` objects or the nested mapping `{miller_index: {clean_slab_entry: [adsorbed_slab_entries]}}` used for clean/adsorbed surface comparisons.
- `WorkFunctionAnalyzer.from_files` reads VASP `POSCAR`, `LOCPOT`, and `OUTCAR`; use the direct constructor when the user already has an in-memory structure, local-potential profile, and Fermi energy.

## Interface Matching APIs

| Task | Import | Constructor or call | Main outputs |
| --- | --- | --- | --- |
| Match two 2D surface lattices | `from pymatgen.analysis.interfaces.zsl import ZSLGenerator` | `ZSLGenerator(max_area_ratio_tol=0.09, max_area=400, max_length_tol=0.03, max_angle_tol=0.01, bidirectional=False)` then `zsl(film_vectors, substrate_vectors, lowest=False)` | Iterator of `ZSLMatch` with `match_area`, superlattice vectors, film/substrate transformations, and `match_transformation` |
| Search film/substrate facets | `from pymatgen.analysis.interfaces.substrate_analyzer import SubstrateAnalyzer` | `SubstrateAnalyzer(film_max_miller=1, substrate_max_miller=1, **zsl_kwargs)` then `calculate(film, substrate, elasticity_tensor=None, film_millers=None, substrate_millers=None, ground_state_energy=0, lowest=False)` | Iterator of `SubstrateMatch`; strain-energy fields appear when elasticity data is supplied |
| Build coherent interfaces | `from pymatgen.analysis.interfaces.coherent_interfaces import CoherentInterfaceBuilder` | `CoherentInterfaceBuilder(substrate_structure, film_structure, film_miller, substrate_miller, zslgen=None, termination_ftol=0.25, label_index=False, filter_out_sym_slabs=True)` | `terminations`, `zsl_matches`, `get_interfaces(termination, gap=2.0, vacuum_over_film=20.0, film_thickness=1, substrate_thickness=1, in_layers=True)` |

### Interface Data Contracts

- ZSL inputs are the two in-plane surface lattice vectors for film and substrate. Pass the first two vectors of an intended slab lattice, not full bulk lattice matrices unless they already define the surface plane.
- `SubstrateAnalyzer.calculate` can generate symmetrically distinct Miller indices up to configured maxima; explicit `film_millers` and `substrate_millers` are safer for focused or expensive searches.
- `CoherentInterfaceBuilder` constructs low-thickness slabs internally with `reorient_lattice=False` and uses a bidirectional `ZSLGenerator` by default when no custom generator is supplied.
- `termination_ftol` may be a single float or `(film_ftol, substrate_ftol)` to tune termination grouping separately for film and substrate.

## Pourbaix APIs

| Task | Import | Constructor or call | Main outputs |
| --- | --- | --- | --- |
| Wrap solid or ion entries | `from pymatgen.analysis.pourbaix_diagram import PourbaixEntry` | `PourbaixEntry(entry, entry_id=None, concentration=1e-6)` | `phase_type`, `name`, `energy`, `energy_at_conditions(pH, V)`, `normalized_energy_at_conditions(pH, V)`, `npH`, `nPhi`, `nH2O` |
| Represent aqueous ions | `from pymatgen.analysis.pourbaix_diagram import IonEntry` and `from pymatgen.core.ion import Ion` | `IonEntry(Ion.from_formula("Zn[+2]"), energy)` then `PourbaixEntry(ion_entry, concentration=1e-6)` | Charge-aware ion entry with concentration-dependent energy term |
| Build a Pourbaix diagram | `from pymatgen.analysis.pourbaix_diagram import PourbaixDiagram` | `PourbaixDiagram(entries, comp_dict=None, conc_dict=None, filter_solids=True, nproc=None)` | `stable_entries`, `unstable_entries`, `all_entries`, `find_stable_entry(pH, V)`, `get_stable_entry(pH, V)`, `get_decomposition_energy(entry, pH, V)`, `get_hull_energy(pH, V)` |
| Plot domains | `from pymatgen.analysis.pourbaix_diagram import PourbaixPlotter` | `PourbaixPlotter(pourbaix_diagram)` | `get_pourbaix_plot(...)`, `plot_entry_stability(...)`, `domain_vertices(entry)` |

### Pourbaix Data Contracts

- `PourbaixEntry` input energies should be formation energies with respect to the hydrogen/oxygen gas convention required by the Pourbaix formalism; raw total energies produce scientifically wrong domains.
- Solids get `concentration=1.0` internally. Ion concentrations come from `PourbaixEntry(..., concentration=...)` or `PourbaixDiagram(..., conc_dict={...})`.
- `PourbaixDiagram` treats H and O as open species and strips them from `comp_dict`; include at least one non-H/O element in the target composition.
- With `filter_solids=True`, solids are filtered through a compositional phase diagram before Pourbaix domains are computed. Use `filter_solids=False` only for deliberate metastable or diagnostic studies.

## Interfacial Reactivity APIs

| Task | Import | Constructor or call | Main outputs |
| --- | --- | --- | --- |
| Closed-system reaction kinks | `from pymatgen.analysis.interface_reactions import InterfacialReactivity` | `InterfacialReactivity(c1, c2, pd, norm=True, use_hull_energy=False, **kwargs)` | `get_kinks()`, `get_dataframe()`, `minimum`, `products`, `labels`, `plot(backend="plotly" | "matplotlib")` |
| Open-element reaction kinks | `from pymatgen.analysis.interface_reactions import GrandPotentialInterfacialReactivity` | `GrandPotentialInterfacialReactivity(c1, c2, grand_pd, pd_non_grand, include_no_mixing_energy=False, norm=True, use_hull_energy=False, **kwargs)` | Grand-potential analogue of kink, products, dataframe, and plotting workflows |

### Interfacial Reactivity Data Contracts

- `InterfacialReactivity` requires a `PhaseDiagram` spanning every element in both reactant compositions.
- Use `GrandPotentialInterfacialReactivity` for open-element grand-potential analyses; the closed-system class raises when passed a grand-potential phase diagram unless an internal bypass flag is used.
- `get_kinks()` returns tuples of `(index, mixing_ratio, reaction_energy_eV_per_atom, reaction, reaction_energy_kJ_per_mol_formula)`.
- `use_hull_energy=False` uses exact ground-state entry energies when present; if exact compositions are absent, pymatgen falls back to hull energies with a warning.

## Cross-Sub-Skill Prerequisites

- Use `../entries-thermodynamics-and-batteries/` before Pourbaix or interface-reactivity workflows that need compatibility-corrected entries, formation energies, or phase diagrams.
- Use `../structures-local-environments-and-transformations/` before workflows that need structure construction, standardization, oxidation-state assignment, slab generation, or geometry validation.
- Use `../external-data-access/` before live data retrieval and never place credentials in reusable scripts, notebooks, figures, or logs.
