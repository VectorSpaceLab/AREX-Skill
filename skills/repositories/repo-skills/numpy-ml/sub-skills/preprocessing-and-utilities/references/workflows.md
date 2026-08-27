# Workflows

## Tabular preprocessing

```python
import numpy as np
from numpy_ml.preprocessing.general import Standardizer, OneHotEncoder, FeatureHasher

X = np.array([[1.0, 2.0], [3.0, 4.0]])
scaler = Standardizer()
scaler.fit(X)
print(scaler.transform(X))

encoder = OneHotEncoder()
y = encoder.transform(['red', 'blue', 'red'])
print(y)
print(encoder.inverse_transform(y))

hasher = FeatureHasher(n_dim=8, sparse=True)
H = hasher.encode([{'red': 1, 'round': 1}, {'blue': 1}])
print(H.shape)
```

After this step, route the prepared arrays to a model sub-skill such as
`../../supervised-and-tabular-models/SKILL.md`.

## Text preprocessing

```python
from numpy_ml.preprocessing.nlp import tokenize_words, Vocabulary, TFIDFEncoder

text = 'Hello, tiny World!'
tokens = tokenize_words(text, filter_stopwords=False)
print(tokens)

vocab = Vocabulary(filter_stopwords=False, filter_punctuation=True)
# Fit/train methods depend on the corpus representation; keep a tiny file or
# list of lines and inspect the object state after training.
```

Use this route to normalize text before n-gram or Word2Vec workflows.

## Signal and kernel utilities

```python
import numpy as np
from numpy_ml.preprocessing.dsp import DFT, DCT
from numpy_ml.utils.kernels import RBFKernel
from numpy_ml.utils.distance_metrics import euclidean

signal = np.array([1.0, 0.0, -1.0, 0.0])
print(DFT(signal))
print(DCT(signal))

X = np.array([[1.0, 2.0]])
Y = np.array([[3.0, 4.0]])
print(RBFKernel(sigma=1)(X, Y))
print(euclidean(X[0], Y[0]))
```

## Data structures and graphs

Use `PriorityQueue`, `BallTree`, and graph helpers for tiny algorithmic
experiments. Validate return types directly; for example, `PriorityQueue.pop()`
returns a dict with keys such as `key`, `val`, and `priority`.
