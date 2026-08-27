# Pipeline Recipes

## Purpose

Read this when you need the supported CogDL `pipeline()` app names and the
smallest safe recipe for each one.

## Verified application registry

The inspected checkout exposes five public apps in `SUPPORTED_APPS`:

- `dataset-stats`
- `dataset-visual`
- `generate-emb`
- `oagbert`
- `recommendation`

## Dataset stats

```python
from cogdl import pipeline
stats = pipeline("dataset-stats")
rows = stats("cora")
```

What to expect:
- Returns a tabular summary with node, edge, feature, class, and labeled-data
  counts.
- First use of a built-in dataset may download or cache data if it is missing.

## Dataset visual

```python
from cogdl import pipeline
visual = pipeline("dataset-visual")
visual("cora", seed=0, depth=3)
```

What to expect:
- Samples an ego network and writes a PNG named after the dataset.
- Treat built-in datasets as cache/network-dependent.

## Generate embeddings

Safe no-download embedding-model recipe:

```python
import numpy as np
from cogdl import pipeline

generator = pipeline("generate-emb", model="prone")
edge_index = np.array([[0, 1], [0, 2], [1, 2], [2, 3], [3, 4]])
emb = generator(edge_index)
```

What to expect:
- Embedding-model runs such as `prone`, `netmf`, `netsmf`, `deepwalk`,
  `line`, `node2vec`, `hope`, `sdne`, `grarep`, `dngr`, and `spectral`
  can run from an edge list without a built-in dataset.
- GNN-based embedding models need node features or an explicit `num_features`
  choice; those runs may also train and are not part of the safe smoke path.
- Older training-backed embedding paths such as `mvgrl` may hit the removed
  `np.int` alias on NumPy 1.24+; use the safe `prone` smoke path for no-download
  checks, or pin `numpy<1.24` if you need that older model path.

## Recommendation

```python
import numpy as np
from cogdl import pipeline

data = np.array([[0, 1], [0, 2], [1, 2], [1, 3], [2, 3]])
rec = pipeline("recommendation", model="lightgcn", data=data)
```

What to expect:
- The pipeline accepts either a recommendation-style built-in dataset or a
  custom NumPy interaction array.
- The implementation uses the trailing rows of the custom array for validation
  and test data.
- Querying the result returns top-k recommendations per user.

## OAG-BERT

`pipeline("oagbert", model="oagbert-v1")` returns a tokenizer and model for
paper/entity workflows. Read `references/oagbert.md` for variants and input
fields.

## Choosing a recipe

- Use `dataset-stats` when you only need counts or a quick dataset sanity
  check.
- Use `dataset-visual` when you need an ego-network image and can tolerate a
  PNG write.
- Use `generate-emb` when the task is about graph embeddings rather than a
  full training loop.
- Use `recommendation` when the request is about top-k ranking for users/items.
- Use `oagbert` when the request is paper metadata, entity-aware encoding, or
  text generation around academic graphs.
