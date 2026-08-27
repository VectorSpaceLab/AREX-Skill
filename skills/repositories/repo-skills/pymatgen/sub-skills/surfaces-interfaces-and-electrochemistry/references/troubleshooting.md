# Troubleshooting

## Pourbaix Energies Are Raw Total Energies

Symptoms:

- The diagram runs but stable domains are unphysical.
- Unexpected solids dominate all pH/V conditions.
- The user says energies came directly from VASP, `ComputedEntry`, or an API without formation-energy conversion.

Cause:

- `PourbaixEntry` expects formation energies in the Pourbaix reference convention. It then adds water, pH, voltage, and concentration terms; raw total energies make those corrections meaningless.

Fix:

1. Pause interpretation and identify whether every solid and ion energy is a formation energy.
2. For DFT solids, prepare compatibility-corrected entries or a phase-diagram/formation-energy workflow before wrapping entries in `PourbaixEntry`.
3. For ions, confirm the energies are aligned to the same hydrogen/oxygen/water convention as the solids.
4. Record the reference convention with the final diagram or table so pH/V results remain traceable.

Use `../entries-thermodynamics-and-batteries/` for entry compatibility and formation-energy preparation.

## Pourbaix Composition Or Concentration Is Wrong

Symptoms:

- Changing `PourbaixEntry(..., concentration=...)` affects ions but not solids.
- Diagram construction complains that `comp_dict` lacks non-H/O elements.
- `get_decomposition_energy` raises a composition mismatch.

Causes:

- Solids are assigned concentration `1.0` internally.
- H and O are open species and are stripped from `comp_dict`.
- Decomposition energy is defined for entries matching the diagram's non-H/O target composition.

Fix:

1. Put only non-H/O elements in `comp_dict`, such as `{"Zn": 1.0}`.
2. Use `conc_dict={"Zn": 1e-6}` for element-level ion concentrations.
3. For multicomponent systems, set a target composition such as `{"Ag": 0.5, "Te": 0.5}`.
4. Before calling `get_decomposition_energy`, compare the entry's non-H/O fractional composition with the diagram composition.

## Invalid Or Incomplete Pourbaix Entries

Symptoms:

- Construction raises that supplied entries must be solid or ion entries.
- Aqueous species names or charges look wrong.
- Multicomponent diagrams are slow or produce unexpectedly few stable domains.

Causes:

- Solids or ions were not wrapped in `PourbaixEntry`, or multicomponent combinations require `MultiEntry` processing.
- Ion formulas lack charge information or were parsed incorrectly.
- Too many unrelated candidate entries create a large multi-entry search space.

Fix:

1. Wrap solids as `PourbaixEntry(ComputedEntry(...))` or `PourbaixEntry(ComputedStructureEntry(...))`.
2. Wrap ions as `PourbaixEntry(IonEntry(Ion.from_formula("Fe[+2]"), energy), concentration=...)`.
3. Start with physically relevant solids and ions, then broaden only after the focused set behaves.
4. Keep `filter_solids=True` for most production diagrams so unstable solids are filtered by a compositional phase diagram.
5. Use `nproc` only when multiprocessing is safe in the user's execution environment.

## Surface Energies Are Symbolic Or Inconsistent

Symptoms:

- `SlabEntry.surface_energy` returns a SymPy expression instead of a float.
- Equivalent facets have very different energies.
- Clean and adsorbed surfaces compare inconsistently.
- Surface energies are negative or wildly outside the expected scale.

Causes:

- Non-stoichiometric or adsorbed slabs require chemical-potential reservoirs.
- Slab, bulk, adsorbate, and reservoir entries were computed with inconsistent settings.
- A reservoir entry is missing or uses a mismatched reference state.
- Units are mixed, for example J/m² beside eV/Å².

Fix:

1. Confirm bulk and slab structures represent the same material and facet convention.
2. Confirm slab, bulk, adsorbate, and reservoir calculations share compatible DFT settings and corrections.
3. For an n-element bulk, provide n-1 reservoir entries when modeling chemical potentials.
4. Substitute all `delu_*` variables before numerical ranking.
5. Treat negative surface energies as a stop condition until references, stoichiometry, adsorption accounting, and units are rechecked.

## Wulff Shape Looks Unphysical

Symptoms:

- One facet dominates even though the input set seems balanced.
- The weighted surface energy is far outside the facet-energy range.
- Warnings mention negative surface energies.

Causes:

- `miller_list` and `e_surf_list` are misordered or have inconsistent units.
- Energies are raw slab excess energies rather than surface energies.
- Miller indices are not in the same conventional-cell basis as the lattice.

Fix:

