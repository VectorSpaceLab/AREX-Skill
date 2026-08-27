# Visualization and Report API Reference

Signatures below were verified from the installed signature report where available and from public source definitions/stubs for the same checkout. They are included here so a future Researcher does not need to inspect source files for common plotting/report calls.

## Public visualization namespace

`mne.viz.__all__` exposes these major families: Raw/Epochs/Evoked plotting, topomaps, layouts, projections, ICA plots, covariance/filter/event plots, 3D/source visualization, sensor/montage plots, browser backend controls, and UI events.

High-frequency public functions:

```text
mne.viz.plot_raw(raw, events=None, duration=10.0, start=0.0, n_channels=20, bgcolor='w', color=None, bad_color='lightgray', event_color='cyan', *, annotation_colors=None, annotation_regex='.*', scalings=None, remove_dc=True, order=None, show_options=False, title=None, show=True, block=False, highpass=None, lowpass=None, filtorder=4, clipping=_RAW_CLIP_DEF, show_first_samp=False, proj=True, group_by='type', butterfly=False, decim='auto', noise_cov=None, event_id=None, show_scrollbars=True, show_scalebars=True, show_zero_line=False, time_format='float', precompute=None, use_opengl=None, picks=None, theme=None, overview_mode=None, splash=True, verbose=None, figure_class=None)
mne.viz.plot_epochs(epochs, picks=None, scalings=None, n_epochs=20, n_channels=20, title=None, events=False, event_color=None, order=None, show=True, block=False, decim='auto', noise_cov=None, butterfly=False, show_scrollbars=True, show_scalebars=True, show_zero_line=False, epoch_colors=None, event_id=None, group_by='type', precompute=None, use_opengl=None, *, theme=None, overview_mode=None, splash=True, annotation_colors=None, figure_class=None)
mne.viz.plot_evoked(evoked, picks=None, exclude='bads', unit=True, show=True, ylim=None, xlim='tight', proj=False, hline=None, units=None, scalings=None, titles=None, axes=None, gfp=False, window_title=None, spatial_colors='auto', zorder='unsorted', selectable=True, noise_cov=None, time_unit='s', sphere=None, *, highlight=None, verbose=None)
mne.viz.plot_compare_evokeds(evokeds, picks=None, colors=None, linestyles=None, styles=None, cmap=None, vlines='auto', ci=True, truncate_yaxis='auto', truncate_xaxis=True, ylim=None, invert_y=False, show_sensors=None, legend=True, split_legend=None, axes=None, title=None, show=True, combine=None, sphere=None, time_unit='s')
```

## Raw plot method family

```text
Raw.plot(events=None, duration=10.0, start=0.0, n_channels=20, bgcolor='w', color=None, bad_color='lightgray', event_color='cyan', *, annotation_colors=None, annotation_regex='.*', scalings=None, remove_dc=True, order=None, show_options=False, title=None, show=True, block=False, highpass=None, lowpass=None, filtorder=4, clipping=_RAW_CLIP_DEF, show_first_samp=False, proj=True, group_by='type', butterfly=False, decim='auto', noise_cov=None, event_id=None, show_scrollbars=True, show_scalebars=True, show_zero_line=False, time_format='float', precompute=None, use_opengl=None, picks=None, theme=None, overview_mode=None, splash=True, verbose=None, figure_class=None) -> Figure | MNEQtBrowser
```

Operational notes:

- `events` overlays vertical event markers; `event_color` may be a color or mapping.
- `annotation_colors` and `annotation_regex` control displayed annotations.
- `proj=True` applies projectors only for plotting; it does not mutate the stored Raw data.
- `highpass`/`lowpass` here are display filters; do not treat them as preprocessing.
- `group_by`, `butterfly`, `show_scrollbars`, and `show_scalebars` are browser presentation choices.
- For static reports, use Matplotlib browser backend and `show=False`.

PSD wrappers exist (`plot_raw_psd`, `plot_raw_psd_topo`), but for new workflows prefer computing a spectrum and plotting that object when available in the user's MNE version.

