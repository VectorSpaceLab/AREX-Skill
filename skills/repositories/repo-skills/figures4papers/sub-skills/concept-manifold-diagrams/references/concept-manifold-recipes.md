# Concept and Manifold Diagram Recipes

Use this reference when a user asks for a publication-ready conceptual figure rather than a direct quantitative benchmark. The recipes are distilled from figures4papers-style scripts into self-contained patterns: probability panels, manifold clouds, diffusion matrices, shaded spheres, geodesic arrows, and clean explanatory layouts. Use user data when supplied; otherwise keep synthetic examples explicitly labeled as illustrative.

## Shared contract

- Use a headless matplotlib backend for unattended scripts.
- Keep random examples deterministic with an explicit seed and record the seed in the script.
- Prefer portable sans-serif fonts, white backgrounds, top/right spines off for axis-based panels, and axis-free panels for pure diagrams.
- Use the house semantic palette: blue for the key/proposed structure, neutral gray for background/prior, red for contrast or force arrows, teal/violet for secondary geometry.
- Keep synthetic samples, interpolation curves, and KDE contours clearly separate from measured experimental data.
- Save every requested format from the same figure object, create parent directories, and close the figure after export.

## Data contracts

### Probability/distribution concept panel

Use this for before/after distributions, prior-vs-guided probability curves, or one-dimensional answer-space diagrams.

```python
x = np.linspace(0, 1, 500)
curves = {
    "prior": gaussian(x, 0.30, 0.10),
    "guided": gaussian(x, 0.72, 0.08),
    "blind": 0.35 * gaussian(x, 0.30, 0.14) + 0.18,
}
target_x = 0.72
```

Validation:

- Every curve must be a finite 1D array with the same length as `x`.
- Normalize curves only when the plot is meant to compare shape rather than absolute density.
- Arrow/gap annotations should point to actual curve values, not arbitrary y positions.
- If the distribution is synthetic, label it as an illustrative answer space or conceptual density.

### Manifold scatter or KDE panel

Use this for latent-space cartoons, manifold ridges, and point-cloud overlays.

```python
points_a = rng.normal(size=(600, 2))
points_b = rng.normal(loc=[1.5, 1.0], scale=[0.6, 0.25], size=(600, 2))
ridge_a = np.column_stack([t, 0.2 * np.sin(2 * np.pi * t)])
ridge_b = np.column_stack([t, 0.8 + 0.2 * np.sin(2 * np.pi * t + 0.5)])
```

Validation:

- Point arrays must be finite with shape `(n_points, 2)`.
- KDE contours require enough unique points; duplicate or collinear points can cause singular covariance errors.
- For explanatory plots, low-alpha scatter plus thicker ridge curves usually reads better than dense legends.
- Turn axes off when coordinates have no physical units; keep axes when the user supplies meaningful coordinates.

### Swiss-roll/diffusion matrix panel

Use this for transition matrices, diffusion probabilities, and manifold-neighborhood illustrations.

```python
points = np.column_stack([x, z])
dist = pairwise_distance(points)
P = np.exp(-(dist ** 2) / (2 * sigma ** 2))
P[P < threshold] = 0
P = P / P.sum(axis=1, keepdims=True)
```

Validation:

- Distance and probability matrices must be square with shape `(n_points, n_points)`.
- Row sums must be finite and nonzero before normalization.
- After normalization, each row should sum to 1 within a tolerance such as `1e-6`.
- Keep `n_points` small for publication templates; large all-pairs line drawings can become slow and visually unreadable.

### Shaded sphere and geodesic diagram

Use this for geometry cartoons with sampled points, spherical constraints, or pairwise dispersion arrows.

Validation:

- Keep image/grid resolution finite; 128-256 is often enough for a shaded disk.
- Use clipped square roots for sphere shading to avoid small negative numerical values.
- Keep arrows shortened from endpoints so arrowheads do not cover points.
- Use high-contrast arrow colors and large enough linewidths for PDF export.

## Recipes

### Two-panel distribution plus manifold concept

1. Create `fig, (ax_left, ax_right) = plt.subplots(1, 2, figsize=(18, 5))`.
2. In the left axis, plot 2-3 smooth curves with translucent fills and a single highlighted vertical target.
3. Add an arrow or bracket between two relevant curve values; label the conceptual quantity concisely.
4. In the right axis, draw low-alpha point clouds first, then contour/ridge curves, then highlighted samples or arrows.
5. Use a shared palette so the same semantic group has the same color in both panels.
6. Adjust `wspace` manually after `tight_layout` when text annotations need extra room.

### KDE manifold overlay

1. Generate or receive two `(n, 2)` point clouds.
2. If SciPy is available and there are enough unique points, use `scipy.stats.gaussian_kde` on a grid.
3. Select upper quantile contour levels such as 0.72-0.99 to show dense manifold regions without filling the whole plot.
4. Draw contours at low alpha, then ridge curves and highlighted stars/points at higher z-order.
5. Use axis-free layout unless coordinates have units.

### Swiss-roll plus diffusion matrix

1. Generate or load a 2D manifold point set.
2. Sort points by a known manifold coordinate when showing the transition matrix; this makes the matrix structure readable.
3. Compute a Gaussian transition matrix and threshold tiny values before row normalization.
4. Plot the matrix with a red sequential colormap and no axis ticks.
5. In the paired point-cloud panel, draw only edges above a probability threshold to avoid clutter.
6. Check row normalization and file outputs before handing the figure to the user.

### Shaded sphere with geodesic arrows

1. Draw a shaded disk using a normalized light direction and `imshow`.
2. Place a few deterministic points on or inside the disk.
3. Draw arcs or arrows between points using interpolation; keep arrows thick enough for print.
4. Turn axes off and use a short legend or direct labels only for concepts that are not obvious.
5. Prefer concise annotations in white callout boxes when labels overlap geometry.

### 3D arrow/projection panel

- Use 3D axes only when depth is essential. Otherwise, emulate 3D with shaded 2D geometry for cleaner publication output.
- Hide panes, grids, and ticks for conceptual 3D panels.
- Use explicit view angles and axis limits so reruns are deterministic.
- If arrows disappear behind surfaces, increase z-order, use projection-aware arrow patches, or switch to a 2D schematic.

## Validation checklist

Before final export:

- The script states whether data are synthetic or user-supplied.
- Random seeds are fixed and visible.
- Arrays are finite and expected shapes are asserted.
- Probability matrices are normalized or intentionally unnormalized with a caption reason.
- Optional SciPy/TeX dependencies are checked before use.
- Annotation text is visible and not clipped.
- Axes are removed only when coordinates are conceptual.
- PNG/PDF outputs exist and are non-empty.

## Related runtime files

- [`../scripts/concept_manifold_template.py`](../scripts/concept_manifold_template.py) provides deterministic built-in examples for distribution, manifold, Swiss-roll, and sphere diagrams.
- [`troubleshooting.md`](troubleshooting.md) explains common SciPy, KDE, stochastic, projection, TeX, and export failures.
