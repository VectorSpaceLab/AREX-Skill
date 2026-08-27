---
name: plotting-reporting
description: "Create Nilearn plots, interactive views, surface visualizations,
  cluster tables, and HTML reports while handling optional plotting dependencies
  and headless environments."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# Plotting and Reporting

Use this sub-skill when a task asks for Nilearn visualization or reporting:
static brain plots, interactive HTML views, surface plots, design/event/matrix
figures, connectome displays, cluster tables, or generated HTML reports.

## Read First

- For function families, common signatures, return objects, `output_file`, and
  engine behavior, read [API Reference](references/api-reference.md).
- For practical plot/report recipes, read [Workflows](references/workflows.md).
- For optional dependency, headless, browser, threshold, colorbar, orientation,
  and report warnings, read [Troubleshooting](references/troubleshooting.md).
- For a no-network local sanity check, run
  `python scripts/smoke_plotting_reporting.py --help`.

## Route Here

- Choose between `plot_img`, `plot_anat`, `plot_epi`, `plot_roi`,
  `plot_prob_atlas`, `plot_stat_map`, `plot_glass_brain`, `plot_carpet`, or
  image-comparison helpers for static volume figures.
- Build connectome, marker, matrix, event, design-matrix, contrast-matrix, or
  design-correlation visualizations.
- Use `plot_surf`, `plot_surf_stat_map`, `plot_surf_roi`, `plot_img_on_surf`,
  `view_surf`, or `view_img_on_surf` after valid surface or volume inputs exist.
- Use `view_img`, `view_connectome`, or `view_markers` when the deliverable is
  an embeddable interactive HTML view rather than a static Matplotlib display.
- Produce `get_clusters_table` outputs, GLM HTML reports, or save/open
  `HTMLReport` objects and estimator reports.
- Diagnose plotting-specific optional dependencies such as Matplotlib, Plotly,
  Kaleido, Chrome, browser display, and Matplotlib backends.

## Route Elsewhere

- Use `../data-io-signal/SKILL.md` for loading, resampling, masking,
  unmasking, confound cleaning, or constructing NIfTI images before plotting.
- Use `../surface-workflows/SKILL.md` for mesh/data contracts,
  `SurfaceImage`, fsaverage helpers, and volume-to-surface projection details
  before visualization choices.
- Use `../glm-analysis/SKILL.md` for GLM fitting, contrasts, thresholding
  decisions, and statistical interpretation before plotting/reporting outputs.
- Use `../maskers-regions/SKILL.md` for masker setup, labels/maps extraction,
  region signals, and fitted masker objects before calling `generate_report`.
- Route package installation policy and broad environment repair to the root
  Nilearn troubleshooting guidance; keep this sub-skill focused on symptoms
  specific to plotting and report rendering.

## Fast Operating Rules

- In scripts and CI, set a non-interactive Matplotlib backend before importing
  `nilearn.plotting`, and prefer `output_file=` for static figures so displays
  close automatically.
- If you call static plotters without `output_file`, close returned display or
  figure objects with `.close()` or `matplotlib.pyplot.close()`.
- Keep interactive `view_*` outputs as HTML objects; save them with
  `.save_as_html(...)` rather than relying on a browser or notebook display.
- Treat Plotly surface PNG export as an optional extra: `engine="plotly"` needs
  Plotly, and static image export also needs Kaleido plus a compatible Chrome.
- Avoid network fetchers in plotting/report smoke examples unless the user
  explicitly asks for datasets; create tiny synthetic images or reuse inputs
  already supplied by the user.
- Document thresholding, `two_sided`, `cluster_threshold`, colorbar, and
  orientation choices when plots or cluster tables support decisions.

## Bundled Script

Run `python scripts/smoke_plotting_reporting.py` for a no-network smoke check
that creates a tiny synthetic image, saves a static plot headlessly, and tries a
cluster table. Use `--output-dir` to keep the generated files.
