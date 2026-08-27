# Statistical visualization workflows

These recipes are self-contained after ManimML is installed. They generate tiny data or icons locally and do not depend on repository example files.

## Workflow 1: Smoke-check the statistical helper

From this sub-skill directory:

```bash
python scripts/build_statistical_visualizations.py --example all --iterations 12 --max-depth 2
```

Expected signals:

- sampler output has `(iterations, 2)` sample and proposal arrays;
- decision-tree diagram constructs with generated class icons;
- decision-area rectangles are finite;
- MCMC axes and Gaussian objects construct without rendering;
- matplotlib-to-image conversion returns a Manim image mobject.

Use the helper before writing a rendered scene so dependency problems appear early.

## Workflow 2: Decision-tree diagram from sklearn iris

`DecisionTreeDiagram` needs image leaves, so this recipe creates tiny class icons in a temporary directory.

```python
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
from PIL import Image, ImageDraw
from sklearn.datasets import load_iris
from sklearn.tree import DecisionTreeClassifier
from manim import BLUE, ORANGE, GREEN, FadeIn, Scene
from manim_ml.decision_tree.decision_tree import DecisionTreeDiagram


def make_class_icons(directory):
    colors = [(70, 130, 180), (255, 165, 0), (60, 179, 113)]
    labels = ["S", "V", "G"]
    paths = []
    for idx, (color, label) in enumerate(zip(colors, labels)):
        image = Image.new("RGB", (48, 48), color)
        draw = ImageDraw.Draw(image)
        draw.text((18, 15), label, fill=(255, 255, 255))
        path = Path(directory) / f"class_{idx}.png"
        image.save(path)
        paths.append(str(path))
    return paths


class TinyDecisionTreeScene(Scene):
    def construct(self):
        iris = load_iris()
        X = iris.data[:, :2]
        y = iris.target
        clf = DecisionTreeClassifier(max_depth=2, max_leaf_nodes=4, random_state=1)
        clf.fit(X, y)

        with TemporaryDirectory() as tmp:
            tree = DecisionTreeDiagram(
                clf.tree_,
                feature_names=iris.feature_names[:2],
                class_names=list(iris.target_names),
                class_images_paths=make_class_icons(tmp),
                class_colors=[BLUE, ORANGE, GREEN],
            )
            tree.move_to([0, 0, 0])
            self.play(FadeIn(tree))  # safer than relying on the custom Create override
```

For a first render, save this scene as your own script and run a low-quality still/video render, for example:

```bash
manim -ql -s my_scene.py TinyDecisionTreeScene
```

### Decision-tree design notes

- Fit the classifier on the same feature subset used by the diagram labels.
- Keep `max_depth` and `max_leaf_nodes` small for readable node layouts.
- Use generated icons when a user asks for class-color leaves but has no image files.
- Use `FadeIn(tree)` or `self.add(tree)` first; only try `Create(tree, traversal_order="bfs")` after a construction smoke test.

## Workflow 3: Compute a decision surface before rendering it

```python
import numpy as np
from sklearn.datasets import load_iris
from sklearn.tree import DecisionTreeClassifier
from manim_ml.decision_tree.decision_tree_surface import compute_decision_areas

iris = load_iris()
X = iris.data[:, :2]
y = iris.target
clf = DecisionTreeClassifier(max_depth=2, max_leaf_nodes=4, random_state=1).fit(X, y)

maxrange = [
    float(X[:, 0].min() - 0.2),
    float(X[:, 0].max() + 0.2),
    float(X[:, 1].min() - 0.2),
    float(X[:, 1].max() + 0.2),
]
rectangles = compute_decision_areas(clf, maxrange, x=0, y=1, n_features=2)

assert rectangles.shape[1] == 5
assert np.all(np.isfinite(rectangles[:, :4]))
```

Rows are `[x_left, x_right, y_bottom, y_top, class_index]`. Once these rectangles are finite, you can convert them to Manim polygons yourself or experiment with `DecisionTreeSurface` against a known-good `Axes` object.

## Workflow 4: Iris dataset plot and optional surface

```python
from sklearn.datasets import load_iris
from sklearn.tree import DecisionTreeClassifier
from manim import Create, Scene
from manim_ml.decision_tree.decision_tree_surface import IrisDatasetPlot, DecisionTreeSurface


class IrisSurfaceScene(Scene):
    def construct(self):
        iris = load_iris()
        plot = IrisDatasetPlot(iris)
        self.play(Create(plot))

        X = iris.data[:, :2]
        clf = DecisionTreeClassifier(max_depth=2, max_leaf_nodes=4, random_state=1).fit(X, iris.target)
        surface = DecisionTreeSurface(clf, iris.data, plot.axes_group[0])
        self.play(Create(surface))
```

This scene follows the package workflow, but surface rendering is less robust than raw rectangle computation. If it fails, fall back to Workflow 3 and create explicit polygons from the returned rectangles.

