# API Reference

This reference covers the inspected public APIs for `pymatgen` 2026.5.4 with `pymatgen-core` 2026.5.18. Prefer live introspection for exact enum-like values, but keep the workflow patterns here self-contained.

## Diffraction Calculators

| Capability | Import | Current signature | Primary return | Notes |
| --- | --- | --- | --- | --- |
| Powder X-ray diffraction | `from pymatgen.analysis.diffraction.xrd import XRDCalculator` | `XRDCalculator(wavelength="CuKa", symprec=0, debye_waller_factors=None)` | `DiffractionPattern` from `get_pattern(structure, scaled=True, two_theta_range=(0, 90))` | `wavelength` is a numeric angstrom value or a key in `XRDCalculator.AVAILABLE_RADIATION`; `symprec` refines through spglib when nonzero; Debye-Waller factors are element-symbol keyed. |
| Powder neutron diffraction | `from pymatgen.analysis.diffraction.neutron import NDCalculator` | `NDCalculator(wavelength=1.54184, symprec=0, debye_waller_factors=None)` | `DiffractionPattern` from `get_pattern(structure, scaled=True, two_theta_range=(0, 90))` | Uses numeric wavelengths in angstroms, constant neutron scattering lengths, and no X-ray radiation-key table. |
| Transmission electron diffraction | `from pymatgen.analysis.diffraction.tem import TEMCalculator` | `TEMCalculator(symprec=None, voltage=200, beam_direction=(0, 0, 1), camera_length=160, debye_waller_factors=None, cs=1)` | `pandas.DataFrame` from `get_pattern(structure, scaled=None, two_theta_range=None)` | `voltage` is in kV, `camera_length` is in cm, and `cs` is in mm. Plot helpers return Plotly figures. |

`DiffractionPattern` is imported from `pymatgen.analysis.diffraction.core` and subclasses `pymatgen.core.spectrum.Spectrum`. It is constructed as `DiffractionPattern(x, y, hkls, d_hkls)`, where `x` is two-theta in degrees, `y` is intensity, `hkls` is a list of Miller-index/multiplicity dictionaries, and `d_hkls` is interplanar spacing in angstroms. XRD and neutron calculators inherit `get_plot(structure, two_theta_range=(0, 90), annotate_peaks="compact", ax=None, with_labels=True, fontsize=16)`, `show_plot()`, and `plot_structures()` from the abstract diffraction calculator.

`XRDCalculator.AVAILABLE_RADIATION` exposes supported string keys. The inspected table includes common `Cu`, `Mo`, `Cr`, `Fe`, `Co`, and `Ag` K-alpha/K-beta variants such as `CuKa`, `CuKa1`, `CuKa2`, `MoKa`, and `AgKb1`. For custom radiation, pass a numeric wavelength in angstroms instead of inventing a string alias.

## Spectrum Objects

| Capability | Import | Current signature | Notes |
| --- | --- | --- | --- |
| X-ray absorption spectrum | `from pymatgen.analysis.xas.spectrum import XAS` | `XAS(x, y, structure, absorbing_element, edge="K", spectrum_type="XANES", absorbing_index=None, zero_negative_intensity=False)` | `x` is energy in eV and `y` is `mu(E)` intensity. The object computes `e0` from the maximum derivative and a signed `k` grid. More than 5% negative intensities warn; `zero_negative_intensity=True` clips them. |
| Site-weighted XAS | `from pymatgen.analysis.xas.spectrum import site_weighted_spectrum` | `site_weighted_spectrum(xas_list, num_samples=500)` | Requires structures that match under `StructureMatcher`, one absorbing element, one edge, at least two distinct non-`None` `absorbing_index` values, and usable common energy-grid overlap. Weights by symmetry multiplicity. |
| X-ray photoelectron spectrum | `from pymatgen.analysis.xps import XPS` | `XPS(x, y, *args, **kwargs)` and `XPS.from_dos(dos)` | `XPS` subclasses `Spectrum`; `from_dos` expects a `CompleteDos` with element-orbital projections, weights by bundled photoionization cross sections, and returns binding energy as `-dos.energies`. |

