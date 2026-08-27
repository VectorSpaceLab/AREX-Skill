---
name: visualization-reporting
description: "Guide MNE-Python plotting, visualization backends, topomaps,
  source visualization routing, and Report creation for Researcher."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# Visualization and Reporting Router

Use this sub-skill when the task is to make, save, debug, or package MNE-Python visual outputs after the data object already exists: Raw/Epochs/Evoked browsers, static Matplotlib figures, topomaps, source-visualization routing, optional 3D backend decisions, and `mne.Report` HTML/HDF5 reports.

## Route first

- **Continuous data browser**: `Raw.plot(...)`, `mne.viz.plot_raw(...)`, event/annotation coloring, channel grouping, bad-channel inspection, and non-interactive exports. See [workflows](references/workflows.md#raw-epochs-and-evoked-plot-routing) and [backend choices](references/backend-compatibility.md#2d-browser-backends).
- **Epoch review and summary plots**: `Epochs.plot(...)`, `Epochs.plot_image(...)`, `Epochs.plot_drop_log(...)`, `Epochs.plot_topo_image(...)`, and PSD/topomap summaries. See [workflows](references/workflows.md#raw-epochs-and-evoked-plot-routing).
- **Evoked figures and comparisons**: butterfly/image/joint/topomap/topo/white plots, comparison overlays, and publication-style figure saving. See [workflows](references/workflows.md#evoked-and-condition-comparison-routing) and [API reference](references/api-reference.md#evoked-plot-method-family).
- **Standalone topomaps**: `mne.viz.plot_topomap(data, info_or_pos, show=False)` with channel positions, masking, interpolation, `vlim`/`cnorm`, and axes/colorbar handling. See [topomap workflow](references/workflows.md#topomap-routing) and [troubleshooting](references/troubleshooting.md#topomap-and-channel-location-errors).
- **3D/source visual outputs**: choose PyVistaQt or notebook rendering for already-computed source estimates, alignments, BEM, sensors, and screenshots. Route inverse modeling, forward model math, and source-estimate creation to `source-modeling-inverse`; return here only for plotting and export choices. See [backend compatibility](references/backend-compatibility.md#3d-backends).
- **Reports**: build `mne.Report`, add Raw/Epochs/Evoked/custom figures/images/HTML, parse folders when appropriate, and save with `open_browser=False` for automation. See [report workflow](references/workflows.md#mne-report-workflow) and [API reference](references/api-reference.md#report-api-family).
- **CLI report commands**: route command discovery and shell-facing `mne` CLI help to `cli-datasets-config`; this sub-skill only covers Python `mne.Report` and the plotting/report APIs.
- **Preprocessing choices**: filtering, epoching, rejection, baselining, ICA, annotations, and averaging belong to `preprocessing-epochs-evoked`; this sub-skill assumes the object to visualize is ready or gives only visualization-safe validation.

## Operating rules

1. Prefer `show=False` in scripts, notebooks that must run unattended, tests, and reports; explicitly save and close Matplotlib figures.
2. Set a non-interactive backend before importing `matplotlib.pyplot` in headless automation.
3. Use browser/Qt/PyVista interactivity only when a display and optional dependencies are intentionally available.
4. Keep generated reports reproducible: choose an output file, set `open_browser=False`, and pass `overwrite=True` only when replacing that exact output is desired.
5. For topomaps, verify channel locations before changing interpolation or color scaling; missing montage/digitization is the common failure, not a colormap issue.
6. Use the bundled [plotting backend probe](scripts/plotting_backend_probe.py) before promising GUI, notebook, or 3D behavior in an unknown runtime.

## Quick commands

```bash
python sub-skills/visualization-reporting/scripts/plotting_backend_probe.py --format text
python sub-skills/visualization-reporting/scripts/plotting_backend_probe.py --output mne-topomap.png --report-output mne-report.html
```

Run the script from any project where MNE-Python is importable. It does not require original repository files or datasets.

## Evidence provenance

This sub-skill distills public API stubs, source signatures, visualization/report API pages, visualization tutorials/examples, visualization/report tests, dependency metadata, and an installed signature report. Provenance paths include `mne/viz`, `mne/report`, `mne/viz/__init__.pyi`, `mne/report/__init__.pyi`, `doc/api/visualization.rst`, `doc/api/report.rst`, `tutorials/visualization`, `examples/visualization`, `mne/viz/tests`, `mne/report/tests`, and `pyproject.toml`.
