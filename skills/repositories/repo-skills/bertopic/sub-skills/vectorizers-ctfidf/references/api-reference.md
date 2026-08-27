# API reference

This sub-skill owns BERTopic topic-term extraction and online vocabulary workflows.

## Core classes

| Class | Purpose | Key parameters | Notes |
| --- | --- | --- | --- |
| `bertopic.vectorizers.ClassTfidfTransformer` | Class-based TF-IDF used to score words per topic | `bm25_weighting`, `reduce_frequent_words`, `seed_words`, `seed_multiplier` | Expects a sparse count matrix grouped per topic. It normalizes each topic row before applying the IDF variant. |
| `bertopic.vectorizers.OnlineCountVectorizer` | Incremental `CountVectorizer` with vocabulary growth and cleanup | `decay`, `delete_min_df`, plus normal `CountVectorizer` kwargs | Use for streaming / partial-fit workflows. It updates the vocabulary with OOV tokens and can remove low-frequency terms after each update. |

## BERTopic entry points

| API | Purpose | Important behavior |
| --- | --- | --- |
| `BERTopic(..., vectorizer_model=..., ctfidf_model=...)` | Inject a custom vectorizer and/or c-TF-IDF transformer before fitting | Best for changing topic words without changing clustering. |
| `BERTopic.update_topics(docs, images=None, topics=None, top_n_words=10, n_gram_range=None, vectorizer_model=None, ctfidf_model=None, representation_model=None)` | Recompute topic words after fitting | Use `topics=` as a keyword if you are remapping topic assignments. `images` is the second positional argument, so do not pass a topic list positionally. The method refreshes topic representations and topic vectors; it does not retrain embeddings or clustering. |
| `BERTopic.partial_fit(...)` | Incremental learning workflow | This sub-skill only covers the vectorizer side of the online path; the cluster and dimensionality reducers must also support partial fitting. |

## CountVectorizer knobs used here

| Parameter | What it changes | When to use |
| --- | --- | --- |
| `ngram_range` | Single words vs. phrases | Raise it to surface domain phrases such as bigrams and trigrams. |
| `stop_words` | Removes generic words before scoring | Use English stopwords or a domain stopword list when common words dominate topics. |
| `min_df` | Drops terms that appear too rarely | Use to reduce sparse vocabulary size and remove one-off noise. |
| `max_features` | Caps the vocabulary by frequency | Use when you want a hard vocabulary ceiling without tuning `min_df` aggressively. |
| `tokenizer` | Custom token segmentation | Required for languages or corpora that need custom token boundaries. When you pass a tokenizer, make tokenization behavior explicit and keep it stable across fit and refresh calls. |
| `token_pattern=None` | Lets the custom tokenizer own tokenization | Use when your tokenizer already performs segmentation and you want the regex tokenizer disabled. |

## c-TF-IDF behavior to remember

- Topics are scored after documents are grouped by topic.
- The count matrix is L1-normalized row-wise before IDF weighting.
- `bm25_weighting=True` swaps in a BM25-style class IDF variant.
- `reduce_frequent_words=True` applies a square root to normalized term frequencies and can reduce generic words that are not standard stopwords.
- `seed_words` and `seed_multiplier` boost exact-matching terms when the model is configured to use seed words.
- The transformer consumes sparse counts, not raw text.

## Online vocabulary behavior to remember

- `partial_fit(raw_documents)` expands the vocabulary with OOV tokens.
- `update_bow(raw_documents)` updates the stored sparse bag-of-words matrix.
- `decay` reduces older counts before adding a new batch.
- `delete_min_df` removes terms whose accumulated frequency falls below the threshold.
- Terms removed by cleanup can reappear later if they become frequent again.
- `OnlineCountVectorizer` still accepts normal `CountVectorizer` options such as `stop_words`, `ngram_range`, `min_df`, and custom tokenizers.

## Related workflow help

- See [`workflows.md`](workflows.md) for recommended tuning and online update sequences.
- See [`troubleshooting.md`](troubleshooting.md) for import, parameter, and empty-vocabulary failures.
- See [`../scripts/smoke_vectorizers.py`](../scripts/smoke_vectorizers.py) for a safe synthetic verification helper.
