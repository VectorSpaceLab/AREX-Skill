---
name: spectra-diffraction-and-visualization
description: "Use pymatgen diffraction calculators, spectrum objects, plotting
  helpers, FEFF plotting expectations, and optional visualization APIs safely."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Spectra, Diffraction, and Visualization

Use this sub-skill when a task mentions `XRDCalculator`, `NDCalculator`, `TEMCalculator`, `DiffractionPattern`, XAS, XPS, `SpectrumPlotter`, headless spectrum or diffraction plotting, optional VTK/chemview structure visualization, or FEFF DOS/cross-section plotting file expectations.

## Read This First

- For imports, signatures, return objects, calculator options, plotting helpers, optional visualization APIs, and FEFF helper inputs, read [references/api-reference.md](references/api-reference.md).
- For headless-safe recipes covering XRD/ND/TEM, toy XAS/XPS-style spectrum plotting, XAS site weighting, optional visualization, and FEFF caveats, read [references/workflows.md](references/workflows.md).
- For predictable failures involving wavelength labels, scattering data, malformed structures, matplotlib backends, XAS stitching/site weighting, VTK/chemview imports, FEFF inputs, and units, read [references/troubleshooting.md](references/troubleshooting.md).
- To prove the baseline install can compute diffraction peaks and save spectra plots without a GUI, run [scripts/diffraction_spectrum_smoke.py](scripts/diffraction_spectrum_smoke.py) with `python scripts/diffraction_spectrum_smoke.py --help`, then run it with `--output-dir`.

## Routing Boundaries

- Stay here for Python API workflows involving diffraction calculators, `DiffractionPattern` data, XAS/XPS spectrum objects, generic `SpectrumPlotter` plots, FEFF plotting input expectations, and visualization dependency decisions.
- Route structure creation, parsing, symmetry cleanup, oxidation-state setup, local environments, and transformations to `../structures-local-environments-and-transformations/SKILL.md` before diffraction or visualization work.
- Route command syntax for `pmg plot`, `pmg view`, `feff_plot_dos`, `feff_plot_cross_section`, console-script discovery, and persistent configuration to `../cli-and-configuration/SKILL.md`.
- Route Wulff, slab, surface-energy, Pourbaix, interfacial-reactivity, and electrochemical plotting to `../surfaces-interfaces-and-electrochemistry/SKILL.md`.
- Do not treat VTK, chemview, Plotly static export, or FEFF output files as baseline requirements; they are optional or user-data-dependent.

## Default Approach

1. Start from an in-memory `Structure` supplied by the user or produced by another sub-skill; keep reusable examples fixture-free.
2. In automation, select a noninteractive matplotlib backend before importing plotting helpers, then save figures explicitly instead of calling `show()`.
3. Use calculator `get_pattern()` methods when the user needs peak data, and `get_plot()` / `SpectrumPlotter.save_plot()` only when they need plot files.
4. Validate XAS compatibility before combining spectra: matching structures, absorbing element, edge, spectrum type/mode, distinct site-wise absorbing indices, and overlapping energy grids.
5. Explain FEFF helpers as file-based plotters for existing FEFF outputs, not as FEFF calculation generators.
