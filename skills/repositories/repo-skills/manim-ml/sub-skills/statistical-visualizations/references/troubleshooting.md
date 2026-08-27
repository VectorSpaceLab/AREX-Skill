# Statistical visualization troubleshooting

Use this guide when ManimML statistical/probability scenes fail during import, object construction, or rendering.

## Quick diagnosis order

1. Confirm the environment imports Manim Community and ManimML.
2. Run `python scripts/build_statistical_visualizations.py --example sampler --iterations 12`.
3. Run `python scripts/build_statistical_visualizations.py --example decision-tree --max-depth 2`.
4. If matplotlib or seaborn is involved, force the Agg backend before importing `pyplot`.
5. Only render after object construction succeeds.

## Decision-tree failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `FileNotFoundError` from Pillow while constructing leaves | `DecisionTreeDiagram` leaf nodes require image paths. | Generate small class-icon images or pass valid caller-provided image paths via `class_images_paths`. |
| `NotImplementedError` from `LeafNode(display_type="text")` | Text leaves are declared but not implemented. | Use image-icon leaves, or create a custom tree mobject with `Text` leaves. |
| `TypeError` or indexing errors from feature names | Tree was fit on more/different features than the provided `feature_names`. | Fit on the same feature subset you label, or pass names for every feature index used by the tree. |
| Tree is too wide or unreadable | Deep sklearn tree creates many Manim nodes. | Use `max_depth`, `max_leaf_nodes`, smaller node text, or split the explanation across scenes. |
| Custom `Create(decision_tree, traversal_order="bfs")` fails | The custom expansion path has unresolved helper branches. | Use `FadeIn(decision_tree)` or `self.add(decision_tree)` first; only use the BFS animation after a smoke test. |
| Importing `DecisionTreeSurface` from `manim_ml.decision_tree.decision_tree` fails | Surface classes are in a separate module. | Import from `manim_ml.decision_tree.decision_tree_surface`. |

## Decision-surface failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Non-finite or empty rectangles | `maxrange` is wrong or the tree/data dimensionality does not match `x`, `y`, and `n_features`. | Compute finite bounds from the plotted data and pass `n_features=2` for two-feature iris-style examples. |
| Surface polygons render outside axes | Coordinates were computed against one feature range but displayed on different axes. | Build the `Axes` from the same data range used for `compute_decision_areas`. |
| Merge/polygon errors | `merge_overlapping_polygons` is color-set and geometry sensitive. | Skip merging; create one translucent polygon per rectangle for a more robust custom surface. |
| Surface object constructs but `Create(surface)` fails | The surface workflow is less robust than raw rectangle computation. | Verify rectangles first; use explicit `Polygon` objects in your scene if the packaged surface path fails. |

## MCMC sampler and animation failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `samples.shape` is not expected | `iterations` or `ndim` differs from the asserted shape. | For 2-D examples, pass `initial_location=np.array([0.0, 0.0])`, `iterations=N`, and `ndim=2`. |
| Warm-up output is empty despite `warm_up > 0` | Current sampler returns `np.array([])` for warm-up samples. | Treat `warm_up` as a non-output argument; if warm-up traces matter, implement a wrapper sampler. |
| Chain animation fails when building density background | `true_samples` is missing or too small/invalid for the seaborn KDE plot. | Pass a generated `(n, 2)` array, use at least dozens of samples, or use a simpler background image. |
| MCMC render is slow | Too many iterations, too many true samples, or high-quality Manim render settings. | Start with 10-25 iterations, <=200 true samples, and low-quality/still render flags. |
| Accepted and rejected proposals are not visually distinguished | Transition logic currently treats transitions as accepted for line creation. | If rejected transitions must be shown, post-process sampler outputs and write custom line coloring. |

## GaussianDistribution failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `Uncrecognized distribution theme` for a valid-looking theme | The implementation compares strings by identity. | Normalize user input to the literal `"gaussian"` or `"ellipse"` before constructing. |
| Ellipse size/orientation looks wrong | Covariance matrix is not 2x2 positive semidefinite or does not match axes scale. | Use a symmetric 2x2 covariance and test with identity covariance first. |
| Gaussian is off-screen | Mean is outside the axes range. | Align `mean` with `Axes(x_range=..., y_range=...)`. |

## Matplotlib-to-image failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Backend/display error in headless runs | Matplotlib chose an interactive backend. | Call `matplotlib.use("Agg", force=True)` before importing `matplotlib.pyplot`. |
| Figure is blank or clipped | Figure was closed too early or layout has no visible artists. | Convert before `plt.close(fig)`, call `ax.axis("off")` only after plotting, and check the figure manually with a tiny local save if needed. |
| Memory grows over repeated conversions | Figures are not closed. | Call `plt.close(fig)` after `convert_matplotlib_figure_to_image_mobject`. |
| `seaborn.load_dataset` fails | Example depends on external dataset access/cache. | Generate NumPy arrays locally or use sklearn toy datasets already shipped with scikit-learn. |

## Manim rendering issues

Construction checks do not guarantee rendering. If a scene imports and constructs but rendering fails:

- Confirm you installed Manim Community rather than an incompatible Manim package.
- Try a low-quality still render first: `manim -ql -s my_scene.py SceneName`.
- Avoid LaTeX-dependent labels unless the system has a TeX installation.
- Reduce scene complexity: shallow trees, fewer MCMC iterations, lower DPI matplotlib images.
- If text/font warnings appear, use default fonts or simplify labels.

## Known source limitations to document in user-facing code

- Text leaves for decision-tree diagrams are not implemented.
- Level-order decision-tree expansion and several tree/surface synchronization helpers are stubs.
- The BFS tree expansion helper has unresolved variable paths; static display is safer.
- `metropolis_hastings_sampler` accepts `warm_up` but returns an empty warm-up array.
- MCMC chain visualization builds a density image from `true_samples`; do not call it without sample data.
- Gaussian theme selection is sensitive to exact string handling.