## Epoch plot method family

```text
Epochs.plot(picks=None, scalings=None, n_epochs=20, n_channels=20, title=None, events=False, event_color=None, order=None, show=True, block=False, decim='auto', noise_cov=None, butterfly=False, show_scrollbars=True, show_scalebars=True, show_zero_line=False, epoch_colors=None, event_id=None, group_by='type', precompute=None, use_opengl=None, *, theme=None, overview_mode=None, splash=True, annotation_colors=None, figure_class=None) -> Figure | MNEQtBrowser
Epochs.plot_image(picks=None, sigma=0.0, vmin=None, vmax=None, colorbar=True, order=None, show=True, units=None, scalings=None, cmap=None, fig=None, axes=None, overlay_times=None, combine=None, group_by=None, evoked=True, ts_args=None, title=None, clear=False) -> list[Figure]
Epochs.plot_drop_log(threshold=0, n_max_plot=20, subject=None, color=(0.9, 0.9, 0.9), width=0.8, ignore=('IGNORED',), show=True) -> Figure
Epochs.plot_topo_image(layout=None, sigma=0.0, vmin=None, vmax=None, colorbar=None, order=None, cmap='RdBu_r', layout_scale=0.95, title=None, scalings=None, border='none', fig_facecolor='k', fig_background=None, font_color='w', select=False, show=True) -> Figure
Epochs.plot_psd(fmin=0, fmax=inf, tmin=None, tmax=None, picks=None, proj=False, *, method='auto', average=False, dB=True, estimate='power', xscale='linear', area_mode='std', area_alpha=0.33, color='black', line_alpha=None, spatial_colors=True, sphere=None, exclude='bads', ax=None, show=True, n_jobs=1, verbose=None, **method_kw) -> Figure
```

Operational notes:

- `events=True` in `Epochs.plot` displays `epochs.events`; `events=False` hides them.
- `plot_image` returns a list because grouping/picks may create multiple figures.
- `combine` in `plot_image` can summarize channels; keep the underlying analysis decision documented elsewhere.
- `plot_drop_log` only visualizes drop reasons already present in `epochs.drop_log`.

## Evoked plot method family

```text
Evoked.plot(picks=None, exclude='bads', unit=True, show=True, ylim=None, xlim='tight', proj=False, hline=None, units=None, scalings=None, titles=None, axes=None, gfp=False, window_title=None, spatial_colors='auto', zorder='unsorted', selectable=True, noise_cov=None, time_unit='s', sphere=None, *, highlight=None, verbose=None) -> Figure
Evoked.plot_image(picks=None, exclude='bads', unit=True, show=True, clim=None, xlim='tight', proj=False, units=None, scalings=None, titles=None, axes=None, cmap='RdBu_r', colorbar=True, mask=None, mask_style=None, mask_cmap='Greys', mask_alpha=0.25, time_unit='s', show_names='auto', group_by=None, sphere=None) -> Figure
Evoked.plot_topo(layout=None, layout_scale=0.945, color=None, border='none', ylim=None, scalings=None, title=None, proj=False, vline=(0.0,), fig_background=None, merge_grads=False, legend=True, axes=None, background_color='w', noise_cov=None, exclude='bads', select=False, show=True) -> Figure
Evoked.plot_topomap(times='auto', *, average=None, ch_type=None, scalings=None, proj=False, sensors=True, show_names=False, mask=None, mask_params=None, mask_label_params=None, contours=6, outlines='head', sphere=None, image_interp='cubic', extrapolate='auto', border='mean', res=64, size=1, cmap=None, vlim=(None, None), cnorm=None, colorbar=True, cbar_fmt='%3.1f', units=None, axes=None, time_unit='s', time_format=None, nrows=1, ncols='auto', show=True) -> Figure
Evoked.plot_field(surf_maps, time=None, time_label='t = %0.0f ms', n_jobs=None, fig=None, vmax=None, n_contours=21, *, show_density=True, alpha=None, interpolation='nearest', interaction='terrain', time_viewer='auto', verbose=None) -> Figure3D | EvokedField
Evoked.plot_white(noise_cov, show=True, rank=None, time_unit='s', sphere=None, axes=None, *, spatial_colors='auto', verbose=None) -> Figure
Evoked.plot_joint(times='peaks', title='', picks=None, exclude='bads', show=True, ts_args=None, topomap_args=None) -> Figure | list
Evoked.plot_psd(fmin=0, fmax=inf, tmin=None, tmax=None, picks=None, proj=False, *, method='auto', average=False, dB=True, estimate='power', xscale='linear', area_mode='std', area_alpha=0.33, color='black', line_alpha=None, spatial_colors=True, sphere=None, exclude='bads', ax=None, show=True, n_jobs=1, verbose=None, **method_kw) -> Figure
```

