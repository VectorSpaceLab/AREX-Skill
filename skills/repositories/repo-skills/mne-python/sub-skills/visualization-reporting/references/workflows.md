# Visualization and Report Workflows

This reference helps choose the plotting or reporting surface for an MNE object that already exists in memory. It is self-contained operational guidance; source evidence paths are listed as provenance only and are not runtime dependencies.

## Default automation pattern

Use this for scripts, CI-like checks, report generation, and headless machines:

```python
import os
os.environ.setdefault("MPLBACKEND", "Agg")  # set before pyplot

import matplotlib
matplotlib.use("Agg", force=True)
import matplotlib.pyplot as plt
import mne

fig = evoked.plot(show=False)        # or raw.plot(...), epochs.plot(...)
fig.savefig("figure.png", dpi=150)
plt.close(fig)
```

Notes:

- Most MNE plotting functions and methods accept `show`; use `show=False` unless an interactive user explicitly wants windows.
- If a function returns a browser object rather than a plain Matplotlib figure, prefer Matplotlib browser backend for automated capture or pass the object to `mne.Report.add_figure` when supported.
- Do not set backends after many figures already exist; select the backend before plotting.
- Keep preprocessing and object construction elsewhere. This sub-skill chooses visual outputs and report packaging.

## Raw, Epochs, and Evoked plot routing

| User goal | Use | Key options | Output/check |
| --- | --- | --- | --- |
| Inspect continuous Raw traces, events, annotations, bad channels | `raw.plot(...)` or `mne.viz.plot_raw(raw, ...)` | `events`, `duration`, `start`, `n_channels`, `group_by`, `butterfly`, `show=False`, `block=False`, `decim="auto"`, `scalings`, `annotation_colors`, `annotation_regex` | Figure/browser object. Save only after ensuring selected backend supports capture. |
| Headless Raw summary figure | use Matplotlib backend, choose a short `duration`, `show=False` | `mne.viz.set_browser_backend("matplotlib")`; limit `n_channels`; turn off heavy interactivity | Save PNG/SVG and close. |
| Epoch browsing/rejection display | `epochs.plot(...)` | `n_epochs`, `n_channels`, `events`, `event_color`, `epoch_colors`, `group_by`, `butterfly`, `show=False` | Browser/figure; interactive rejection requires display. |
| Epoch image by channel/type | `epochs.plot_image(...)` | `picks`, `group_by`, `combine`, `vmin`/`vmax`, `cmap`, `evoked`, `ts_args`, `show=False` | List of Matplotlib figures; save each. |
| Epoch drop diagnostics | `epochs.plot_drop_log(...)` | `threshold`, `n_max_plot`, `ignore`, `show=False` | Matplotlib figure with drop percentages. |
| Evoked butterfly/GFP | `evoked.plot(...)` | `picks`, `exclude`, `gfp`, `spatial_colors`, `ylim`, `xlim`, `highlight`, `show=False` | Matplotlib figure. |
| Evoked image | `evoked.plot_image(...)` | `picks`, `group_by`, `cmap`, `colorbar`, `show_names`, `show=False` | Matplotlib figure. |
| Evoked joint plot | `evoked.plot_joint(...)` | `times="peaks"` or explicit times, `ts_args`, `topomap_args`, `show=False` | Time-series plus topomaps. |
| Evoked whitening check | `evoked.plot_white(noise_cov, show=False)` | `noise_cov`, `rank`, `spatial_colors` | Noise covariance visualization; covariance computation belongs elsewhere. |
| Compare conditions | `mne.viz.plot_compare_evokeds(evokeds, ...)` | `picks`, `colors`, `linestyles`, `ci`, `combine`, `axes`, `show=False` | Figure or list of figures depending on picks/axes. |

### Raw/Epochs browser backend selection

- Use `mne.viz.set_browser_backend("matplotlib")` for maximum portability and reports.
- Use `mne.viz.set_browser_backend("qt")` when an operator needs smooth scrolling, richer overview bars, and a working Qt event loop with `mne-qt-browser` installed.
- In scripts that need human interaction, `block=True` may be required to keep the window alive; in automated runs, keep `block=False` and `show=False`.

## Evoked and condition comparison routing

Prefer object methods because they carry the object's metadata and mirror the public API:

```python
fig = evoked.plot(picks="eeg", gfp=True, show=False)
fig_joint = evoked.plot_joint(times="peaks", show=False)
fig_topo = evoked.plot_topomap(times=[0.1, 0.2], ch_type="eeg", show=False)
```

Use module-level functions when writing code that accepts multiple object types or needs a consistent namespace:

```python
fig = mne.viz.plot_evoked(evoked, picks="eeg", show=False)
fig = mne.viz.plot_compare_evokeds({"A": evoked_a, "B": evoked_b}, picks="eeg", show=False)
```

Color scaling rules of thumb:

- Signed sensor/time data: use diverging colormaps such as `"RdBu_r"` unless a domain reason dictates otherwise.
- Strictly positive power/amplitude data: use sequential colormaps such as `"Reds"`, `"viridis"`, or a task-specific map.
- Use `vlim="joint"` for comparable evoked topomaps when all maps should share limits; use explicit `vlim=(low, high)` for publication reproducibility.
- Do not combine `cnorm` with explicit non-`None` `vlim` bounds; `cnorm` already defines normalization.

## Topomap routing

Use topomaps for one value per sensor/channel. Inputs must match positions:

