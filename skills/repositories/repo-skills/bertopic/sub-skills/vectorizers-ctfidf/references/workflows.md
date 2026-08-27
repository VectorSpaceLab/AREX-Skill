# Workflows

## 1) Fit-time topic-term tuning

Use this when the model is not yet trained and you want better topic words from the start.

1. Choose a `CountVectorizer` that matches the corpus.
2. Tune `stop_words`, `min_df`, `max_features`, and `ngram_range` conservatively first.
3. If the topic words still look generic, add `ClassTfidfTransformer(reduce_frequent_words=True)`.
4. On smaller datasets, try `bm25_weighting=True` as a second pass.
5. Fit BERTopic with the vectorizer and c-TF-IDF transformer already injected.

```python
from bertopic import BERTopic
from bertopic.vectorizers import ClassTfidfTransformer
from sklearn.feature_extraction.text import CountVectorizer

vectorizer_model = CountVectorizer(
    stop_words="english",
    min_df=2,
    ngram_range=(1, 2),
)
ctfidf_model = ClassTfidfTransformer(
    bm25_weighting=True,
    reduce_frequent_words=True,
)

model = BERTopic(
    vectorizer_model=vectorizer_model,
    ctfidf_model=ctfidf_model,
)
```

### Good signals

- Topic names become more specific.
- Stop words disappear from the top-ranked terms.
- Phrases appear where the corpus naturally contains multiword entities.
- The sparse topic-term matrix gets smaller when `min_df` or `max_features` is tightened.

### Bad signals

- Empty or near-empty topic vocabularies.
- Only a few terms survive after stopword removal.
- Every topic looks identical because the vectorizer is too restrictive.

## 2) Post-fit `update_topics` refresh

Use this when the cluster assignments are acceptable but the topic words need cleanup.

1. Keep the original documents in the same order used during fitting.
2. Build a new `CountVectorizer` for the desired representation style.
3. Pass it to `update_topics(...)`.
4. If you are changing topic assignments too, pass `topics=` explicitly.
5. Re-check the top words and the vocabulary size.

```python
from sklearn.feature_extraction.text import CountVectorizer
from bertopic.vectorizers import ClassTfidfTransformer

vectorizer_model = CountVectorizer(
    stop_words="english",
    ngram_range=(1, 3),
    min_df=5,
)
ctfidf_model = ClassTfidfTransformer(reduce_frequent_words=True)

model.update_topics(
    docs,
    vectorizer_model=vectorizer_model,
    ctfidf_model=ctfidf_model,
)
```

### Good signals

- The topic name becomes more specific.
- Stop words disappear from the top-ranked terms.
- Phrases appear where the corpus naturally contains multiword entities.
- The sparse topic-term matrix gets smaller when `min_df` or `max_features` is tightened.

### Bad signals

- Empty or near-empty topic vocabularies.
- Only a few terms survive after stopword removal.
- Every topic looks identical because the vectorizer is too restrictive.
- Boundary-crossing phrases appear after topic documents are concatenated; this is normal when you group documents into topic documents, but it may require a lower `ngram_range` or more careful preprocessing.

## 3) Custom tokenizer workflow

Use a custom tokenizer when the default token boundaries are wrong for your text.

1. Write a tokenizer that returns a list of tokens.
2. Pass it into `CountVectorizer` or `OnlineCountVectorizer`.
3. Set `token_pattern=None` when using a custom tokenizer so the tokenizer is the source of truth.
4. Keep the tokenizer deterministic across fit and update calls.

```python
from sklearn.feature_extraction.text import CountVectorizer

vectorizer = CountVectorizer(
    tokenizer=my_tokenizer,
    token_pattern=None,
    lowercase=False,
)
```

### Practical notes

- If you need Chinese segmentation or another language-specific splitter, use a domain-appropriate tokenizer.
- If your tokenizer already normalizes case, disable redundant lowercasing.
- If the tokenizer emits many one-off tokens, pair it with `min_df`.

## 4) Streaming vocabulary workflow

Use `OnlineCountVectorizer` when topic-term extraction must evolve over batches.

1. Initialize `OnlineCountVectorizer` with any normal `CountVectorizer` options you still need.
2. Add `decay` when recent batches should matter more than older batches.
3. Add `delete_min_df` when the vocabulary should stay bounded.
4. Call `partial_fit(batch)` before `update_bow(batch)` for each batch.
5. After each batch, inspect the sparse matrix and vocabulary size.

```python
from bertopic.vectorizers import OnlineCountVectorizer

vectorizer = OnlineCountVectorizer(
    stop_words="english",
    ngram_range=(1, 2),
    decay=0.1,
    delete_min_df=5,
)

for batch in batches:
    vectorizer.partial_fit(batch)
    bow = vectorizer.update_bow(batch)
```

### Good signals

- Older terms fade naturally when they are no longer supported by new data.
- Low-frequency noise disappears after cleanup.
- Frequent new terms re-enter the vocabulary automatically.

### Bad signals

- `update_bow` is called before the first `partial_fit` / `fit`.
- Batch shapes change in a way that makes your manual bag-of-words bookkeeping inconsistent.
- `delete_min_df` is so high that the vocabulary keeps collapsing.

## 5) Tiny smoke-check workflow

Use the bundled smoke script when you want a fast confidence check without downloading models.

```bash
python scripts/smoke_vectorizers.py
```

The script exercises:

- custom tokenization,
- c-TF-IDF scoring,
- fit-time `CountVectorizer` sweeps,
- `update_topics(...)` refreshes, and
- `OnlineCountVectorizer` decay/cleanup behavior.

## Tuning order of operations

Recommended sequence for manual investigation:

1. Start with `stop_words` and `min_df`.
2. Add `ngram_range` if phrases matter.
3. Add `max_features` if the vocabulary is still too large.
4. Add `reduce_frequent_words` if generic high-frequency terms still dominate.
5. Add `bm25_weighting` if you are on a smaller corpus and want a more aggressive reweighting variant.
6. Move to `OnlineCountVectorizer` only when the workflow must support incremental updates.
