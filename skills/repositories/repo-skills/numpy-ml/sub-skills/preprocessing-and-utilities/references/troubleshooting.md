# Troubleshooting

## `OneHotEncoder` has no `fit_transform`

Use `transform(labels, categories=None)`. On first use it creates the category
mapping. Then call `inverse_transform(Y)` if you need labels back.

## Unknown label assertion

If `OneHotEncoder` is already fit and new labels appear, transform raises an
assertion. Refit with the full category list or handle unknown labels before
encoding.

## `FeatureHasher` method or sparse errors

Call `FeatureHasher.encode(...)`, not `transform`. Provide feature dictionaries
such as `{'token': 1}`. Prefer `sparse=True` with SciPy installed. If sparse
matrix construction is not wanted, test dense mode explicitly because this
legacy snapshot has less coverage there.

## MFCC/audio parameter problems

MFCC expects a numeric waveform and sampling-rate assumptions. Use tiny arrays
for smoke tests. Install optional audio comparison libraries only when running
original comparison tests; the base package uses NumPy/SciPy routines.

## Kernel or distance mismatch

Make sure inputs are arrays of compatible length and shape. Kernel classes are
callable; distance functions consume two 1D vectors.

## Graph/networkx comparison failures

NetworkX is only a comparison-test dependency. The utility graph classes can be
used without it; install NetworkX only for native test comparison work.

## Legacy version drift

This snapshot is sensitive to newer Python and NumPy versions. If a utility
fails before your own logic runs, check root compatibility before debugging the
specific preprocessing call.
