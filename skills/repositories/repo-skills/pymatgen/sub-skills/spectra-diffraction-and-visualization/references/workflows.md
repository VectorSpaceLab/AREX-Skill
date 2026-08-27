# Workflows

These recipes are safe for a baseline install unless a section explicitly names an optional dependency or user-provided file requirement. Set a noninteractive matplotlib backend before importing `pyplot` or pymatgen plotting helpers in headless jobs.

## Headless XRD Peak Data and Plot

```python
import matplotlib
matplotlib.use("Agg")

from pymatgen.analysis.diffraction.xrd import XRDCalculator
from pymatgen.core import Lattice, Structure

structure = Structure(Lattice.cubic(4.209), ["Cs", "Cl"], [[0, 0, 0], [0.5, 0.5, 0.5]])
calculator = XRDCalculator(wavelength="CuKa", symprec=0)
pattern = calculator.get_pattern(structure, two_theta_range=(0, 90))

for two_theta, intensity, hkls, d_hkl in zip(pattern.x[:5], pattern.y[:5], pattern.hkls[:5], pattern.d_hkls[:5]):
    print(f"{two_theta:.3f} deg  I={intensity:.2f}  hkl={hkls}  d={d_hkl:.3f} Å")

ax = calculator.get_plot(structure, two_theta_range=(0, 90), annotate_peaks=None)
ax.figure.savefig("xrd.png", dpi=150, bbox_inches="tight")
```

Use `scaled=False` when preserving absolute intensities for downstream comparison. Use `two_theta_range=None` only when the user really wants all diffracted beams inside the limiting sphere; bounded ranges are better for automation.

## Neutron Diffraction with Debye-Waller Factors

```python
from pymatgen.analysis.diffraction.neutron import NDCalculator

calculator = NDCalculator(wavelength=1.54184, debye_waller_factors={"C": 1.0})
pattern = calculator.get_pattern(structure, two_theta_range=(0, 90))
print(pattern.x[0], pattern.y[0], pattern.hkls[0], pattern.d_hkls[0])
```

Neutron diffraction uses numeric wavelengths and the same `DiffractionPattern` layout as XRD. Missing neutron scattering data raises `ValueError`; do not use dummy species in examples meant for reliable diffraction.

## TEM Data and Plotly Figure

```python
from pymatgen.analysis.diffraction.tem import TEMCalculator

calculator = TEMCalculator(voltage=200, beam_direction=(0, 0, 1), camera_length=160)
print(f"electron wavelength = {calculator.wavelength_rel():.5f} Å")

df = calculator.get_pattern(structure)
print(df.head())

fig = calculator.get_plot_2d_concise(structure)
fig.write_html("tem-pattern.html", include_plotlyjs="cdn")
```

`TEMCalculator.get_pattern()` returns a `pandas.DataFrame`, unlike XRD and ND. Prefer HTML export for Plotly figures unless static-image export dependencies are confirmed.

## Construct and Plot Toy XAS Spectra

```python
import matplotlib
matplotlib.use("Agg")

import numpy as np
from pymatgen.analysis.xas.spectrum import XAS
from pymatgen.core import Lattice, Structure
from pymatgen.vis.plotters import SpectrumPlotter

structure = Structure(Lattice.cubic(4.209), ["Cs", "Cl"], [[0, 0, 0], [0.5, 0.5, 0.5]])
energy = np.linspace(7700, 7800, 201)
mu = np.exp(-0.5 * ((energy - 7728) / 4) ** 2) + 0.2 * np.exp(-0.5 * ((energy - 7750) / 8) ** 2)
xas = XAS(energy, mu, structure, "Cs", edge="K", spectrum_type="XANES", absorbing_index=0)

plotter = SpectrumPlotter(xshift=xas.e0, yshift=0.1)
plotter.add_spectrum("Cs K-edge", xas, color="b")
plotter.save_plot("xas.png", xlim=(-20, 80))
```