```python
import numpy as np
import mne

info = mne.create_info(["Fp1", "Fp2", "Cz", "O1", "O2"], sfreq=100, ch_types="eeg")
info.set_montage("standard_1020")
data = np.array([1.0, -0.5, 0.2, 0.7, -0.1])
im, cn = mne.viz.plot_topomap(data, info, contours=0, res=32, show=False)
fig = im.axes.figure
fig.savefig("topomap.png", dpi=150)
```

Choose among topomap APIs:

- `mne.viz.plot_topomap(data, info_or_pos, ...)`: standalone vector. `pos` may be an `Info` with one channel type and `len(data)` channels, or an explicit coordinate array.
- `evoked.plot_topomap(times=..., ...)`: topomaps over time with labels, optional colorbar, time averaging, projection controls, and `vlim="joint"` support.
- `epochs.compute_psd(...).plot_topomap(...)` or available PSD-topomap wrappers: spectral topomaps. PSD computation choices belong to analysis/time-frequency guidance; this sub-skill handles figure behavior.
- `plot_tfr_topomap(...)`: time-frequency topomap for a ready TFR object.

Topomap validation before plotting:

1. Confirm `len(data) == len(info["ch_names"])` after picking.
2. Confirm the `Info` has digitization or channel `loc` entries. For EEG, set a montage (`info.set_montage(...)` or equivalent) before plotting.
3. Pick one channel type when using standalone `Info`; mixed EEG/MEG/fNIRS topomaps need separate calls or explicit `ch_type`.
4. Use small `res` and `contours=0` for smoke tests; increase only for final figures.
5. If passing `axes`, ensure the number of axes matches the expected topomap/colorbar layout.

## Source and 3D visualization routing

This sub-skill covers backend choice and export for source/3D visual objects, not inverse modeling. Once another route has produced source estimates, source spaces, BEM, transforms, or surface maps:

- Use `mne.viz.set_3d_backend("pyvistaqt")` for desktop interactive 3D with a Qt display.
- Use `mne.viz.set_3d_backend("notebook")` for inline notebook 3D when the notebook stack is installed.
- Use context managers (`with mne.viz.use_3d_backend("pyvistaqt"):`) to avoid global backend surprises in mixed workflows.
- Close 3D resources with `mne.viz.close_all_3d_figures()` after screenshots or tests.
- For reports, add compatible 3D figures with `Report.add_figure(...)` after verifying PyVista dependencies; otherwise save a static screenshot/image and add it with `Report.add_image(...)`.

Common 3D routes after inputs exist:

| Ready input | Plot/export entry point | Boundary note |
| --- | --- | --- |
| SourceEstimate | `stc.plot(...)` or `mne.viz.plot_source_estimates(...)` | Computing `stc` belongs to source modeling. |
| Alignment/coregistration inputs | `mne.viz.plot_alignment(...)` | Transform/source/BEM setup belongs elsewhere. |
| BEM surfaces | `mne.viz.plot_bem(...)` or report BEM methods | MRI/data acquisition belongs elsewhere. |
| Evoked field maps | `evoked.plot_field(...)` / `mne.viz.plot_evoked_field(...)` | `surf_maps` creation belongs elsewhere. |

## Figure saving and export

Matplotlib:

```python
fig = evoked.plot(show=False)
fig.savefig("evoked.svg", bbox_inches="tight")
fig.savefig("evoked.png", dpi=200)
```

Report-friendly Matplotlib:

```python
report = mne.Report(title="QC", image_format="png")
fig = evoked.plot_joint(show=False)
report.add_figure(fig, title="Evoked joint", tags=("evoked", "joint"))
report.save("qc.html", open_browser=False, overwrite=True)
```

Images already on disk:

```python
report.add_image("topomap.png", title="Topomap", caption="Synthetic EEG topomap")
```

Do not pass an image filename to `Report.add_figure`; use `add_image` for paths and `add_figure` for Matplotlib figures, MNE 3D figures, browser figures, or NumPy image arrays.

## MNE Report workflow

### Minimal report

```python
import mne

report = mne.Report(title="Subject QC", image_format="png")
fig = evoked.plot(show=False)
report.add_figure(fig, title="Evoked butterfly", tags=("evoked", "qc"))
report.save("subject-qc.html", open_browser=False, overwrite=True)
```

### Add MNE objects directly

```python
report = mne.Report(title="Run summary", image_format="png", raw_psd=False, projs=False)
report.add_raw(raw, title="Raw", psd=False, butterfly=True)
report.add_epochs(epochs, title="Epochs", psd=True, topomap_kwargs={"res": 32, "contours": 0})
report.add_evokeds([evoked_a, evoked_b], titles=["A", "B"], n_time_points=5)
report.save("run-summary.html", open_browser=False, overwrite=True)
```

### Folder parsing

Use `Report.parse_folder(...)` when you have a directory of supported MNE files and want a broad automatic summary:

```python
report = mne.Report(title="Folder QC", image_format="png", raw_psd=False)
report.parse_folder(
    data_path="derivatives/sub-01",
    pattern=["*raw.fif", "*epo.fif", "*ave.fif"],
    render_bem=False,
    on_error="warn",
    n_time_points_evokeds=5,
    raw_butterfly=False,
    topomap_kwargs={"res": 32, "contours": 0},
)
report.save("folder-qc.html", open_browser=False, overwrite=True)
```

Use `render_bem=False` unless `subject` and `subjects_dir` are intentionally available. Use `on_error="raise"` in verification when failure should stop the run; use `"warn"` for broad exploratory scans.

### Update an HDF5-backed report

```python
with mne.open_report("qc.h5", title="QC") as report:
    report.add_figure(fig, title="New figure", replace=True)
```

Saving to `.h5`/`.hdf5` preserves an editable report state for `open_report`; saving to `.html` creates a browser-ready artifact.
