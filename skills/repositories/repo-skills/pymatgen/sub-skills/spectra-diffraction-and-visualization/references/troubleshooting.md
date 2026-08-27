# Troubleshooting

## Invalid XRD Wavelength or Radiation Label

Symptom: `XRDCalculator(wavelength="...")` raises a key error, or a workflow asks for an unsupported radiation name.

- Inspect `XRDCalculator.AVAILABLE_RADIATION` in the installed package before using string labels.
- Pass a numeric wavelength in angstroms for custom radiation instead of inventing a string alias.
- Catch non-string, non-numeric wavelength inputs before constructing the calculator; lists and arrays are not accepted.
- Use `NDCalculator(wavelength=<float>)` for neutron diffraction; it does not use the XRD radiation-key table.

## Missing Scattering Data

Symptom: XRD or neutron diffraction raises `ValueError` about missing scattering coefficients or scattering lengths.

- Confirm all sites use real elements covered by the calculator data tables.
- Avoid dummy species, placeholder labels, and unsupported transuranic elements in diffraction snippets.
- For mixed occupancies, confirm each species is a real element and each occupancy is meaningful.
- If the user needs nonstandard scatterers, explain that the built-in calculators are not a general custom-scattering-factor framework.

## Malformed or Unsuitable Structures

Symptom: diffraction, TEM, symmetry refinement, plotting, or visualization fails before producing a figure.

- Confirm the input is a periodic `Structure` with a valid lattice, finite coordinates, and species on every site.
- Route construction, parsing, oxidation-state cleanup, symmetry setup, and transformations to `../structures-local-environments-and-transformations/SKILL.md`.
- Set `symprec=0` for XRD/ND or `symprec=None` for TEM when symmetry refinement is the likely failure source.
- Check units: lattice lengths and wavelengths are in angstroms; XRD/ND `x` values are two-theta degrees; TEM `voltage` is kV and `camera_length` is cm.

## Headless Matplotlib Failures

Symptom: plotting hangs, opens a window, or fails with a display/backend error in CI, containers, SSH sessions, or notebooks without a display.

- Set the backend before importing `matplotlib.pyplot` or pymatgen plotting helpers: `import matplotlib; matplotlib.use("Agg")`.
- Prefer `get_plot()` plus `ax.figure.savefig(...)` or `SpectrumPlotter.save_plot(...)` over `show()`, `show_plot()`, and interactive viewers.
- Include a filename extension such as `.png`, `.pdf`, or `.svg` so matplotlib can choose a writer.
- Close figures in long-running batch scripts if many plots are generated.

## Spectrum Shape, Normalization, and Units

Symptom: `SpectrumPlotter` raises a missing `x` or `y` error, plots a confusing curve, or labels/units are wrong.

- `SpectrumPlotter` only validates that each object has `x` and `y`; physical meaning, axis units, grid compatibility, and normalization remain caller responsibilities.
- XAS `x` values are energies in eV and `y` values are `mu(E)` intensities; XPS `x` values represent binding energy in eV.
- Normalize, smear, shift, or stack spectra only when those operations match the scientific comparison.
- Use `XAS(..., zero_negative_intensity=True)` only when clipping negative intensities is justified; otherwise investigate the source of negative values.

## XAS Stitching and Site Weighting

Symptom: `XAS.stitch()` or `site_weighted_spectrum()` raises structure, element, edge, mode, spectrum-type, or absorbing-index errors.

- Structure mismatch means `StructureMatcher` could not group the structures.
- Site weighting requires one absorbing element, one edge, and at least two site-wise spectra with distinct non-`None` `absorbing_index` values.
- `site_weighted_spectrum()` interpolates over the common energy range; an empty or tiny overlap invalidates the result even when earlier checks pass.
- `XAS.stitch(..., mode="XAFS")` requires one XANES and one EXAFS spectrum for the same edge with energy overlap.
- `XAS.stitch(..., mode="L23")` requires one L2 XANES and one L3 XANES and is limited to supported lighter elements.

## XPS from DOS Problems

Symptom: `XPS.from_dos(dos)` warns about missing cross sections, returns an all-zero/poor spectrum, or fails on DOS access.

- Confirm the input is a `CompleteDos` with projected element-orbital DOS, not only a total DOS.
- Missing orbital cross sections can warn and omit contributions; do not silence those warnings without explaining the approximation.
- The returned binding-energy axis is `-dos.energies`; verify the user’s sign convention before comparing with external XPS data.
- Parsing VASP outputs or locating calculation files is outside this sub-skill unless the user already supplies a `CompleteDos` object.

## TEM Plotting and Export

Symptom: TEM data shape surprises the user, Plotly static export fails, or spot positions appear inconsistent.

- `TEMCalculator.get_pattern()` returns a `pandas.DataFrame`, not `DiffractionPattern`.
- `get_plot_2d()` and `get_plot_2d_concise()` return Plotly figures; static image export may require optional image backends.
- Save Plotly figures as HTML when static export dependencies are missing.
- Recheck `beam_direction`, `voltage`, `camera_length`, and units before interpreting spot geometry.

## Optional VTK and Chemview Visualization

Symptom: `StructureVis` import or initialization fails, `quick_view()` raises `RuntimeError("MolecularViewer not loaded.")`, or rendering fails on a server.

- VTK-backed `StructureVis` requires VTK Python bindings and a GUI or offscreen rendering setup.
- `quick_view()` requires optional `chemview` and is intended for notebooks.
- The baseline install for this skill does not assume optional visualization extras.
- For headless verification, use diffraction and `SpectrumPlotter` file output rather than VTK or chemview rendering.

## FEFF Plotting Helper File Expectations

Symptom: `feff_plot_dos` or `feff_plot_cross_section` fails because files are missing, misnamed, or not FEFF outputs.

- FEFF DOS plotting expects an `ldos` file set plus `feff.inp`.
- FEFF cross-section plotting expects `xmu.dat` plus `feff.inp`.
- These helpers parse existing FEFF outputs through `pymatgen.io.feff.outputs`; they do not run FEFF or synthesize missing files.
- Route exact console-script syntax, `--help` checks, and CLI output-file behavior to `../cli-and-configuration/SKILL.md`.

## API Plotting vs CLI Plotting Boundary

Symptom: a user asks for `pmg plot`, `pmg view`, `feff_plot_dos`, or `feff_plot_cross_section` flags.

- Use this sub-skill for Python API semantics, return objects, headless plotting patterns, and FEFF input expectations.
- Use `../cli-and-configuration/SKILL.md` for command syntax, console-script discovery, persistent config, and safe/mutating CLI classification.
- In headless jobs, choose commands or APIs that save to files instead of showing windows.
