# Statistical visualization API reference

This reference covers the ManimML APIs used for decision-tree, MCMC, Gaussian, probability, and matplotlib-image workflows. Prefer construction checks before render commands.

## Import map

```python
# Decision-tree diagram nodes
from manim_ml.decision_tree.decision_tree import DecisionTreeDiagram, DecisionTreeContainer

# Decision surfaces and iris-style plots
from manim_ml.decision_tree.decision_tree_surface import (
    DecisionTreeSurface,
    IrisDatasetPlot,
    compute_decision_areas,
    merge_overlapping_polygons,
)

# MCMC and probability visualizations
from manim_ml.diffusion.mcmc import (
    gaussian_proposal,
    MultidimensionalGaussianPosterior,
    metropolis_hastings_sampler,
    MCMCAxes,
)
from manim_ml.utils.mobjects.probability import GaussianDistribution
from manim_ml.utils.mobjects.plotting import convert_matplotlib_figure_to_image_mobject
```

Do not assume `DecisionTreeSurface` or `IrisDatasetPlot` are re-exported from `manim_ml.decision_tree.decision_tree`; import them from `decision_tree_surface`.

## Decision-tree diagram APIs

### `DecisionTreeDiagram`

```python
DecisionTreeDiagram(
    sklearn_tree,
    feature_names=None,
    class_names=None,
    class_images_paths=None,
    class_colors=[RED, GREEN, BLUE],
)
```

- `sklearn_tree` is usually `DecisionTreeClassifier(...).fit(X, y).tree_`, not the classifier object itself.
- `feature_names` must index every feature used by the tree. For iris two-feature examples, pass the first two iris feature names.
- `class_names` is stored but leaf rendering currently uses images, not text labels.
- `class_images_paths` must contain a path per class because leaf nodes open images with Pillow.
- `class_colors` is used for the rectangle around leaf images.
- Construction creates `tree_group`, `nodes_map`, and `edge_map` and adds the tree group to the object.

Useful attributes after construction:

```python
decision_tree.tree_group      # Manim group containing nodes and edges
decision_tree.nodes_map       # sklearn node index -> Manim node mobject
decision_tree.edge_map        # "parent,child" -> Manim Line
```

Animation notes:

- `Create(decision_tree, traversal_order="bfs")` is intended, but the current BFS expansion path depends on helper code with unresolved branches. Smoke-test it before using it in a production render.
- Static construction plus `FadeIn(decision_tree)` or `self.add(decision_tree)` is safer than relying on the custom `Create` override.
- `create_level_order_expansion_decision_tree(...)` and `make_expand_tree_animation(...)` are not implemented.

### Decision-tree leaf behavior

`LeafNode(display_type="text")` raises `NotImplementedError`. If a user asks for text-only tree leaves, use one of these workarounds:

1. Generate small temporary image icons containing class colors or labels and pass their paths as `class_images_paths`.
2. Build a custom Manim tree mobject with `Text`/`SurroundingRectangle` leaves instead of `DecisionTreeDiagram`.
3. Render the class labels elsewhere in the scene and use icon leaves in the tree.

## Decision-surface APIs

### `compute_decision_areas`

```python
compute_decision_areas(
    tree_classifier,
    maxrange,
    x=0,
    y=1,
    n_features=None,
)
```

- `tree_classifier` is the fitted `DecisionTreeClassifier`, not `.tree_`.
- `maxrange` is `[x_min, x_max, y_min, y_max]`; it clips open-ended tree intervals to finite plot bounds.
- `x` and `y` choose which feature dimensions appear on the 2-D surface.
- `n_features=2` is safest for two-feature iris examples.
- Return value is a NumPy array of rows `[x_left, x_right, y_bottom, y_top, class_index]`.

Recommended check:

```python
rectangles = compute_decision_areas(clf, maxrange, x=0, y=1, n_features=2)
assert rectangles.ndim == 2 and rectangles.shape[1] == 5
assert np.all(np.isfinite(rectangles[:, :4]))
```

### `IrisDatasetPlot`

```python
IrisDatasetPlot(iris)
```

- `iris` is the object returned by `sklearn.datasets.load_iris()`.
- Uses `iris.data[:, 0:2]`, `iris.feature_names`, `iris.target`, and `iris.target_names`.
- Builds `point_group`, `axes_group`, `legend_group`, and `all_group`.
- The custom `Create` override is meant to animate points, axes, and legend.

### `DecisionTreeSurface`

```python
DecisionTreeSurface(tree_clf, data, axes, class_colors=[BLUE, ORANGE, GREEN])
```

