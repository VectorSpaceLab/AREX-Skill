# Cross-Cutting Troubleshooting

Use this when a figures4papers-style figure task fails before a specific sub-skill has a better workflow-level diagnosis.

## Install and import failures

### `ModuleNotFoundError: No module named 'matplotlib'` or `numpy`

Cause: the plotting dependencies are not installed in the Python environment that runs the script.

Fix:

1. Install at least `numpy` and `matplotlib`.
2. For trend/heatmap/manifold workflows, also install optional dependencies when used: `scipy`, `seaborn`, and `python-dateutil`.
3. Run `scripts/check_figure_env.py --output figure_env_smoke --formats png` from this skill to verify imports and headless export.

### Optional dependency is missing

- `scipy` is needed for KDE/spline/distance-heavy concept diagrams when the template uses those features.
- `seaborn` is useful for seaborn-style heatmaps, but the bundled heatmap template can use matplotlib directly.
- `python-dateutil` is useful for robust month arithmetic in timeline scripts; simple categorical timelines can avoid it.

If an optional package is unavailable and the user did not require the exact feature, choose the bundled template path that avoids it.

## Headless and backend failures

### Figure windows hang or no output appears on a server

Cause: a GUI backend was selected in a non-interactive session.

Fix:

- Set `matplotlib.use("Agg")` before importing `matplotlib.pyplot` in scripts that run unattended.
- Do not call `plt.show()` in batch figure-generation scripts.
- Save to files and verify nonzero file sizes.

### `RuntimeError: Invalid DISPLAY variable`

Fix: use the Agg backend and rerun the script from a clean process. Setting the backend after importing `pyplot` is often too late.

## Font and TeX failures

### Helvetica or Arial warnings

Cause: the target machine lacks those fonts. The figures4papers look remains acceptable with DejaVu Sans fallback.

Fix:

- Use `font.family` or `font.sans-serif` with `DejaVu Sans` first for portable scripts.
- Only request exact Helvetica/Arial rendering when the venue or user requires it and the font is installed.

### `RuntimeError: Failed to process string with tex`

Cause: `text.usetex=True` was enabled but LaTeX is missing or incomplete.

Fix:

- Disable TeX for the portable default.
- Use matplotlib mathtext and Unicode arrows for common labels.
- If exact TeX is required, install and verify LaTeX outside the script, then rerun with the script's `--use-tex` option where provided.

## Data and validation failures

### Shape mismatch

Symptoms include missing bars, malformed radar polygons, shifted heatmap annotations, or explicit validation errors.

Fix:

- Convert inputs to explicit NumPy arrays and print shapes before plotting.
- Match row/column conventions to the owning sub-skill reference.
- Validate label counts against array axes.
- Do not rely on broadcasting; transpose data intentionally and document the convention.

### Non-finite values

Fix:

- Replace or remove `NaN`/`inf` before plotting.
- For radar charts, imputation changes polygon geometry and should be user-approved.
- For heatmaps, missingness may be shown with a masked color instead of coerced to zero.

### Log scale receives zero or negative values

Fix:

- Use log scale only for strictly positive rates or throughputs.
- Convert positive times to throughput only after checking all times are positive.
- Ask how to handle timeouts, censored values, or zeros.

## Output failures

### `FileNotFoundError` during `savefig`

Fix: create the parent directory before saving. All bundled templates and `figure_style_helpers.finalize_figure` do this automatically.

### Output exists but is empty

Fix:

1. Save before closing the figure.
2. Check requested formats are supported by matplotlib.
3. Avoid overwriting a directory path as if it were a file basename.
4. Run a bundled template with built-in data to distinguish environment/export issues from user-data issues.

### PDF/SVG text is not editable

Fix: set `svg.fonttype = 'none'` and `pdf.fonttype = 42`/`ps.fonttype = 42` before saving. The root helper applies these defaults.

## Routing failures

If troubleshooting reveals the figure family was misidentified:

- Bar/grid comparison problems belong to `bar-comparison-figures`.
- Line, event, radar, heatmap, and matrix problems belong to `trend-radar-heatmap-figures`.
- Synthetic concept, manifold, diffusion, sphere, and geometry problems belong to `concept-manifold-diagrams`.

Do not patch a template beyond its purpose when a sibling sub-skill has the right data contract and troubleshooting guidance.
