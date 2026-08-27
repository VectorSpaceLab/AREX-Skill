# Backend Compatibility Guide

MNE-Python visualization spans Matplotlib, 2D browser backends, 3D PyVista backends, notebook integrations, and `mne.Report`. Choose the lightest backend that satisfies the user-visible output.

## Decision table

| Runtime situation | Recommended choice | Why | Avoid |
| --- | --- | --- | --- |
| Non-interactive script, CI, server, batch report | `MPLBACKEND=Agg`, `show=False`, `open_browser=False` | Deterministic, no display, works for Matplotlib figures and topomaps | Qt browser, notebook backend, blocking windows |
| Local desktop exploratory Raw/Epochs review | `mne.viz.set_browser_backend("qt")` if installed; otherwise `"matplotlib"` | Qt browser has richer interactive scrolling; Matplotlib is portable fallback | Headless execution without display |
| Static notebook figure outputs | notebook inline Matplotlib or Agg in execution pipeline | Good for saved notebooks and simple figures | Expecting rich 3D interactivity from inline Matplotlib |
| Notebook 3D interaction | `mne.viz.set_3d_backend("notebook")` with notebook/PyVista stack | Inline 3D when dependencies are present | Google Colab-like environments without compatible VTK/trame stack |
| Desktop 3D source visualization | `mne.viz.set_3d_backend("pyvistaqt")` | Full PyVistaQt interaction and source plots | Running without Qt/display |
| Report generation with custom figures | Matplotlib figures with `show=False`; `Report.save(open_browser=False)` | Embeds images and avoids browser side effects | Passing image paths to `add_figure` |

## Headless Matplotlib pattern

Set the backend before importing `pyplot`:

```python
import os
os.environ.setdefault("MPLBACKEND", "Agg")

import matplotlib
matplotlib.use("Agg", force=True)
import matplotlib.pyplot as plt
```

Then use:

```python
fig = evoked.plot(show=False)
fig.savefig("evoked.png", dpi=150, bbox_inches="tight")
plt.close(fig)
```

For topomaps, `plot_topomap` returns an image object:

```python
im, cn = mne.viz.plot_topomap(data, info, contours=0, show=False)
im.axes.figure.savefig("topomap.png", dpi=150)
```

## 2D browser backends

Public controls:

```python
mne.viz.set_browser_backend("matplotlib")
mne.viz.set_browser_backend("qt")
backend = mne.viz.get_browser_backend()
with mne.viz.use_browser_backend("matplotlib"):
    fig = raw.plot(show=False)
```

Backend capabilities from source documentation:

- `matplotlib`: Raw/Epochs/ICA source browser support, events, annotation editing, projector toggling, butterfly mode, selection mode. More portable for scripts and reports.
- `qt`: same core browser functions plus smooth scrolling and overview-bar/z-score-mode features. Requires `mne-qt-browser` and a Qt binding.

Operational rules:

- Use `qt` only when the user wants interactive review and a display is available.
- In scripts launched outside an existing Qt event loop, `block=True` may be necessary for human interaction.
- If `get_browser_backend()` returns `None` or backend import fails, fall back to Matplotlib for static outputs.
- Do not use browser interactions as the only validation in a headless workflow; validate saved image/report artifacts instead.

## 3D backends

Public controls:

```python
mne.viz.set_3d_backend("pyvistaqt")
mne.viz.set_3d_backend("notebook")
with mne.viz.use_3d_backend("pyvistaqt"):
    fig = mne.viz.create_3d_figure((600, 600), show=False)
mne.viz.close_all_3d_figures()
```

Backend capabilities from source documentation:

- `pyvistaqt`: full support for source estimates, vector source estimates, alignment, sparse source estimates, evoked fields, snapshots, linked brains, large data, opacity/transparency, glyphs, smooth shading, subplots, and toolbar.
- `notebook`: supports the main 3D functions and inline Jupyter/JupyterLab display, but not every desktop feature (`link_brains` is not listed as supported in the source capability table).
- The old name `pyvista` is accepted when setting and maps to `pyvistaqt`; `get_3d_backend()` returns `pyvistaqt`, not `pyvista`.

Optional dependency evidence from package metadata:

- Core MNE requires Matplotlib.
- Full visualization/reporting installs include `mne-qt-browser`, `pyvista`, `pyvistaqt`, `qtpy`, a Qt binding, `ipympl`, `ipywidgets`, `trame`, `trame-pyvista`, `trame-vtk`, `trame-vuetify`, `vtk`, and `pillow` among other packages.
- The full default chooses a PySide6 Qt binding; a full PyQt6 variant is also defined.

Headless 3D choices:

1. If only 2D quality-control output is needed, skip 3D and create Matplotlib screenshots/figures.
2. If 3D is required on Linux without a display, use a virtual display or an off-screen-capable VTK/Mesa setup. Verify with a small 3D probe before running expensive source plots.
3. If PyVista imports but rendering fails, treat the 3D backend as unavailable for automation until the display/OpenGL stack is fixed.

## Notebook and IPython decisions

Recommended notebook patterns from install guidance:

- For fast, correct rendering and rich interactivity in IPython/Jupyter, use Qt Matplotlib when available (`%matplotlib qt` or launching IPython with a Qt Matplotlib backend).
- For static notebooks, inline Matplotlib works, but some 3D functionality loses interactivity or opens separate windows.
- On Windows notebooks, an explicit Qt GUI event loop may be required for interactive Qt windows.
- The notebook 3D backend requires PyVista plus notebook support packages; check them before selecting it.

For reproducible notebook execution, prefer explicit `show=False`, save figures/reports, and close figures just as in scripts.

## Report backend behavior

`mne.Report` is usually compatible with headless automation when all figures are produced with non-interactive settings:

```python
report = mne.Report(title="QC", image_format="png")
report.add_figure(fig, title="Evoked")
report.save("qc.html", open_browser=False, overwrite=True)
```

Rules:

- Use `open_browser=False` in scripts and tests.
- Choose `image_format="png"` for broad compatibility, `"svg"` for vector fidelity and possibly larger files, or `"webp"`/`"auto"` when acceptable.
- Add image paths with `add_image`, not `add_figure`.
- Report methods that render BEM/source content need subject metadata and may need 3D dependencies; set `render_bem=False` or `plot_src=False` when those inputs/backends are unavailable.

## Bundled probe

Use [plotting_backend_probe.py](../scripts/plotting_backend_probe.py) to check the active runtime without requiring optional dependencies. It verifies:

- MNE import status and version.
- Matplotlib import status and backend.
- Display-related environment hints.
- A synthetic EEG `plot_topomap(..., show=False)` smoke test when possible.
- Optional 3D/browser dependency presence by import-spec lookup.
- Optional `mne.Report` save path if requested.
