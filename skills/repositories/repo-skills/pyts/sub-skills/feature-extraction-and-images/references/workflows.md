# Feature, Image, and SSA Workflows

## When to read

Read this when the task is to extract features, transform a series into an
image, or decompose it into SSA components.

## Common recipes

### 1. Feature extraction for classification

Use `BagOfPatterns`, `BOSS`, `ROCKET`, `ShapeletTransform`, or `WEASEL` when
you want a transformer that outputs a feature matrix for a downstream model.

```python
from pyts.transformation import ROCKET
X_feat = ROCKET(n_kernels=16, kernel_sizes=(3, 5, 7), random_state=0).fit_transform(X)
```

The bundled smoke script confirms the tiny-array shapes for BagOfPatterns,
BOSS, ROCKET, ShapeletTransform, and WEASEL.

### 2. Image transforms

Use the image transformers when a 2D representation is more useful than a raw
feature vector.

```python
from pyts.image import GramianAngularField, MarkovTransitionField, RecurrencePlot
X_gaf = GramianAngularField(image_size=4).transform([[0, 1, 2, 3]])
X_mtf = MarkovTransitionField(image_size=4).fit_transform([[0, 1, 2, 3]])
X_rp = RecurrencePlot(dimension=2, time_delay=1, flatten=True).transform([[0, 1, 2, 3]])
```

### 3. SSA decomposition

Use `SingularSpectrumAnalysis` when you need a decomposition into component
series rather than a classifier-ready feature matrix.

```python
from pyts.decomposition import SingularSpectrumAnalysis
X_ssa = SingularSpectrumAnalysis(window_size=2).transform([[0, 1, 2, 3]])
```

## Shape and cost notes

- `ROCKET` defaults to large kernel sizes; shrink them for tiny smoke arrays.
- `ShapeletTransform` can be expensive even on small data, so keep the smoke
  fixture tiny and fix `random_state`.
- `WEASEL` is sensitive to `word_size`, `window_sizes`, `drop_sum`, and
  `chi2_threshold`; tune those together when a tiny example returns an empty
  feature matrix.
- `GramianAngularField`, `MarkovTransitionField`, and `RecurrencePlot` all
  return image-like arrays; `RecurrencePlot(flatten=True)` becomes a feature
  vector.

## Cross-links

- Use `../preprocessing-and-symbols/SKILL.md` for the symbolic building blocks
  that feed these transformers.
- Use `../metrics-and-classifiers/SKILL.md` after feature extraction if the
  next step is to score or classify.
- Use `../multivariate-workflows/SKILL.md` for multivariate extensions of the
  image and transformation ideas.
