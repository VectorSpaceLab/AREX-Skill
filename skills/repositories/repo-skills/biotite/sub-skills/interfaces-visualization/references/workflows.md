# Interfaces and Visualization Workflows

These workflows are self-contained patterns for future agents. They intentionally avoid network fetches, GUI launch, and display-heavy side effects unless the caller explicitly requests them.

## Diagnose optional interface availability

1. Run `scripts/check_optional_interfaces.py` from this sub-skill.
2. Treat `available=false` for `rdkit`, `openmm`, `pymol`, or `matplotlib` as a route to install/skip guidance, not as a Biotite core failure.
3. If PyMOL is unavailable or a GUI is not available, choose a Matplotlib or file-export alternative where possible.
4. If ffmpeg/ImageMagick are unavailable, avoid `pymol_interface.play()` and prefer still images or caller-managed video export.

## Prepare an AtomArray for export

1. Load files via `../file-io-formats/` or construct/filter atoms via `../structure-analysis/`.
2. Confirm `atoms.coord` is a finite NumPy array with shape `(n, 3)` for `AtomArray` or `(m, n, 3)` for `AtomArrayStack`.
3. Confirm required annotations such as `chain_id`, `res_id`, `ins_code`, `res_name`, `hetero`, `atom_name`, and `element` are present when exporting to PyMOL, RDKit, or OpenMM.
4. Attach or compute a `BondList` when the target interface requires bonds: RDKit `to_mol()` and OpenMM `to_topology()` require one; PyMOL export works without bonds but warns and may be visually incomplete.
5. Remove or repair NaN coordinates before PyMOL export. If NaNs came from RDKit conformer selection or OpenMM topology-only conversion, generate/select coordinates first.

## Visualize in PyMOL without assuming a GUI

1. Probe PyMOL availability with the diagnostic script.
2. Import lazily: `import biotite.interface.pymol as pymol_interface`.
3. Let Biotite auto-start library mode or call `pymol_interface.launch_pymol()` before creating objects. Do not import `cmd` or `pymol` directly before launch planning.
4. Create an object with `pymol_interface.PyMOLObject.from_structure(atoms, delocalize_bonds=True)` when aromatic bond display should use PyMOL's delocalized bond order.
5. Use NumPy masks or integer indices directly with object methods, e.g. `obj.show_as('cartoon', protein_mask)` and `obj.color((1.0, 0.5, 0.0), ligand_mask)`.
6. Use `obj.where(mask)` only when a raw PyMOL selection expression is needed for commands outside `PyMOLObject` wrappers.
7. Render only when the environment supports it: `show()` needs IPython and PyMOL PNG output; `play()` also needs ffmpeg or ImageMagick.
8. Use `pymol_interface.reset()` instead of raw PyMOL `reinitialize` so Biotite-specific PyMOL parameters are restored.

## Convert a Biotite molecule to RDKit

1. Confirm RDKit availability with `scripts/check_optional_interfaces.py`.
2. Prepare a single-molecule `AtomArray` or multi-model `AtomArrayStack` with finite coordinates and an associated `BondList`.
3. Call `rdkit_interface.to_mol(atoms)` for default aromatic handling or `to_mol(atoms, kekulize=True)` when downstream RDKit code expects formal alternating bonds.
4. Set `explicit_hydrogen` deliberately when comparing to RDKit molecules that use implicit hydrogens.
5. Pass `include_extra_annotations=['my_category']` only for Biotite annotation arrays that should become RDKit atom properties.
6. After RDKit processing, convert back with `rdkit_interface.from_mol(mol, ...)`; verify conformer selection and check for NaN coordinates before handing the result to PyMOL.

## Convert Biotite structures to OpenMM and back

1. Confirm OpenMM availability before importing `biotite.interface.openmm`.
2. Prepare atoms through the structure sub-skill: ensure bonds for topology conversion and a valid box when periodic boundaries are needed.
3. Use `to_topology(atoms)` when OpenMM APIs need a topology, and `to_system(atoms)` only when a bare particle-mass system is sufficient.
4. Let OpenMM add hydrogens, solvent, forces, constraints, and integrators; Biotite's `to_system()` does not supply force-field terms.
5. If OpenMM changes atom count or topology, create a new template with `from_topology(topology)` before parsing states.
6. Capture states with `context.getState(getPositions=True)` and parse with `from_state(template, state)` or `from_states(template, states)`.
7. Analyze resulting trajectories via `../structure-analysis/` or visualize them with PyMOL only after checking optional availability.

## Make headless Matplotlib plots

1. In scripts or CI, select a non-interactive backend before importing `matplotlib.pyplot`: `import matplotlib; matplotlib.use('Agg')`.
2. Create `fig, ax = pyplot.subplots(...)` and pass `ax` into `biotite.sequence.graphics` or `biotite.structure.graphics` functions.
3. Keep sequence construction, alignments, feature annotations, and structure filtering in sibling sub-skills; this sub-skill owns only the plotting/export step.
4. Save figures to caller-chosen files with `fig.savefig(...)`; do not call `pyplot.show()` in automated helpers.
5. Close figures after saving to avoid leaking global Matplotlib state in agent-run scripts.

## Source examples adapted or excluded

- Plot, animation, and gallery examples under `doc/examples/scripts/` are reference-only recipes. They often fetch network data, need GUI/display contexts, or create heavyweight renderings.
- This sub-skill bundles only `scripts/check_optional_interfaces.py`, a safe diagnostic helper that imports/probes optional packages without launching PyMOL, rendering images, downloading data, or opening windows.
