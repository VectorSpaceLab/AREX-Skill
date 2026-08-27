# Interfaces and Visualization Troubleshooting

Use this page when optional interface imports, conversions, rendering, or plotting fail. Optional package failures are expected in many Biotite installations and should be handled gracefully.

## Missing optional packages

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ImportError` or package requirement error importing `biotite.interface.rdkit` | RDKit is not installed or is too old for the used Biotite interface path | Run `scripts/check_optional_interfaces.py`; install RDKit in the active environment or choose a non-RDKit path. RDKit conversion is optional, not required for core Biotite. |
| `ImportError` importing `biotite.interface.openmm` | OpenMM is not installed | Install OpenMM only for simulation interop tasks; do not require it for structure analysis or file parsing. |
| `ImportError` importing `biotite.interface.pymol` | PyMOL/pymol2 is not installed or unavailable in the environment | Install PyMOL/pymol2 if visualization through PyMOL is required, or use Matplotlib/file export alternatives. |
| `ImportError` importing `matplotlib` or graphics modules | Matplotlib is not installed | Install Matplotlib for plotting or skip plot generation and return data tables/arrays instead. |
| `ImportError: IPython is not installed` from `pymol_interface.show()` or `play()` | PyMOL notebook display helper needs IPython display classes | Save/render through caller-managed PyMOL commands or install IPython for notebook display. |

## PyMOL startup and session issues

- Library mode is the safest default for scripts. It has no GUI and is enough for PyMOL API calls and file/image rendering.
- Use `launch_interactive_pymol()` only when a user explicitly needs an interactive window. GUI mode can fail on headless systems and is not supported in some macOS contexts.
- Do not import `cmd` or `pymol` directly from `biotite.interface.pymol` before deciding launch behavior. Access them as `pymol_interface.cmd` and `pymol_interface.pymol` after import to avoid accidental duplicate launches.
- `DuplicatePyMOLError` usually means a PyMOL session has already been started. Reuse the existing `pymol_interface.pymol` instance or restart the process instead of trying to launch a second session.
- Use `pymol_interface.reset()` rather than PyMOL's raw `reinitialize` command so Biotite restores parameters needed for object ordering and movie feedback.
- Interactive PyMOL can conflict with Matplotlib-created OpenGL contexts. If both are needed, prefer PyMOL library mode or launch interactive PyMOL before creating Matplotlib figures.

## PyMOL conversion and rendering issues

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ValueError: PyMOL does not support infinite or NaN coordinates` | The `AtomArray` contains NaN/inf coordinates, often from topology-only OpenMM conversion or missing RDKit conformers | Generate/select coordinates first, filter out invalid atoms/models, or avoid PyMOL export until coordinates are finite. |
| `LossyConversionWarning` about unmappable bond types | PyMOL supports only a limited bond-order vocabulary; coordination and some special Biotite bond types degrade | Treat visualization bonds as display semantics. For chemistry-preserving workflows, keep Biotite/RDKit bond data separately. |
| Coordination bonds display as single bonds | PyMOL cannot represent Biotite coordination bonds exactly in this interface | Warn the user and avoid using PyMOL output as authoritative bond chemistry. |
| `ModifiedObjectError` from `PyMOLObject` methods | Atoms were added to or deleted from the underlying PyMOL object after the handle was created | Recreate the `PyMOLObject` wrapper from the current PyMOL object or avoid mutating atom counts through raw PyMOL commands. |
| `NonexistentObjectError` | The wrapped PyMOL object was deleted or the session reset | Recreate the object with `PyMOLObject.from_structure()` after reset. |
| `TimeoutError` from `show()` | PyMOL did not write PNG output within the timeout | Increase timeout for ray tracing, disable `use_ray`, simplify the scene, or verify PyMOL can render in the environment. |
| `RenderError` from `play()` | ffmpeg/ImageMagick is missing or failed | Install an encoder, switch to still images, or return frame-generation instructions instead of running video export. |
| PyMOL PNG rendering crashes in pytest | Known fragility of PyMOL `png()` under pytest execution | Do not make PyMOL render tests mandatory; use import/conversion diagnostics or manual rendering checks. |

## RDKit conversion issues

- `to_mol()` requires an associated `BondList`. If a loaded structure has no bonds, route through file-IO/structure workflows to load with bonds or compute/connect bonds before conversion.
- `explicit_hydrogen=False` with explicit hydrogen atoms raises a structure error. Either remove hydrogens before conversion or set `explicit_hydrogen=True`/`None` intentionally.
- Missing conformers or selecting the wrong conformer type can produce NaN coordinates after `from_mol()`. Generate coordinates with RDKit or select an existing conformer before PyMOL export.
- RDKit may not preserve stereochemistry or all uncommon bond orders through Biotite round trips. Use warnings and SMILES/topology checks to decide whether the loss matters.
- RDKit coordinate arrays may need C-contiguous layout; Biotite's interface handles this for `to_mol()`, but custom downstream RDKit code may still assume contiguous arrays.
- Dative/coordination bond handling is task-sensitive: `use_dative_bonds=True` can be chemically useful but may trigger RDKit kekulization failures.

## OpenMM conversion issues

- `to_topology()` needs bonds. `to_system()` can create a bare system without bonds, but it only sets particle masses and optional periodic box vectors.
- `from_topology()` returns an `AtomArray` with NaN coordinates because OpenMM topology does not contain positions. Use it as a template, then fill coordinates from states.
- `from_state()` and `from_states()` require OpenMM states created with `getPositions=True`; otherwise positions are not available for parsing.
- If OpenMM `Modeller` adds hydrogens/solvent or otherwise changes topology, do not reuse the original AtomArray as the state template. Build a new template with `from_topology()`.
- OpenMM periodic boxes must be in an OpenMM-compatible vector orientation. Fix box vectors in the structure workflow before calling `to_topology()` or `to_system()`.
- Remember unit expectations: Biotite structure coordinates are Å-oriented, while OpenMM positions and boxes are unit-bearing quantities. The interface converts to/from Å, but custom OpenMM code must attach units explicitly.

## Matplotlib and plotting issues

- In headless environments, set a non-interactive backend such as `Agg` before importing `matplotlib.pyplot`.
- Pass a Matplotlib `Axes` into Biotite graphics functions. Most graphics helpers draw onto existing axes and do not create figures for you.
- Avoid `pyplot.show()` in automated agent helpers; save figures and close them instead.
- If text scaling looks slightly off, prefer `plot_scaled_text()` for new code; `set_font_size_in_coord()` is deprecated and relies on backend renderer behavior.
- Sequence and structure graphics are visualization layers only. If a plot is wrong because data, alignments, filters, bonds, or coordinates are wrong, route back to the owning analysis sub-skill.
