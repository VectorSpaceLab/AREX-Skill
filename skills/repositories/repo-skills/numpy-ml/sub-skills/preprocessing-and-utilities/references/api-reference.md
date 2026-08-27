# API Reference

## General preprocessing

- `Standardizer(with_mean=True, with_std=True)`
  - `fit(X)` stores feature-wise mean/std.
  - `transform(X)` returns standardized data.
  - `inverse_transform(Z)` reverses scaling.
- `OneHotEncoder()`
  - `transform(labels, categories=None)` fits categories lazily if needed and returns a dense one-hot matrix.
  - `inverse_transform(Y)` maps one-hot rows back to labels.
  - There is no `fit_transform` method in this snapshot.
- `FeatureHasher(n_dim=256, sparse=True)`
  - `encode(examples)` accepts a dict or list of dicts mapping feature IDs to numeric values.
  - Prefer `sparse=True` when SciPy is available.

## NLP preprocessing

- `tokenize_words(line, lowercase=True, filter_stopwords=True, filter_punctuation=True, **kwargs)`
- `Vocabulary(lowercase=True, min_count=None, max_tokens=None, filter_stopwords=True, filter_punctuation=True, tokenizer='words')`
- `TFIDFEncoder(vocab=None, lowercase=True, min_count=0, smooth_idf=True, max_tokens=None, input_type='files', filter_stopwords=True, filter_punctuation=True, tokenizer='words')`
- `BytePairEncoder(max_merges=3000, encoding='utf-8')`
- `HuffmanEncoder()`

## DSP and signal utilities

- `DFT(frame, positive_only=True)`
- `DCT(frame, orthonormal=True)`
- `mfcc(x, fs=44000, n_mfccs=13, alpha=0.95, center=True, n_filters=20, window='hann', normalize=True, lifter_coef=22, stride_duration=0.01, window_duration=0.025, replace_intercept=True)`

Other utilities include interpolation, framing, autocorrelation, power/magnitude
spectra, Mel conversions, and filter banks.

## Kernels, distances, and data structures

- Kernels: `LinearKernel(c0=0)`, `PolynomialKernel(d=3, gamma=None, c0=1)`, `RBFKernel(sigma=None)`, `KernelInitializer(param=None)`.
- Distances: `euclidean`, `manhattan`, `chebyshev`, `minkowski`, `hamming`.
- Data structures: `PriorityQueue(capacity, heap_order='max')`, `BallTree(leaf_size=40, metric=None)`, `DiscreteSampler(probs, log=False, with_replacement=True)`, `Dict(encoder=None)`.
- Graph helpers live under the utility graph module and are useful for DAG and path experiments.

## Method-name gotchas

- `PriorityQueue.pop()` returns a dictionary, not a node object.
- `FeatureHasher.encode(...)` is the public transformation method.
- `OneHotEncoder.transform(...)` may fit categories on first use.
