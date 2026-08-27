# API Reference

## Constructors

- `GMM(C=3, seed=None)`
- `MultinomialHMM(A=None, B=None, pi=None, eps=None)`
- `LDA(T=10)`
- `SmoothedLDA(T, **kwargs)`
- `MLENGram(N, unk=True, filter_stopwords=True, filter_punctuation=True)`
- `AdditiveNGram(N, K=1, unk=True, filter_stopwords=True, filter_punctuation=True)`
- `GoodTuringNGram(N, conf=1.96, unk=True, filter_stopwords=True, filter_punctuation=True)`

## Behavior notes

### GMM

- Train on small 2D NumPy arrays.
- The model stores learned mixture state on the instance after `fit`.
- `predict(X)` returns cluster- or component-related outputs, depending on the call path used by the model.

### HMM

- Provide valid transition, emission, and initial probability matrices when building a supervised model.
- Sequence methods expect NumPy arrays or array-like integer observation sequences.
- `log_likelihood(...)` should receive a numeric observation sequence, not a raw Python list when the implementation checks `.ndim`.

### LDA

- Topic count `T` is the primary control knob.
- `SmoothedLDA` accepts additional keyword controls for the smoothed/MAP variant.
- Use a document-term style representation and keep the corpus size tiny for smoke tests.

### n-gram models

- `train(corpus_fp, vocab=None, encoding=None)` reads from a corpus file path.
- `log_prob(words, N)` expects a token sequence with at least `N` words.
- Use preprocessing helpers for tokenization, stop-word filtering, and punctuation handling before training when needed.

## Validation hints

- For probability matrices, check row sums and shapes before training.
- For sequences, keep observation IDs consistent and numeric.
- For language models, use tiny text files and deterministic tokenization in smoke checks.
- If you need corpus cleanup, route that work to the preprocessing sub-skill rather than duplicating it here.