`XAS` inherits common `Spectrum` behavior such as `as_dict()` / `from_dict()`, arithmetic, `normalize()`, `smear()`, and interpolation. `XAS.stitch(other, num_samples=500, mode="XAFS" | "L23")` checks structure, absorbing element, and absorbing index compatibility. `XAFS` mode combines XANES and EXAFS for the same edge with overlap; `L23` mode combines L2 and L3 XANES for supported lighter elements.

## Plotting APIs

| Capability | Entry point | Current signature | Notes |
| --- | --- | --- | --- |
| Generic spectra plotting | `from pymatgen.vis.plotters import SpectrumPlotter` | `SpectrumPlotter(xshift=0.0, yshift=0.0, stack=False, color_cycle=("qualitative", "Set1_9"))` | Add spectra with `add_spectrum(label, spectrum, color=None)` or `add_spectra(mapping, key_sort_func=None)`. Use `get_plot(xlim=None, ylim=None)`, `save_plot(filename, **kwargs)`, or `show(**kwargs)`. |
| XRD/ND matplotlib plot | Calculator `get_plot()` | `get_plot(structure, two_theta_range=(0, 90), annotate_peaks="compact", ax=None, with_labels=True, fontsize=16)` | Returns a matplotlib `Axes`; save with `ax.figure.savefig(...)` in headless workflows. Avoid `show_plot()` in automation. |
| TEM Plotly plot | `TEMCalculator` methods | `get_plot_2d(structure)` and `get_plot_2d_concise(structure)` | Return Plotly `Figure` objects. HTML export is safer than static image export when Plotly image backends are absent. |

`SpectrumPlotter.add_spectrum()` validates only that the object has `x` and `y` attributes. Axis labels, physical units, grid compatibility, and normalization are caller responsibilities. `SpectrumPlotter.save_plot()` delegates to matplotlib and requires a filename with an extension such as `.png` or `.pdf`.

## Optional Structure Visualization

| Capability | Import | Current signature | Runtime expectation |
| --- | --- | --- | --- |
| VTK structure viewer | `from pymatgen.vis.structure_vtk import StructureVis` | `StructureVis(element_color_mapping=None, show_unit_cell=True, show_bonds=False, show_polyhedron=True, poly_radii_tol_factor=0.5, excluded_bonding_elements=None)` | Requires VTK Python bindings and a rendering-capable GUI or offscreen setup. `write_image(filename="image.png", magnification=1, image_format="png")` saves rendered output. |
| Notebook chemview viewer | `from pymatgen.vis.structure_chemview import quick_view` | `quick_view(structure, bonds=True, conventional=False, transform=None, show_box=True, bond_tol=0.2, stick_radius=0.1)` | Requires optional `chemview`. When absent, it raises `RuntimeError("MolecularViewer not loaded.")`. Intended for notebooks. |

The baseline package inspection did not install broad optional visualization extras. Use XRD/ND/spectrum file-output checks as the default headless validation path; use VTK or chemview only after the user confirms optional dependencies and rendering support.

## CLI-Adjacent FEFF Helpers

FEFF plotting console scripts are file-based helpers, not baseline APIs. Exact console syntax belongs to `../cli-and-configuration/SKILL.md`; this sub-skill owns the file expectations and plotting semantics.

- `feff_plot_dos` parses an FEFF `ldos` file set plus `feff.inp` through `pymatgen.io.feff.outputs.LDos`, builds DOS objects, and calls a plotter interactively.
- `feff_plot_cross_section` parses `xmu.dat` plus `feff.inp` through `pymatgen.io.feff.outputs.Xmu`, then plots single-atom and embedded absorption cross sections.
- These helpers do not run FEFF or create missing FEFF outputs. Verify file presence and choose a headless save path or CLI-owned output flag when available.
