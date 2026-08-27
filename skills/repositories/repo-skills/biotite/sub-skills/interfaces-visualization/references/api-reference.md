# Interfaces and Visualization API Reference

Use this page to choose the correct optional interface or graphics surface. The optional packages are not core Biotite dependencies; import probes should happen before a recipe assumes the package is installed.

## Interface package boundary

| Surface | Use for | Main entry points | Important boundary |
| --- | --- | --- | --- |
| `biotite.interface.pymol` | Send `AtomArray`/`AtomArrayStack` objects to PyMOL, style with NumPy-compatible selections, render static images or movies, draw CGOs/shapes | `PyMOLObject.from_structure()`, `PyMOLObject.to_structure()`, `to_model()`, `from_model()`, `draw_cgo()`, `draw_box()`, `draw_arrows()`, `show()`, `play()`, `reset()` | Requires PyMOL/pymol2. Library mode starts without a GUI; interactive GUI launch is separate and more fragile. |
| `biotite.interface.rdkit` | Convert small molecules between Biotite `AtomArray`/`AtomArrayStack` and RDKit `Mol` for SMILES/InChI, depiction, conformer work, and cheminformatics | `to_mol(atoms, kekulize=False, use_dative_bonds=False, include_extra_annotations=(), explicit_hydrogen=None)`, `from_mol(mol, ...)` | Requires RDKit. Input to `to_mol()` must have a `BondList`; hydrogen handling and unsupported bond types can change results. |
| `biotite.interface.openmm` | Convert structures into OpenMM topology/system objects and parse OpenMM state coordinates/boxes back to Biotite | `to_topology(atoms)`, `to_system(atoms)`, `from_topology(topology)`, `from_context(template, context)`, `from_state(template, state)`, `from_states(template, states)` | Requires OpenMM. Biotite coordinates/boxes are converted through OpenMM units; state recovery needs a matching template. |
| `biotite.visualize` | Biotite colors and Matplotlib helper patches/arrows | `colors`, `plot_scaled_text()`, `set_font_size_in_coord()`, `AdaptiveFancyArrow` | Helpers lazily use Matplotlib objects and are best kept inside plotting functions. |
| `biotite.sequence.graphics` | Sequence/alignment/features/plasmid/dendrogram/logo plots on Matplotlib axes | `plot_alignment()`, `plot_sequence_logo()`, `plot_feature_map()`, `plot_plasmid_map()`, `plot_dendrogram()`, color scheme helpers | Requires a prepared `Axes`; sequence construction/alignment belongs to `../sequence-analysis/`. |
| `biotite.structure.graphics` | Simple 2D structure-related plotting on Matplotlib axes | `plot_atoms()`, `plot_ball_and_stick_model()`, `plot_nucleotide_secondary_structure()` | Use only for graphics; structure filtering, bonds, and geometry preparation belong to `../structure-analysis/`. |

## PyMOL interface details

- Import as `import biotite.interface.pymol as pymol_interface`; avoid `from biotite.interface.pymol import cmd, pymol` before launch planning because these attributes can auto-start a PyMOL session.
- `launch_pymol()` starts object-oriented library mode, which is suitable for scripts and non-GUI rendering. `launch_interactive_pymol(*args)` starts a GUI and should be opt-in.
- `PyMOLObject.from_structure(atoms, name=None, delete=True, delocalize_bonds=False)` creates a PyMOL object directly from Biotite atoms and returns a handle with methods such as `show_as()`, `color()`, `set()`, `set_bond()`, `zoom()`, `orient()`, `label()`, and `where()`.
- `PyMOLObject.to_structure(state=..., altloc=..., include_bonds=...)` converts a PyMOL object back to Biotite; avoid comparing PyMOL-derived bond perception as exact chemistry unless the workflow explicitly tolerates PyMOL bond semantics.
- `to_model(atom_array, delocalize_bonds=False)` rejects infinite or NaN coordinates. It maps only PyMOL-supported bond orders and warns with `LossyConversionWarning` for unsupported Biotite bond types.
- `draw_cgo()`, `get_cylinder_cgo()`, `get_cone_cgo()`, `get_sphere_cgo()`, `get_point_cgo()`, `get_line_cgo()`, `get_multiline_cgo()`, `draw_box()`, and `draw_arrows()` create CGO-based PyMOL objects for geometry overlays.
- `show(size=None, use_ray=False, timeout=60.0)` returns an IPython image and uses PyMOL `png`; `play(size=None, fps=30, format='gif'|'mp4')` needs external video tooling such as ffmpeg or ImageMagick.

## RDKit interface details

- Import as `import biotite.interface.rdkit as rdkit_interface` only after RDKit availability is acceptable for the task.
- `to_mol(atoms, kekulize=False, use_dative_bonds=False, include_extra_annotations=(), explicit_hydrogen=None)` preserves atom order and stores standard Biotite annotations in RDKit PDB residue info.
- `to_mol()` expects an associated Biotite `BondList`; missing bonds raise a structure error. Prepare bonds with structure/file-IO workflows before using this interface.
- `explicit_hydrogen=None` infers hydrogen handling from the input. Set it deliberately when comparing with RDKit molecules using implicit hydrogens.
- Aromatic bonds can be represented as RDKit aromatic bonds by default or kekulized into single/double/triple alternatives with `kekulize=True`.
- `use_dative_bonds=True` maps Biotite coordination bonds to RDKit dative bonds, but downstream RDKit kekulization may fail for some molecules.
- `from_mol(mol, ...)` can select conformers and may return NaN coordinates when the requested conformer type is absent; downstream PyMOL export will reject those NaNs.

## OpenMM interface details

- Import as `import biotite.interface.openmm as openmm_interface` only when OpenMM is installed or the task explicitly asks for simulation interop.
- `to_topology(atoms)` creates an `openmm.app.Topology` and requires bonds. It preserves chain/residue/atom annotations where OpenMM supports them and uses the first model/box for stacks.
- `to_system(atoms)` creates an `openmm.System` with particle masses and optional periodic box vectors; it does not create force-field forces or constraints.
- `from_topology(topology)` creates an `AtomArray` with topology annotations, bonds, optional box, and coordinates set to NaN because OpenMM topology has no positions.
- `from_state(template, state)`, `from_states(template, states)`, and `from_context(template, context)` copy topology from a Biotite template and replace coordinates/box from OpenMM states created with `getPositions=True`.
- OpenMM box vectors must satisfy OpenMM periodic-box shape requirements: first vector on x-axis and second vector in the xy-plane. Invalid Biotite boxes raise a structure error during conversion.

## Matplotlib-backed graphics details

- Sequence graphics import from `biotite.sequence.graphics`; provide Matplotlib `Axes` explicitly and keep figure saving/showing under caller control.
- Common sequence graphics: `plot_alignment()`, `plot_alignment_similarity_based()`, `plot_alignment_type_based()`, `plot_alignment_array()`, `get_color_scheme()`, `list_color_scheme_names()`, `plot_dendrogram()`, `plot_feature_map()`, `plot_sequence_logo()`, and `plot_plasmid_map()`.
- Structure graphics import from `biotite.structure.graphics`; common entry points are `plot_atoms()`, `plot_ball_and_stick_model()`, and `plot_nucleotide_secondary_structure()`.
- General visualization helpers in `biotite.visualize` provide Biotite color names and scalable text/arrow helpers for Matplotlib axes.
