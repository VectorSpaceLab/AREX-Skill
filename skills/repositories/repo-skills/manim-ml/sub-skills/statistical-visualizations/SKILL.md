---
name: statistical-visualizations
description: "Build and troubleshoot ManimML statistical, probability,
  decision-tree, MCMC, Gaussian, and matplotlib-image visualizations with safe
  CPU-first recipes."
disable-model-invocation: true
metadata:
  disco-role: operating
  package: manim_ml
  sub-skill-role: statistical-probability-visualization
license: MIT
---

# Statistical visualizations with ManimML

Use this sub-skill when a task asks for ManimML scenes or helper code involving statistical or probability visualizations:

- scikit-learn decision-tree diagrams from a fitted `DecisionTreeClassifier.tree_`.
- Iris-style two-feature scatter plots and decision-surface overlays.
- Metropolis-Hastings sampling checks, MCMC axes, and compact chain animations.
- 2-D Gaussian/probability mobjects.
- Converting matplotlib/seaborn figures into Manim `ImageMobject` objects.

Route neural-network layer diagrams, forward-pass animations, dropout, and CNN/image-layer workflows to the `neural-network-visualization` sub-skill instead.

## Required runtime assumptions

The target Python environment should import Manim Community, ManimML, NumPy, Pillow, SciPy, matplotlib, seaborn, scikit-learn, and tqdm. These workflows are CPU workflows. Full video rendering is optional and may additionally require the usual Manim system rendering stack.

For headless execution, set matplotlib to the Agg backend before creating figures:

```python
import matplotlib
matplotlib.use("Agg", force=True)
```

## First checks

Run the bundled helper from this sub-skill directory to verify package-level construction without rendering:

```bash
python scripts/build_statistical_visualizations.py --help
python scripts/build_statistical_visualizations.py --example sampler --iterations 12
python scripts/build_statistical_visualizations.py --example decision-tree --max-depth 2
```

`--example all` runs the compact sampler, decision-tree, MCMC axes, Gaussian, and matplotlib-image construction checks. These checks synthesize their own tiny data or icons and do not require repository example assets.

## Capability map

| Need | Use | Details |
| --- | --- | --- |
| Fitted scikit-learn tree diagram | `DecisionTreeDiagram(sklearn_tree, feature_names=..., class_images_paths=...)` | Leaves require image paths in the current implementation. Use generated temporary icons or caller-provided class images. |
| Decision areas over a 2-D feature plane | `compute_decision_areas(tree_classifier, maxrange, x=0, y=1, n_features=2)` | Compute rectangles first; only build a Manim surface after confirming finite ranges and compatible axes. |
| Iris-style dataset scatter | `IrisDatasetPlot(iris)` | Designed for sklearn's iris object and the first two features. Treat full rendering as optional. |
| Metropolis-Hastings sampler | `metropolis_hastings_sampler(...)` | Required smoke path. Returns samples, an empty warm-up array, and proposals. |
| MCMC axes/animations | `MCMCAxes(...)` | Construct axes and proposal/chain animations with tiny iteration counts before rendering. |
| Gaussian probability overlay | `GaussianDistribution(axes, mean=..., cov=..., dist_theme="gaussian")` | Use 2-D mean/covariance matching the axes. |
| Matplotlib figure as Manim image | `convert_matplotlib_figure_to_image_mobject(fig, dpi=...)` | Use Agg, close figures after conversion, and avoid remote datasets. |

## Safe operating pattern

1. Decide whether the output is only a static Manim object, an animation object, or a rendered video/still.
2. Keep data tiny for construction checks: two iris features, shallow trees, 10-25 MCMC iterations, and small generated icons/images.
3. Import `DecisionTreeSurface` and `IrisDatasetPlot` from `manim_ml.decision_tree.decision_tree_surface`; do not rely on outdated re-export assumptions.
4. For decision-tree leaves, provide three valid image files when using the iris classifier. If no real images are available, generate simple colored square icons.
5. For MCMC animation construction, provide `true_samples` if calling `visualize_metropolis_hastings_chain_sampling`; it builds a background density image.
6. Render only after construction succeeds. Prefer Manim low quality (`-ql`) or still-image (`-s`) flags for first renders.

## Reference files

- `references/api-reference.md` - public API signatures, return expectations, and source limitations.
- `references/workflows.md` - self-contained decision-tree, MCMC, Gaussian, and matplotlib recipes.
- `references/troubleshooting.md` - common errors and recovery steps.
- `scripts/build_statistical_visualizations.py` - CPU-first smoke helper with no default render step.
