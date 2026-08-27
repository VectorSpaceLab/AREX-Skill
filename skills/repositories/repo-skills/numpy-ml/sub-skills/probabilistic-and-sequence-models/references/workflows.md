# Workflows

## Tiny GMM example

```python
import numpy as np
from numpy_ml.gmm import GMM

rng = np.random.RandomState(1)
X = np.vstack([rng.normal(0, 0.1, (5, 2)), rng.normal(2, 0.1, (5, 2))])
model = GMM(C=2, seed=1)
model.fit(X, max_iter=2, verbose=False)
print(model.predict(X[:2]))
```

Keep the array small and well separated so cluster assignments are easy to inspect.

## Tiny HMM example

```python
import numpy as np
from numpy_ml.hmm import MultinomialHMM

A = np.array([[0.7, 0.3], [0.2, 0.8]])
B = np.array([[0.6, 0.4], [0.1, 0.9]])
pi = np.array([0.5, 0.5])
model = MultinomialHMM(A=A, B=B, pi=pi)
print(model.log_likelihood(np.array([0, 1, 1])))
```

Use a NumPy observation vector. If the implementation complains about `.ndim`,
a raw Python list is usually the problem.

## Tiny n-gram workflow

```python
import tempfile
from numpy_ml.ngram import AdditiveNGram

with tempfile.NamedTemporaryFile('w', delete=False) as f:
    f.write('a tiny corpus\na tiny test corpus\n')
    path = f.name

model = AdditiveNGram(2, K=1, filter_stopwords=False, filter_punctuation=True)
model.train(path)
print(model.log_prob(['a', 'tiny'], 2))
```

Use this route when the task is about corpus scoring rather than arbitrary text
processing. If tokenization or cleanup is needed first, go to the preprocessing
sub-skill.

## Workflow advice

1. Use the smallest possible synthetic data.
2. Verify probability shapes and probability-mass assumptions before fitting.
3. Fit in place; do not expect `fit(...)` to return a model object.
4. Use the bundled smoke helper after editing example code or switching Python
   versions.