`xshift` is applied to all plotted spectra and is commonly used to zero energy at an edge or Fermi level. `yshift` offsets successive spectra. Use `stack=True` for filled stacked plots when the physical interpretation allows stacking.

## Site-Weighted XAS with Energy-Grid Validation

```python
import numpy as np
from pymatgen.analysis.xas.spectrum import XAS, site_weighted_spectrum
from pymatgen.core import Lattice, Structure

structure = Structure(
    Lattice.tetragonal(3.8, 9.5),
    ["Ti", "Ti", "O", "O"],
    [[0, 0, 0], [0.5, 0.5, 0.5], [0.3, 0.3, 0.2], [0.7, 0.7, 0.8]],
)
energy_a = np.linspace(4950, 5050, 301)
energy_b = np.linspace(4960, 5040, 241)
site_a = XAS(energy_a, np.exp(-((energy_a - 4990) / 8) ** 2), structure, "Ti", "K", "XANES", absorbing_index=0)
site_b = XAS(energy_b, np.exp(-((energy_b - 5000) / 10) ** 2), structure, "Ti", "K", "XANES", absorbing_index=1)

left = max(min(site_a.x), min(site_b.x))
right = min(max(site_a.x), max(site_b.x))
if left >= right:
    raise ValueError("Site spectra do not share an overlapping energy range")

weighted = site_weighted_spectrum([site_a, site_b], num_samples=500)
print(weighted.absorbing_element, weighted.edge, weighted.x[0], weighted.x[-1])
```

This is a common hard case: `site_weighted_spectrum()` checks structures, absorbing element, edge, and distinct site indices, then interpolates over the intersection of energy grids and weights by symmetry multiplicity. Diagnose mismatched absorbing indices and empty overlap before assuming an interpolation bug.

## XAS Stitching

```python
from pymatgen.analysis.xas.spectrum import XAS

# xanes and exafs are XAS objects for the same structure, element, edge, and absorbing_index.
xafs = xanes.stitch(exafs, num_samples=500, mode="XAFS")

# l2 and l3 are XANES objects for the same lighter absorbing element and structure.
l23 = l2.stitch(l3, num_samples=500, mode="L23")
```

`XAFS` mode requires one XANES and one EXAFS spectrum for the same edge with energy overlap. `L23` mode requires one L2 XANES and one L3 XANES and is limited to supported lighter elements.

## XPS from DOS

```python
from pymatgen.analysis.xps import XPS

# dos is a CompleteDos, commonly obtained by parsing an electronic-structure calculation.
xps = XPS.from_dos(dos)
xps.smear(0.3)
```

`XPS.from_dos()` expects projected element/orbital DOS. If the input `CompleteDos` lacks projections or an orbital cross section, the result can warn or be physically unusable. Parsing calculation directories and CLI file discovery belongs to the relevant I/O or CLI workflow.

## Optional Structure Visualization

```python
try:
    from pymatgen.vis.structure_vtk import StructureVis
except Exception as exc:
    raise RuntimeError("VTK-backed visualization is not available in this environment") from exc

visualizer = StructureVis(show_unit_cell=True, show_bonds=False)
visualizer.set_structure(structure)
visualizer.write_image("structure.png")
```

Run VTK visualization only when `vtk` and a rendering-capable environment are available. For notebook-only chemview rendering, call `quick_view(structure)` only after confirming `chemview` is installed. Do not use either path as a baseline CI smoke check.

## FEFF Plotting Helper Expectations

- FEFF DOS plotting expects an `ldos` file set plus `feff.inp`; the helper parses them into DOS objects and plots the total, site, element, or orbital DOS.
- FEFF cross-section plotting expects `xmu.dat` plus `feff.inp`; the helper plots single-atom and embedded absorption cross sections.
- These helpers require existing FEFF output files and usually show plots interactively. Route exact command syntax and safe help probing to `../cli-and-configuration/SKILL.md`.
- In automation, prefer API paths that return axes/figures and explicitly save files; avoid unguarded `show()` calls.
