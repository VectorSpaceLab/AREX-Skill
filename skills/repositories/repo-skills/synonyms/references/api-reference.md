# API Reference

## Purpose

Use this for package-specific API signatures, return shapes, default parameters, and gotchas verified from source and installed-package inspection for Synonyms 3.25.1.

Import pattern:

```python
import synonyms
```

Set `SYNONYMS_DL_LICENSE` or `SYNONYMS_WORD2VEC_BIN_MODEL_ZH_CN` before this import when the model is not already packaged. See [model-and-environment.md](model-and-environment.md).

## Public functions

| API | Verified signature | Returns / behavior | Gotchas |
| --- | --- | --- | --- |
| `synonyms.nearby` | `(word, size=10)` | Tuple `([words], [scores])`; scores are floats in `[0, 1]` where larger is nearer. | OOV words return `([], [])`. With a tiny custom model, keep `size <= vocab_size`. |
| `synonyms.display` | `(word, size=10)` | Prints a numbered nearby-word list using `nearby`. | Display-only helper; use `nearby` for programmatic results. |
| `synonyms.compare` | `(s1, s2, seg=True, ignore=False, stopwords=False)` | Float similarity rounded to three decimals and clamped to `[0, 1]`. Identical raw inputs return `1.0`. | If `seg=True`, Synonyms segments both strings first. If `seg=False`, each sentence is split on spaces and should already be tokenized. |
| `synonyms.seg` | `(sen, HMM=True)` | Tuple `(words, tags)` from jieba POS segmentation. | It does not remove stopwords or punctuation. Custom dictionary must be configured before import. |
| `synonyms.keywords` | `(sentence, topK=5, withWeight=False, allowPOS=())` | Delegates to `jieba.analyse.extract_tags`; returns keywords or `(word, weight)` pairs when `withWeight=True`. | Import still requires the model even though keyword extraction is jieba-based. |
| `synonyms.describe` | `()` | Prints and returns `{"vocab_size", "version", "model_path"}`. | Returned `model_path` can be local/private; do not expose it in public artifacts. |
| `synonyms.v` | `(word)` | NumPy vector for a word. | Raises `KeyError` for OOV. |
| `synonyms.sv` | `(sentence, ignore=False)` | Array/list-like collection of per-token vectors for a tokenized sentence. | `sentence` is expected to be a sequence of tokens/characters as consumed by internal iteration; README describes a segmented string joined by spaces. |
| `synonyms.bow` | `(sentence, ignore=False)` | Bag-of-words-style summed vector from `_get_wv`. | Same tokenization/OOV caveats as `sv`. |

## Common examples

### Nearby words

```python
import synonyms
words, scores = synonyms.nearby("飞机", 10)
for word, score in zip(words, scores):
    print(word, score)
```

Use the returned tuple directly in applications. Use `display` only when printing debug output:

```python
synonyms.display("飞机", 10)
```

### Sentence similarity

```python
score = synonyms.compare("旗帜引领方向", "旗帜指引道路", seg=True)
assert 0.0 <= score <= 1.0
```

For pre-tokenized inputs, use spaces and `seg=False`:

```python
score = synonyms.compare("你们 好 呀", "大家 好", seg=False)
```

### Segmentation and keyword extraction

```python
words, tags = synonyms.seg("中文近义词工具包")
keywords = synonyms.keywords("华为芯片供应出现变化", topK=3)
```

### Vector access

```python
try:
    vec = synonyms.v("飞机")
except KeyError:
    vec = None
```

`v` requires the word to exist in the loaded model. For OOV-tolerant sentence workflows, inspect the `ignore` behavior on `compare`, `sv`, and `bow`.

## Similarity internals that affect user results

- `nearby` queries a KDTree over the loaded word vectors and sorts results by cosine score.
- `compare` combines vector cosine similarity with a Levenshtein-style character similarity smoothed into a score. This means identical strings are exactly `1.0`, and short strings with similar characters can score nonzero even when vector lookups are weak.
- Stopwords are loaded from package data and filtered by default in `compare` when `stopwords=False`.
- OOV words in `_get_wv` either get deterministic random vectors (`ignore=False`) or are skipped (`ignore=True`). For robust production behavior, prefer a complete real model rather than relying on OOV fallback.
