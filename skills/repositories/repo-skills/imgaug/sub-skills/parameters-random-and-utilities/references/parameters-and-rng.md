# Parameters and RNG

## Read this when

You need to choose stochastic parameter forms, make augmentation reproducible, or explain imgaug's random sampling behavior.

## Parameter forms

Most augmenters accept flexible parameter inputs:

| Form | Meaning |
| --- | --- |
| Scalar number | Fixed deterministic value. |
| Tuple `(a, b)` | Uniform draw between two bounds for many continuous/discrete parameters. |
| List `[a, b, c]` | Choice among listed values for many parameters. |
| `StochasticParameter` | Explicit distribution object from `imgaug.parameters`. |

## Verified constructors

- `Choice(a, replace=True, p=None)`
- `Uniform(a, b)`
- `Normal(loc, scale)`
- `Clip(other_param, minval=None, maxval=None)`
- `RNG(generator)`
- `RNG.integers(low, high=None, size=None, dtype='int32', endpoint=False)`
- `imgaug.seed(entropy=None, seedval=None)`
- `imgaug.random.seed(entropy)`

## Examples

```python
import imgaug.augmenters as iaa
import imgaug.parameters as iap

# Shortcut: sampled uniformly.
aug = iaa.GaussianBlur((0.0, 3.0))

# Explicit distribution: normal samples clipped to a safe blur range.
sigma = iap.Clip(iap.Normal(1.0, 0.1), 0.1, 3.0)
aug = iaa.GaussianBlur(sigma=sigma)

# List/choice style.
aug = iaa.Affine(rotate=[-15, 0, 15])
```

## Reproducibility choices

- Use `seed=` on augmenters when constructing a reusable pipeline with controlled randomness.
- Use `to_deterministic()` when two or more separate calls need the exact same sampled transform.
- For images plus annotations, prefer one call containing every aligned augmentable. It avoids needing to replay random state manually.
- Avoid older `random_state=` and `deterministic=` arguments unless maintaining legacy code; they are present in signatures but deprecated.

## Common caveats

- Randomness is consumed as augmenters run; changing pipeline order or adding an augmenter changes later samples.
- Some stochastic parameters prefetch samples for speed, so direct low-level sampling may not behave like a simple NumPy call.
- NumPy 1.17 introduced a new random generator style. imgaug wraps NumPy generators through its `RNG` class to bridge old/new APIs.
