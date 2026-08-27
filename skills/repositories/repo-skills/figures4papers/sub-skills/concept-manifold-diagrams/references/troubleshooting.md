# Concept and Manifold Diagram Troubleshooting

Use this guide when conceptual figures, manifold diagrams, diffusion panels, shaded spheres, or 3D arrow layouts fail validation or produce unreadable output.

## Stochastic reproducibility

### The figure changes on every run

Cause: random samples are generated without an explicit seed.

Fix:

- Use `rng = np.random.default_rng(seed)` and pass the generator through every sampling helper.
- Expose `--seed` in reusable scripts.
- Avoid global `np.random` calls in helper functions unless the seed is set once at the top of the script.
- If the user supplies real data, do not reshuffle or subsample without recording the seed and policy.

### Synthetic data are mistaken for measured results

Fix:

- Label examples as synthetic or illustrative in captions and comments.
- Replace toy arrays with user data before making quantitative claims.
- Keep synthetic concept diagrams in a separate panel or script from benchmark plots when possible.

## SciPy and KDE failures

### `ModuleNotFoundError: No module named 'scipy'`

Cause: a KDE, spline, or distance helper needs SciPy but the environment lacks it.

Fix:

- Install SciPy when KDE/spline/distance routines are required.
- For simple templates, use NumPy-only alternatives such as pairwise broadcasting or polynomial/sinusoidal curves.
- If a script catches the import, print a clear message naming the missing optional dependency rather than exposing a long traceback.

### `LinAlgError` or singular covariance in KDE

Cause: the point cloud has too few unique samples, nearly collinear points, or repeated coordinates.

Fix:

1. Check `points.shape` and the number of unique rows.
2. Add a tiny deterministic jitter only for visualization, and mention it in comments.
3. Reduce KDE complexity or draw scatter/ridge curves without contours.
4. For highly structured data, use a density-free schematic instead of forcing KDE.

### KDE contours cover the entire panel

Fix:

- Use upper quantile contour levels (for example 0.72-0.99) rather than equally spaced values from zero.
- Increase grid padding only as much as needed for labels.
- Lower scatter alpha so contours remain readable.

## Diffusion and matrix normalization

### Probability rows do not sum to one

Symptoms:

- Row-normalization assertion fails.
- Diffusion matrix has blank or all-zero rows.

Fix:

- Check that every row has at least one nonzero transition before dividing.
- Add self-connections or reduce the threshold when thresholding removes all neighbors.
- Normalize with `row_sums[row_sums == 0] = 1` only when you also understand why the row was empty.
- Verify `np.allclose(P.sum(axis=1), 1.0, atol=1e-6)` after normalization.

### Swiss-roll panel is slow or cluttered

Cause: all-pairs line drawing scales quadratically in the number of points.

Fix:

- Reduce the template point count.
- Increase the probability threshold for drawn edges.
- Draw only the top-k neighbors per point.
- Use lower alpha and thinner lines for background connections.

## Sphere, geodesic, and arrow failures

### The shaded sphere has NaNs or warnings

Cause: square root is evaluated slightly below zero outside the disk.

Fix:

- Compute `r2 = x**2 + y**2` and mask `r2 <= 1`.
- Use `np.sqrt(np.clip(1 - r2, 0, 1))`.
- Set outside-disk pixels to white or transparent.

### Geodesic arrows cover the points

Fix:

- Shorten the arc before placing arrowheads.
- Draw points after arrows if points are the visual anchor.
- Use smaller arrowhead mutation scale for dense diagrams.

### 3D arrows disappear or render in the wrong order

Cause: ordinary 2D patches are not projection-aware, or the view angle hides them.

Fix:

- Use projection-aware arrow patches for true 3D axes.
- Set deterministic `view_init`, axis limits, and z-limits.
- Hide panes/ticks only after confirming the 3D objects are visible.
- If the arrow is explanatory rather than data-backed, switch to a 2D schematic with text labels.

## Annotation and layout failures

### Text is clipped by `tight_layout`

Fix:

- Add annotations before calling `tight_layout`.
- Use `fig.subplots_adjust` after `tight_layout` for large labels outside axes.
- Save with a small `bbox_inches='tight'` pad only after checking panel sizes remain consistent.

### Labels overlap the geometry

Fix:

- Use short callout boxes with white backgrounds.
- Move repeated labels into a legend-only panel.
- Reduce the number of highlighted points or arrows rather than shrinking all fonts.
- Increase figure width for two-panel concept figures.

### Axes are missing when they should be present

Fix:

- Turn axes off only for dimensionless conceptual diagrams.
- If coordinates have units or the user provided measured values, keep axis labels and ticks or explain why a schematic display is preferred.

## Optional TeX and font failures

### `RuntimeError: Failed to process string with tex`

Cause: TeX rendering was enabled without a usable LaTeX installation.

Fix:

- Keep TeX disabled by default.
- Use matplotlib mathtext for simple symbols.
- If exact TeX is required, verify the host LaTeX installation before rendering.

### Helvetica or a requested sans font is unavailable

Fix:

- Use a fallback stack such as `Arial`, `Helvetica`, `DejaVu Sans`, `sans-serif`.
- Re-run layout after font fallback changes because text extents may shift.

## Export failures

### Output file is missing or empty

Fix:

1. Use a non-interactive backend before importing `pyplot`.
2. Create the output parent directory before saving.
3. Save every requested format before closing the figure.
4. Check file size after saving.

### A diagram looks blurry in a paper draft

Fix:

- Export a vector format such as PDF or SVG for line art.
- Use PNG at 300 DPI for ordinary panels and higher DPI for dense rasterized panels.
- Avoid unnecessarily large image grids; larger grids increase file size more than clarity after a point.

## When to reroute

If the figure is actually a grouped bar comparison, radar chart, trend panel, or heatmap of measured results, route to the matching quantitative sub-skill instead of forcing it into a conceptual diagram template.