- `tree_clf` is a fitted sklearn classifier.
- `data` should be a 2-D array whose first two columns define the plotted feature range.
- `axes` is a Manim `Axes` object; `IrisDatasetPlot(...).axes_group[0]` is the example source pattern.
- `surface_rectangles` contains polygons generated from `compute_decision_areas`.

Known limitations:

- Build and inspect decision rectangles first; surface construction is more fragile than rectangle computation.
- `merge_overlapping_polygons` expects the class color set it knows about and may print debug output.
- The surface object is safest for visual experimentation after a successful construction smoke test.

## MCMC sampler APIs

### `gaussian_proposal`

```python
gaussian_proposal(x, sigma=0.3)
```

Returns `(x_star, qxx)`, where:

- `x_star` is `x + Normal(0, sigma)` with the same dimensionality as `x`.
- `qxx` is `1` because the proposal is symmetric.

### `MultidimensionalGaussianPosterior`

```python
MultidimensionalGaussianPosterior(ndim=2, seed=12345, scale=3, mu=None, var=None)
```

- Callable object: `posterior(x)` returns a log-density.
- If `mu` or `var` is omitted, random values are generated with `seed`.
- For reproducible tiny examples, pass explicit 2-D `mu` and `var` arrays.
- Values outside `(-500, 500)` in every dimension return a large negative log probability.

### `metropolis_hastings_sampler`

```python
metropolis_hastings_sampler(
    log_prob_fn=MultidimensionalGaussianPosterior(),
    prop_fn=gaussian_proposal,
    initial_location=np.array([0, 0]),
    iterations=25,
    warm_up=0,
    ndim=2,
    sampling_seed=1,
)
```

Returns `(samples, warm_up_samples, candidate_samples)`.

Expected shapes for 2-D sampling:

```python
samples.shape == (iterations, 2)
candidate_samples.shape == (iterations, 2)
warm_up_samples.shape == (0,)  # current source behavior even when warm_up > 0
```

The `warm_up` argument exists but warm-up samples are not populated in the current implementation. Do not promise warm-up trace output unless you add your own sampler wrapper.

## MCMC axes and animation APIs

### `MCMCAxes`

```python
MCMCAxes(
    dot_color=BLUE,
    dot_radius=0.02,
    accept_line_color=GREEN,
    reject_line_color=RED,
    line_color=BLUE,
    line_stroke_width=2,
    x_range=[-3, 3],
    y_range=[-3, 3],
    x_length=5,
    y_length=5,
)
```

Constructs a `Group` containing a Manim `Axes` object. Useful methods:

```python
axes.visualize_gaussian_proposal_about_point(mean, cov=None)
axes.make_transition_animation(start_point, end_point, candidate_point, show_dots=True, run_time=0.1)
axes.show_ground_truth_gaussian(distribution)
axes.visualize_metropolis_hastings_chain_sampling(
    log_prob_fn=MultidimensionalGaussianPosterior(),
    prop_fn=gaussian_proposal,
    show_dots=False,
    true_samples=None,
    sampling_kwargs={},
)
```

Important behavior:

- `visualize_metropolis_hastings_chain_sampling` calls the sampler internally.
- Pass `true_samples` when using the full chain animation; the method builds a background density image from those samples.
- Keep `sampling_kwargs={"iterations": 10}` or similarly small for smoke tests.
- Rejected-vs-accepted line coloring is not currently implemented; the transition path treats proposals as accepted for visual line creation.

## Gaussian/probability mobject

```python
GaussianDistribution(
    axes,
    mean=None,
    cov=None,
    dist_theme="gaussian",
    color=ORANGE,
    **kwargs,
)
```

- `axes` must be a Manim `Axes` object.
- `mean` is a 2-D location; default is `[0.0, 0.0]`.
- `cov` is a 2x2 covariance matrix; default is identity.
- `dist_theme="gaussian"` creates layered ellipses; `dist_theme="ellipse"` creates one filled ellipse.
- The implementation compares theme strings by identity. Use literal values or normalize with `"gaussian" if value == "gaussian" else "ellipse"` before passing user input.

## Matplotlib figure conversion

```python
convert_matplotlib_figure_to_image_mobject(fig, dpi=200)
```

- Calls `fig.tight_layout(pad=0)`, draws the canvas, writes PNG data into memory, converts it to a NumPy array, and returns `ImageMobject(image, image_mode="RGB")`.
- Use the Agg backend in headless contexts.
- Close figures after conversion to avoid accumulating memory:

```python
image = convert_matplotlib_figure_to_image_mobject(fig, dpi=120)
plt.close(fig)
```

Avoid examples that download data at runtime. Generate NumPy arrays or use local sklearn toy datasets for repeatable checks.