Operational notes:

- `proj='interactive'` creates additional controls; avoid it in headless automation.
- `times='peaks'` finds local maxima in global field power for topomap/joint plots.
- `average` in `plot_topomap` averages over time windows centered on `times`.
- `show_names` may be bool or callable for topomap label formatting.
- `plot_field` needs 3D surface maps; route creation of those maps to source-modeling guidance.

## Topomap API family

Installed signature report verified:

```text
mne.viz.plot_topomap(data, pos, *, ch_type='eeg', sensors=True, names=None, mask=None, mask_params=None, mask_label_params=None, contours=6, outlines='head', sphere=None, image_interp='cubic', extrapolate='auto', border='mean', res=64, size=1, cmap=None, vlim=(None, None), cnorm=None, axes=None, show=True, onselect=None)
```

Related public functions:

```text
mne.viz.plot_evoked_topomap(evoked, times='auto', *, average=None, ch_type=None, scalings=None, proj=False, sensors=True, show_names=False, mask=None, mask_params=None, mask_label_params=None, contours=6, outlines='head', sphere=None, image_interp='cubic', extrapolate='auto', border='mean', res=64, size=1, cmap=None, vlim=(None, None), cnorm=None, colorbar=True, cbar_fmt='%3.1f', units=None, axes=None, time_unit='s', time_format=None, nrows=1, ncols='auto', show=True)
mne.viz.plot_tfr_topomap(tfr, tmin=None, tmax=None, fmin=0.0, fmax=inf, *, ch_type=None, baseline=None, mode='mean', sensors=True, show_names=False, mask=None, mask_params=None, mask_label_params=None, contours=6, outlines='head', sphere=None, image_interp='cubic', extrapolate='auto', border='mean', res=64, size=2, cmap=None, vlim=(None, None), cnorm=None, colorbar=True, cbar_fmt='%1.1e', units=None, axes=None, show=True)
mne.viz.plot_epochs_psd_topomap(epochs, bands=None, tmin=None, tmax=None, proj=False, *, bandwidth=None, adaptive=False, low_bias=True, normalization='length', ch_type=None, normalize=False, agg_fun=None, dB=False, sensors=True, names=None, mask=None, mask_params=None, mask_label_params=None, contours=0, outlines='head', sphere=None, image_interp='cubic', extrapolate='auto', border='mean', res=64, size=1, cmap=None, vlim=(None, None), cnorm=None, colorbar=True, cbar_fmt='auto', units=None, axes=None, show=True, n_jobs=None, verbose=None)
```

Return behavior:

- `plot_topomap` returns `(im, cn)`, where `im` is a Matplotlib image and `cn` is a contour set. Use `im.axes.figure` to save the figure.
- `Evoked.plot_topomap` and `plot_evoked_topomap` return a Matplotlib figure.
- `plot_tfr_topomap` and PSD topomap helpers return figures for ready TFR/PSD workflows.

## Backend control APIs

2D browser backends:

```text
mne.viz.set_browser_backend(backend_name, verbose=None)
mne.viz.get_browser_backend()
mne.viz.use_browser_backend(backend_name)
```

