# Visualization and Report Troubleshooting

Use this file when a plotting/report task fails or produces unusable output. Start with backend and object validation before changing scientific parameters.

## Quick triage checklist

1. Is the runtime interactive? If not, set a non-interactive Matplotlib backend before importing `pyplot`, use `show=False`, save files explicitly, and close figures.
2. Does the object have the required metadata? Topomaps need channel positions; reports that render BEM/source content need subject information and optional 3D dependencies.
3. Does the chosen backend match the output? Use Matplotlib/Agg for static images, Qt for human browser interaction, PyVistaQt/notebook for 3D.
4. Is the output path explicit and overwritable? For reports, use `save(..., open_browser=False, overwrite=True)` only for intentional replacement.
5. Can the bundled probe reproduce a tiny topomap/report in the same environment?

## Blank plots or empty saved figures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Saved PNG/SVG is blank | Figure was saved before draw, wrong figure object was saved, or a browser object was returned instead of the expected Matplotlib figure | Use the returned figure/object, call `fig.canvas.draw()` if needed, save `im.axes.figure` for `plot_topomap`, and close after saving. |
| Script hangs after plotting | `show=True`, `block=True`, or a GUI backend opened an event loop | Use `show=False`, `block=False`, `MPLBACKEND=Agg`, and `Report.save(open_browser=False)`. |
| No window appears in desktop session | Non-interactive backend selected or no active event loop | For interactive review, select Qt/Matplotlib GUI backend before plotting; in scripts use `block=True` only when a human should interact. |
| Report contains an empty or missing figure | Figure was closed before `Report.add_figure`, incompatible 3D/browser capture, or unsupported image format | Add the live figure before closing; for uncertain 3D, save a screenshot/image and use `add_image`; use `image_format="png"` first. |

Minimal nonblank check:

```python
fig = evoked.plot(show=False)
fig.canvas.draw()
assert fig.axes, "plot returned a figure with no axes"
fig.savefig("check.png", dpi=100)
```

For `plot_topomap`:

```python
im, cn = mne.viz.plot_topomap(data, info, contours=0, show=False)
fig = im.axes.figure
fig.canvas.draw()
assert fig.axes[0].images or fig.axes[0].collections
```

## Missing Qt or browser backend

Common messages include inability to load a valid 2D backend, import errors for `mne-qt-browser`, Qt binding errors, or windows closing immediately.

Recovery:

- For static output, avoid Qt: `mne.viz.set_browser_backend("matplotlib")`, `show=False`, save a file.
- For interactive Raw/Epochs review, install/use an environment with `mne-qt-browser`, `qtpy`, and a Qt binding, then run with a display.
- In IPython/Jupyter desktop sessions, enable a Qt event loop before plotting if windows should be interactive.
- If a Qt browser object cannot be saved directly, switch to Matplotlib backend or add static Matplotlib figures/images to a report.

## Missing PyVista, PyVistaQt, VTK, or notebook 3D stack

Common messages include no valid 3D backend, import errors for `pyvista`, `pyvistaqt`, `vtk`, `qtpy`, `ipywidgets`, or trame packages, OpenGL/display errors, or notebook backend not functional.

Recovery:

- If source modeling is not the user's task, downgrade to 2D/static views and state that 3D export is unavailable in this runtime.
- For desktop 3D, verify `pyvista`, `pyvistaqt`, Qt, and display/OpenGL first, then select `mne.viz.set_3d_backend("pyvistaqt")`.
- For notebook 3D, verify the notebook backend stack and select `mne.viz.set_3d_backend("notebook")`.
- On headless Linux, use a virtual display or off-screen-capable VTK/Mesa setup; do not treat successful imports as proof that rendering works.
- Close 3D resources after probes with `mne.viz.close_all_3d_figures()`.

## Topomap and channel location errors

Common messages from tests/source include:

- `No channels of type ...`
- `No digitization points found.`
- `points ... doesn't match ... channels.`
- `times must be 1D` or times outside the evoked interval.
- `image_interp must be ...`
- Invalid `border`, `extrapolate`, or `axes` length/type errors.

Recovery:

1. Pick the intended channel type before plotting.
2. Ensure data length matches picked channels exactly.
3. For EEG, set a montage before plotting: `info.set_montage("standard_1020")` or use the user's measured montage.
4. For standalone `plot_topomap`, pass an `Info` with one channel type or an explicit position array with shape `(n_channels, 2)` or equivalent accepted coordinates.
5. For evoked topomaps, keep `times` within `evoked.times`; use `times="peaks"` or a small explicit list for smoke tests.
6. If using custom axes and `colorbar=True`, allocate axes for the topomaps and colorbar according to the function's expected layout.
7. For quick validation, use `res=8` or `res=16`, `contours=0`, and `sensors=False` to reduce rendering complexity.

## Report asset failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `Report(image_format=...)` raises invalid value | Format not one of supported report image formats | Use `"png"`, `"svg"`, `"webp"`, or `"auto"`. |
| `add_figure` rejects a string/path | Paths are not figures | Use `Report.add_image(path, title=...)` for image files. |
| Saving asks for overwrite input | Existing output and `overwrite=False` | In automation, pass `overwrite=True` only when replacing that output is intended. |
| Browser opens during automated run | `open_browser=True` default | Use `Report.save(..., open_browser=False)`. |
| `parse_folder` warns about MRI/BEM/trans rendering | `subject`/`subjects_dir` or BEM/source inputs unavailable | Set `render_bem=False`, `plot_src=False`, or provide subject metadata through the appropriate source-data route. |
| HDF5 report save/load fails | HDF5 optional dependencies unavailable | Save HTML, or prepare an environment with HDF5 support before using `.h5`/`.hdf5` and `open_report`. |
| Report HTML is huge | Many high-resolution images, SVG/vector output, or too many time points | Lower `img_max_width`, `img_max_res`, `n_time_points`, `res`, or use `image_format="png"`/`"webp"`. |

## Browser/report object mismatch

`Report.add_figure` accepts Matplotlib figures, MNE `Figure3D`, compatible browser figures, NumPy image arrays, or lists/arrays of those. If uncertain:

```python
fig = raw.plot(show=False)
try:
    report.add_figure(fig, title="Raw")
except TypeError:
    # fallback: make a simpler Matplotlib summary figure or save a static image
    pass
```

For robust automation, prefer explicit static Matplotlib plots over interactive browser state.

## When to route elsewhere

- If the user asks how to filter, epoch, reject, annotate, baseline, or compute evoked data before plotting, route to `preprocessing-epochs-evoked`.
- If the user asks how to compute a forward model, inverse operator, source estimate, BEM/source space, or source statistics, route to `source-modeling-inverse`.
- If the user asks for `mne report` CLI flags, dataset downloads, or command-line configuration, route to `cli-datasets-config`.
