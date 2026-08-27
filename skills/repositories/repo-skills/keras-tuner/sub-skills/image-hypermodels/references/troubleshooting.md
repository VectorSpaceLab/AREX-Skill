# Image Hypermodels Troubleshooting

## Constructor validation

### `You must specify either input_shape or input_tensor.`

All four constructors require at least one input source. Supply an image shape
without a batch dimension or a Keras tensor. If both are present,
`input_tensor` wins; mismatched redundant values are a common source of
confusion.

### `You must specify classes` / `You must specify classes when include_top=True`

ResNet and Xception require `classes` only when `include_top=True`. Set
`include_top=False` for a feature extractor. EfficientNet has no
`include_top=False` mode and always requires a truthy `classes`; `None` and `0`
are rejected by the current implementation.

### Invalid `augmentation_model`

EfficientNet accepts only `None`, a Keras `Model`, or a `HyperModel`. Wrap a
preprocessing layer in a functional/sequential Keras model, or implement a
`HyperModel.build(hp)` method. A bare layer, callable, integer, or unrelated
object is not an accepted value.

## Shape and backend failures

- Print `keras.backend.image_data_format()` and construct `input_shape` with
  the matching channel position. Do not copy a channels-last fixture into a
  channels-first backend.
- `input_shape` does not include `(batch,)`. For an `input_tensor`, inspect the
  tensor's actual shape instead of trusting a separately supplied shape.
- ResNet and Xception contain repeated striding. Very small spatial dimensions
  can fail or create unusable feature maps; retry with a bounded 64x64 or
  128x128 fixture before debugging the search space.
- Assert model input identity for tensor workflows and assert the output shape
  before fitting. For classifier models it should be `(None, classes)`.
- A feature extractor (`include_top=False`) and `HyperImageAugment` are not
  expected to have an optimizer. EfficientNet and top-included ResNet/Xception
  are compiled by their builders.

## Hyperparameter conflicts and defaults

A value pre-registered in `hp` must be compatible with the exact name and
range requested by the builder. Use the names in `api-reference.md`, not names
from a different KerasTuner release. For targeted checks, `hp.Fixed` is clearer
than mutating `hp.values` directly.

Current augmentation names are `augment_layers` and `factor_rotate`,
`factor_translate_x`, `factor_translate_y`, and `factor_contrast`. Some older
repository test expectations mention `randaug_count` and `randaug_mag`; those
names are not read by the current implementation and should not be used in new
workflows.

Similarly, a few legacy augmentation test comments describe a default zero
RandAugment count, while the current constructor's default `augment_layers=3`
creates a range `[1, 3]` whose effective default is `1`. Prefer the installed
signature and implementation behavior when code and stale comments disagree.

## Augmentation argument errors

- Use `None` to exclude a transform. A scalar `x` means `[0, x]`; a two-value
  sequence means `[lo, hi]`.
- More than two values raise `ValueError`; nonnumeric endpoints raise
  `ValueError`. A one-value sequence is not a supported range and may produce
  an indexing error rather than a friendly validation message.
- The implementation's checks are not a complete `[0, 1]` validator. Reject
  negative, over-one, reversed, or non-finite factors in caller code.
- Truthy `augment_layers` must be an integer or a two-integer sequence. Use
  `0`/`None` for fixed sequential mode. A positive integer `n` means the
  current implementation searches `[1, n]`, not `[0, n]`.
- If a factor is fixed at zero, its transform layer is skipped in fixed mode.
  In RandAugment-like mode, a zero factor makes that transform a no-op even if
  it is selected.

## EfficientNet weight/download and offline failures

`HyperEfficientNet` calls Keras Applications EfficientNet without passing
`weights`. With the installed Keras API, that defaults to ImageNet weights.
The first build can therefore be networked and B1--B7 can consume substantial
memory after resizing. The hypermodel does not expose a `weights=None` escape
hatch.

Use this recovery sequence:

1. Stop an automatic or unbounded build rather than repeatedly retrying a
   download.
2. Check whether the expected Keras weight cache is populated and whether the
   environment permits the download host.
3. Retry explicitly with B0, a small input, an external timeout, and a small
   trial budget only after approval.
4. If offline, skip EfficientNet and verify the augmentation/ResNet/Xception
   paths instead. If a no-weight EfficientNet is a hard requirement, construct
   the underlying Keras Application separately with its own explicit weight
   policy rather than claiming that this hypermodel supports it.

Do not make a smoke script or import check silently fetch weights.

## Slow builds, OOM, or stalled tests

- Start with feature extractors and B0; do not run all ResNet/Xception variants
  as a first check.
- Reduce batch size and synthetic data before changing architecture choices.
- Limit `max_trials`, use an external process timeout, and log the selected
  `hp.values` so a failed trial is reproducible.
- The original application tests skip some model-construction cases when the
  multi-backend mode is active or when builds are too slow. A skipped test is
  not evidence that the public signature changed.
- On a CPU-only host, CUDA initialization warnings are not necessarily a model
  failure. Distinguish them from a real shape, import, compile, or download
  exception.

## Compile and output surprises

Top-included ResNet/Xception compile with categorical cross-entropy and
accuracy. EfficientNet compiles with SGD (momentum `0.1`) and the same loss and
metric. If labels are integer class ids, choose an appropriate loss in a
subclass or training wrapper; do not assume the built-in categorical loss will
accept a different label encoding.

`HyperImageAugment` preserves image shape and is intended to be composed into a
larger model; it is not a classifier. Inference-time preprocessing layers may
behave deterministically, so a no-op-looking prediction is not by itself proof
that the search-space registration failed. Inspect `hp.values` and the model
layers as well.