Valid browser names are `"matplotlib"` and `"qt"`; legacy `"pyqtgraph"` maps to `"qt"` in source. The Qt backend requires the optional browser and Qt stack.

3D backends:

```text
mne.viz.set_3d_backend(backend_name, verbose=None)
mne.viz.get_3d_backend()
mne.viz.use_3d_backend(backend_name)
mne.viz.create_3d_figure(size, bgcolor=(0, 0, 0), smooth_shading=None, handle=None, *, scene=True, show=False, title='MNE 3D Figure')
mne.viz.close_3d_figure(figure)
mne.viz.close_all_3d_figures()
```

Valid 3D names are `"pyvistaqt"` and `"notebook"`; legacy `"pyvista"` maps to `"pyvistaqt"` when setting.

## Report API family

Installed signature report verified:

```text
mne.Report(info_fname=None, subjects_dir=None, subject=None, title=None, cov_fname=None, baseline=None, image_format='auto', raw_psd=False, projs=False, *, img_max_width=850, img_max_res=100, collapse=(), verbose=None)
```

Public report entry points:

```text
mne.open_report(fname, **params)
Report.add_raw(raw, title, *, psd=None, projs=None, butterfly=True, scalings=None, tags=('raw',), replace=False, topomap_kwargs=None)
Report.add_epochs(epochs, title, *, psd=True, projs=None, image_kwargs=None, topomap_kwargs=None, drop_log_ignore=('IGNORED',), tags=('epochs',), replace=False)
Report.add_evokeds(evokeds, *, titles=None, noise_cov=None, projs=None, n_time_points=None, tags=('evoked',), replace=False, topomap_kwargs=None, n_jobs=None)
Report.add_figure(fig, title, *, caption=None, image_format=None, tags=('custom-figure',), section=None, replace=False)
Report.add_image(image, title, *, caption=None, tags=('custom-image',), section=None, replace=False)
Report.add_html(html, title, *, tags=('custom-html',), section=None, replace=False)
Report.add_bem(subject, title, *, subjects_dir=None, decim=2, width=512, n_jobs=None, tags=('bem',), section=None, replace=False)
Report.parse_folder(data_path, pattern=None, n_jobs=None, mri_decim=2, sort_content=True, *, on_error='warn', image_format=None, render_bem=True, plot_src=False, n_time_points_evokeds=None, n_time_points_stcs=None, raw_butterfly=True, stc_plot_kwargs=None, topomap_kwargs=None, verbose=None)
Report.save(fname=None, open_browser=True, overwrite=False, sort_content=False, *, verbose=None)
mne.open_report(fname, **params)
```

Report behavior:

- `image_format='auto'` resolves to a browser-friendly raster format when saving figures; explicit supported formats are `png`, `svg`, and `webp`.
- `add_figure` accepts Matplotlib figures, MNE `Figure3D`, compatible browser figures, NumPy image arrays, or arrays/lists of those. It rejects path-like strings; use `add_image` for image files.
- `add_image` accepts an existing image file with a supported suffix.
- `save(..., open_browser=False)` is the automation-safe default.
- Saving to `.h5`/`.hdf5` creates an editable report state for `open_report`; other suffixes save HTML.
- `parse_folder` can scan supported MNE files, but rendering BEM/source content needs matching subject information and optional 3D dependencies.

## Provenance summary

Evidence was derived from public stubs, source definitions, API pages, visualization/report tests, and installed API signatures. Key source evidence paths: `mne/viz/__init__.pyi`, `mne/report/__init__.pyi`, `mne/io/base.py`, `mne/epochs.py`, `mne/evoked.py`, `mne/viz/raw.py`, `mne/viz/epochs.py`, `mne/viz/evoked.py`, `mne/viz/topomap.py`, `mne/viz/_figure.py`, `mne/viz/backends/renderer.py`, `mne/report/report.py`, `doc/api/visualization.rst`, `doc/api/report.rst`, `mne/viz/tests`, `mne/report/tests`, and the installed signature report.