## Workflow 5: Metropolis-Hastings sampler smoke test

```python
import numpy as np
from manim_ml.diffusion.mcmc import (
    MultidimensionalGaussianPosterior,
    gaussian_proposal,
    metropolis_hastings_sampler,
)

posterior = MultidimensionalGaussianPosterior(
    ndim=2,
    mu=np.array([0.0, 0.0]),
    var=np.array([1.0, 1.0]),
)
samples, warmup, proposals = metropolis_hastings_sampler(
    log_prob_fn=posterior,
    prop_fn=gaussian_proposal,
    initial_location=np.array([0.0, 0.0]),
    iterations=15,
    warm_up=5,
    ndim=2,
    sampling_seed=7,
)

assert samples.shape == (15, 2)
assert proposals.shape == (15, 2)
assert warmup.shape == (0,)  # current implementation does not return warm-up samples
```

Use this when the user wants numerical samples or a fast dependency check. Keep iteration counts small before rendering an animation.

## Workflow 6: MCMC axes and Gaussian proposal animation

```python
import numpy as np
from manim import Create, Scene
from manim_ml.diffusion.mcmc import MCMCAxes


class MCMCProposalScene(Scene):
    def construct(self):
        axes = MCMCAxes(x_range=[-3, 3], y_range=[-3, 3], x_length=5, y_length=5)
        self.play(Create(axes))
        proposal = axes.visualize_gaussian_proposal_about_point(
            mean=np.array([0.0, 0.0]),
            cov=np.eye(2) * 0.4,
        )
        self.play(proposal)
```

This validates axes/probability mobject construction without building a long chain animation.

## Workflow 7: Tiny MCMC chain animation with a true-sample background

```python
import numpy as np
import scipy.stats
from manim import Create, Scene
from manim_ml.diffusion.mcmc import MCMCAxes


def mixture_logpdf(x):
    left = scipy.stats.multivariate_normal(mean=[-0.5, -0.5], cov=[1.0, 1.0]).pdf(x)
    right = scipy.stats.multivariate_normal(mean=[1.8, 1.5], cov=[0.35, 0.35]).pdf(x)
    return np.log(left + right + 1e-12)


class TinyMCMCChainScene(Scene):
    def construct(self):
        rng = np.random.default_rng(4)
        true_samples = np.vstack([
            rng.multivariate_normal([-0.5, -0.5], np.eye(2), size=80),
            rng.multivariate_normal([1.8, 1.5], np.eye(2) * 0.35, size=80),
        ])

        axes = MCMCAxes(x_range=[-4, 4], y_range=[-4, 4], x_length=6, y_length=6)
        self.play(Create(axes))
        animation = axes.visualize_metropolis_hastings_chain_sampling(
            log_prob_fn=mixture_logpdf,
            true_samples=true_samples,
            sampling_kwargs={
                "iterations": 15,
                "initial_location": np.array([-3.0, 3.0]),
                "sampling_seed": 4,
            },
        )
        self.play(animation)
```

Render only after checking that construction completes. The background density conversion uses matplotlib/seaborn and can dominate runtime for larger sample counts.

## Workflow 8: Standalone GaussianDistribution overlay

```python
import numpy as np
from manim import Axes, Create, Scene
from manim_ml.utils.mobjects.probability import GaussianDistribution


class GaussianOverlayScene(Scene):
    def construct(self):
        axes = Axes(x_range=[-3, 3], y_range=[-3, 3], x_length=5, y_length=5, tips=False)
        gaussian = GaussianDistribution(
            axes,
            mean=np.array([0.5, -0.25]),
            cov=np.array([[1.2, 0.25], [0.25, 0.6]]),
            dist_theme="gaussian",
        )
        self.play(Create(axes), Create(gaussian))
```

If user input controls `dist_theme`, normalize it to a literal supported value before passing it to ManimML:

```python
theme = "ellipse" if user_theme == "ellipse" else "gaussian"
```

## Workflow 9: Matplotlib or seaborn figure as an ImageMobject

```python
import matplotlib
matplotlib.use("Agg", force=True)
import matplotlib.pyplot as plt
import numpy as np
from manim import Scene
from manim_ml.utils.mobjects.plotting import convert_matplotlib_figure_to_image_mobject


class MatplotlibImageScene(Scene):
    def construct(self):
        rng = np.random.default_rng(0)
        points = rng.normal(size=(100, 2))
        fig, ax = plt.subplots(figsize=(3, 3), dpi=100)
        ax.scatter(points[:, 0], points[:, 1], s=8)
        ax.axis("off")
        image = convert_matplotlib_figure_to_image_mobject(fig, dpi=120)
        plt.close(fig)
        self.add(image)
```

Avoid `seaborn.load_dataset(...)` in reusable scripts because it may rely on external data availability. Generate arrays locally or use sklearn toy datasets.