1. Rebuild a table with columns for Miller index, energy value, unit, and provenance.
2. Check that the list order passed to `WulffShape` matches the table exactly.
3. Convert all energies to one unit before construction.
4. Use the same conventional-cell lattice convention used to label the Miller indices.

## Slab Terminations Or Surface Areas Look Wrong

Symptoms:

- Coherent interface terminations are missing or duplicated.
- Slab labels or surface areas do not match expected facets.
- Work-function slab regions are split incorrectly.

Causes:

- Miller indices are in a different lattice convention than the structure.
- `termination_ftol` or symmetry filtering merges distinct terminations or splits equivalent ones.
- Work-function layer detection depends on slab placement, `shift`, and `blength`.

Fix:

1. Standardize structures before comparing facets or interfaces.
2. For coherent interfaces, use `termination_ftol=(film_ftol, substrate_ftol)` when film and substrate need different grouping tolerances.
3. Set `filter_out_sym_slabs=False` when distinct termination combinations are filtered too aggressively.
4. For work functions, adjust `shift` and `blength`, then verify enough vacuum exists for a flat potential region.

## ZSL Or Substrate Matching Finds No Matches

Symptoms:

- `list(ZSLGenerator(...)(film_vectors, substrate_vectors))` is empty.
- `CoherentInterfaceBuilder.get_interfaces(...)` raises `No ZSL matches found`.
- Relaxing tolerances creates impractically large interface supercells.

Causes:

- Film/substrate Miller indices produce incompatible surface lattices.
- `max_area`, area-ratio, length, or angle tolerances are too strict.
- Input vectors are not the in-plane surface vectors or the bulk structures are not standardized.

Fix:

1. Confirm `film_vectors` and `substrate_vectors` are each the first two vectors of the intended surface slab lattice.
2. Start with simple low-index Miller pairs, then broaden the facet search.
3. Increase `max_area` gradually and relax `max_area_ratio_tol`, `max_length_tol`, and `max_angle_tol` in small steps.
4. Try `bidirectional=True` if match direction matters.
5. Reject matches that require impractically large supercells even if the algorithm returns them.

## Coherent Interface Builder Raises Transformation Errors

Symptoms:

- Errors mention changed film or substrate lattice vectors during ZSL matching.
- Errors mention a 2D transformation affecting the c-axis.
- Generated `Interface` structures have unexpected strain or atom counts.

Causes:

- ZSL tolerances admit transformations incompatible with integer supercell construction.
- Surface slabs were generated from structures/Miller indices that do not align with the expected in-plane basis.
- The chosen match is mathematically possible but physically impractical.

Fix:

1. Tighten ZSL tolerances or lower `max_area` to avoid pathological transformations.
2. Verify film and substrate structures are conventional/standardized and have sensible lattice metrics.
3. Inspect `builder.zsl_matches` before generating interfaces.
4. Generate only a few candidate interfaces first, then inspect lattice, strain, gap, vacuum, and atom counts.
5. Try a different Miller pair if transformation failures persist.

## Interfacial Reactivity Phase Diagram Is Incomplete

Symptoms:

- Kinks are missing or reactions look chemically impossible.
- The class warns that endpoint ground-state entries cannot be found.
- Passing a grand-potential diagram raises a type error.

Causes:

- The phase diagram does not span every element in both reactants.
- Entries were not compatibility-corrected or are sparse near the tie-line.
- A grand-potential analysis is being routed through the closed-system class.

Fix:

1. Build `PhaseDiagram(entries)` from entries covering the union of elements in both reactant compositions.
2. Add relevant competing phases near the interface tie-line.
3. Use `use_hull_energy=True` only if endpoint hull energies are scientifically acceptable.
4. Use `GrandPotentialInterfacialReactivity` when open species are part of the problem.

## Plotting Fails In Headless Environments

Symptoms:

- Matplotlib raises display or backend errors.
- Plotly is unavailable for `InterfacialReactivity.plot(backend="plotly")`.
- Calling `.show()` blocks or fails in a terminal session.

Fix:

1. Set `matplotlib.use("Agg", force=True)` before importing `pyplot` in scripts or CI.
2. Prefer returning figure objects or saving user-requested files rather than calling `.show()`.
3. Use `backend="matplotlib"` if Plotly is unavailable.
4. Keep smoke checks numerical/import-only unless the user explicitly asks for figure generation.

## Optional Dependencies And Baseline Install

The baseline install supports the public analysis imports in `api-reference.md`, but broad optional extras are not assumed. If a workflow needs Plotly, GUI visualization, external APIs, VASP output parsing, or optional packages, perform a guarded import/check and ask for installation or files before proceeding.
