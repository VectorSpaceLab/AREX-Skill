# Tree and Vector API Guide

The graph demo includes two lightweight utilities under the toolkit: a hierarchy
`TREE` helper and a word-vector similarity helper. This page captures their
operational contracts without depending on the original checkout.

## `TREE` hierarchy behavior

The `TREE` class stores:

- `edge`: adjacency map for internal category edges.
- `leaf`: map from category to leaf entity titles.
- `root`: fixed string `农业`.
- `curpath` and `anspath`: traversal state used by DFS methods.
- `UI_str`: generated HTML tree fragment.

### Loading files

`read_edge(src)` reads parent/child category edges from a text file:

```text
农业 可以食用的植物
可以食用的植物 水果
```

`read_leaf(src)` reads category/entity leaf assignments:

```text
水果 苹果
水果 香蕉
```

Both loaders skip exact duplicate lines and use the first two space-separated
tokens. Paths containing spaces require a parser change.

### Query methods

| Method | Input | Output | Notes |
| --- | --- | --- | --- |
| `get_path(word, unique)` | leaf entity title, boolean | List of root-to-leaf paths | Each path ends with `word`. With `unique=True`, paths whose node sets overlap by more than two nodes are pruned after a random shuffle. |
| `get_father(word)` | category title | List of parent categories | Searches `edge` values only, not `leaf`. |
| `get_branch(word)` | category title | List of non-leaf child categories | Returns `[]` when no branch children exist. |
| `get_leaf(word)` | category title | List of leaf entities | Returns `[]` when no leaf list exists. |
| `create_UI(theme)` | category title | HTML `<ul>...</ul>` fragment | Expands the path from root to `theme` and marks the target as current category. |

### Example behavior

With edges `农业 -> 可以食用的植物 -> 粮食作物 -> 谷物` and leaf `谷物 -> 小麦`,
`get_path('小麦', False)` returns:

```python
[['农业', '可以食用的植物', '粮食作物', '谷物', '小麦']]
```

Run [the bundled smoke script](../scripts/tree_api_smoke.py) for a self-contained
fixture check of these contracts.

## Word-vector behavior

`cos_simi(vector1, vector2)` computes cosine similarity over zipped vector
values and returns `None` if either vector has zero norm. It does not validate
that the vectors have the same length beyond Python's `zip` truncation.

`word_vector_model.read_vec(vec_src)` loads a dictionary:

```python
self.wv[word] = [float_1, float_2, ...]
```

`word_vector_model.get_simi_top(word, top_num)` returns a list of similar words,
but it is not a stable nearest-neighbor implementation:

- It raises `KeyError` if `word` is missing.
- It increments `top_num` internally, then returns the requested number of words.
- It skips candidate keys longer than 12 characters.
- It randomly skips about 70% of candidate words, so repeated calls can differ.
- It returns words only, not similarity scores.
- Dead code after a `continue` suggests a previous sorted-insertion approach was
  abandoned.

Use this helper as a demo/tag-cloud utility, not as a deterministic retrieval
benchmark. For reproducible experiments, replace random sampling with a full
scan or fixed-seed sampler and return scores with words.

## Practical modifications

When modernizing the utilities:

- Keep the root default `农业` unless the data source changes.
- Preserve duplicate-line filtering for source compatibility.
- Reset traversal state (`anspath`, `curpath`, `UI_str`) per call to avoid
  leaking state across requests.
- Escape category/entity text before embedding it in HTML if accepting untrusted
  data.
- Validate vector dimensions and handle missing words explicitly in any new API.
