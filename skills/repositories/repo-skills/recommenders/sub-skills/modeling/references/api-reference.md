# Modeling API Reference

This reference lists the model APIs and helper contracts most likely to be used by an agent. Defaults are those verified or source-confirmed for Recommenders 1.2.1.

## Package and entry-point facts

- Public distribution/import name: `recommenders`.
- No console entry points are declared; modeling workflows use Python imports.
- Base install includes SAR, TF-IDF utilities, Cornac, LightGBM helpers, pandas/numpy/scipy/scikit-learn utilities, and supporting packages.
- Optional extras are required for Spark, GPU/deep-learning, developer, all, and experimental model families. This sub-skill verified only the base CPU scope.

## Standard dataframe column names

Most model helpers use these names unless overridden:

| Meaning | Default column |
|---|---|
| User id | `userID` |
| Item id | `itemID` |
| Observed rating/weight/label for recommender metrics | `rating` |
| Event timestamp | `timestamp` |
| Model score or prediction | `prediction` |

Pass matching `col_user`, `col_item`, `col_rating`, `col_timestamp`, or `col_prediction` arguments when a user uses custom columns.

## SAR: CPU collaborative filtering

Import:

```python
from recommenders.models.sar import SAR
```

Constructor:

```python
SAR(
    col_user="userID",
    col_item="itemID",
    col_rating="rating",
    col_timestamp="timestamp",
    col_prediction="prediction",
    similarity_type="jaccard",
    time_decay_coefficient=30,
    time_now=None,
    timedecay_formula=False,
    threshold=1,
    normalize=False,
)
```

Supported `similarity_type` values:

- `"cooccurrence"`
- `"cosine"`
- `"inclusion index"`
- `"jaccard"`
- `"lexicographers mutual information"`
- `"lift"`
- `"mutual information"`

Important methods:

| Method | Purpose | Input | Output/notes |
|---|---|---|---|
| `fit(df)` | Build user-affinity and item-similarity matrices | Dataframe with user, item, numeric rating; timestamp only if time decay is enabled | Raises on duplicate selected training rows or non-numeric ratings |
| `predict(test)` | Score only the provided user-item pairs | Dataframe with user and item columns | Dataframe with user, item, prediction columns; unseen items receive score 0 with a warning; unseen users raise an error |
| `score(test, remove_seen=False)` | Score all known items for each unique test user | Dataframe with user column | Dense array with shape `(n_test_users, n_train_items)`; `remove_seen=True` masks training items |
| `recommend_k_items(test, top_k=10, sort_top_k=True, remove_seen=False)` | Produce per-user top-k recommendations | Dataframe with user column; may also include item/rating columns | Dataframe with user, item, prediction columns |
| `get_item_based_topk(items, top_k=10, sort_top_k=True)` | Recommend items similar to seed items; useful for cold user/item-list scenarios | Dataframe with item column; optional user and rating columns | Dataframe with user, item, prediction columns; seed items are removed |
| `get_popularity_based_topk(top_k=10, sort_top_k=True, items=True)` | Popular items or users | no dataframe after fit | Dataframe with item/user and prediction count |
| `get_topk_most_similar_users(user, top_k, sort_top_k=True)` | Similar users based on affinity vectors | known user id | Dataframe with user and prediction columns |

SAR data notes:

- Remove or aggregate duplicate user-item interactions before `fit`. If time decay is disabled, duplicates in user/item/rating rows are rejected. If time decay is enabled, timestamp is part of the selected duplicate check.
- Ratings must be numeric. For implicit feedback, use `rating=1` or a confidence/count weight.
- `threshold` must be at least 1.
- Enable `timedecay_formula=True` only when a timestamp column exists and is on a consistent numeric time scale. The `time_decay_coefficient` is a half-life in days.
- `normalize=True` rescales scores to the min/max rating range observed at fit time.

## TF-IDF: CPU content-based item similarity

Import:

```python
from recommenders.models.tfidf.tfidf_utils import TfidfRecommender
```

Constructor:

```python
TfidfRecommender(id_col, tokenization_method="scibert")
```

Tokenization methods:

| Method | Use when | Dependency note |
|---|---|---|
| `none` | Deterministic local workflow where text is already simple enough for scikit-learn tokenization | Safest no-network option |
| `nltk` | Stemming is desired | May require NLTK tokenizer resources |
| `bert` | BERT tokenization is required and assets are already available | Requires HuggingFace tokenizer assets; may try to download if absent |
| `scibert` | Scientific text tokenization is required and assets are already available | Default constructor value, but not the safest no-network setting |

Typical methods:

| Method | Purpose | Input | Output/notes |
|---|---|---|---|
| `clean_dataframe(df, cols_to_clean, new_col_name="cleaned_text")` | Join and clean one or more text columns | item dataframe and list of text column names | Dataframe with `new_col_name` added; NaNs replaced with empty text |
| `tokenize_text(df_clean, text_col="cleaned_text", ngram_range=(1, 3), min_df=0.0)` | Build a `TfidfVectorizer` and tokenized text series | cleaned dataframe | `(tf, vectors_tokenized)` |
| `fit(tf, vectors_tokenized)` | Fit the TF-IDF matrix | vectorizer and tokenized text | Stores `tfidf_matrix` |
| `get_tokens()` | Inspect learned vocabulary | after tokenization and fit | dictionary of token to feature index |
| `get_stop_words()` | Inspect vectorizer stop words | after tokenization and fit | stop-word collection |
| `recommend_top_k_items(df_clean, k=5)` | Build all item-to-item recommendations | cleaned dataframe | Dataframe with `id_col`, `rec_rank`, `rec_score`, and `rec_<id_col>` |
| `get_top_k_recommendations(metadata, query_id, cols_to_keep=[], verbose=True)` | Return detailed recommendations for one query item | metadata dataframe and query item id | Dataframe-like object; if URL formatting is triggered, access underlying tabular data through the returned object's data attribute |

TF-IDF data notes:

- `k` must be less than the number of items; requesting more recommendations than available raises `ValueError`.
- Empty or identical text can produce unhelpful or failing vectorizer output. Validate at least two non-empty documents and useful tokens.
- Use `tokenization_method="none"` in tests and automated smoke checks to avoid network/cache assumptions.

## Cornac helpers

Imports:

```python
import cornac
from recommenders.models.cornac.bpr import BPR
from recommenders.models.cornac.cornac_utils import predict, predict_ranking
```

Helper signatures:

```python
predict(model, data, usercol="userID", itemcol="itemID", predcol="prediction")
predict_ranking(model, data, usercol="userID", itemcol="itemID", predcol="prediction", remove_seen=False)
```

Contracts:

- `model` must be a fitted Cornac recommender with `train_set.uid_map`, `train_set.iid_map`, `rate`, and for ranking, `score` behavior.
- Use `cornac.data.Dataset.from_uir(train.itertuples(index=False), seed=...)` to build a train set from a dataframe containing user, item, rating columns in that order.
- `predict` returns one row per input user-item pair.
- `predict_ranking` scores every known training user against every known training item. With `remove_seen=True`, the helper removes user-item pairs present in `data`.
- Recommenders' `BPR` wrapper extends Cornac BPR with `recommend_k_items(data, top_k=None, remove_seen=False, col_user="userID", col_item="itemID", col_prediction="prediction")`.

## LightGBM helper

Import:

```python
from recommenders.models.lightgbm.lightgbm_utils import NumEncoder
```

Constructor:

```python
NumEncoder(cate_cols, nume_cols, label_col, threshold=10, thresrate=0.99)
```

Methods:

| Method | Purpose | Output |
|---|---|---|
| `fit_transform(df)` | Fit categorical filtering/ordinal/target/binary encodings and numeric imputers on training data | `(train_x, train_y)` numpy arrays |
| `transform(df)` | Apply learned encodings to validation/test data | `(x, y)` numpy arrays |

LightGBM modeling notes:

- This helper is for supervised tabular prediction such as click-through rate, not for direct collaborative top-k recommendation.
- `cate_cols`, `nume_cols`, and `label_col` must match dataframe columns exactly.
- Low-frequency categories are mapped to `<LESS>`; missing categorical values are filled with `<UNK>`; missing numeric values use training means.
- Route parameter sweeps or benchmark comparisons to the operations-and-tuning sub-skill.

## Optional model entry points

The following APIs are useful only when their optional dependencies and data layouts are available. In this skill creation run they were not verified beyond source/import classification.

| Family | Typical entry point | Key requirements |
|---|---|---|
| Spark ALS | PySpark ML `ALS` plus Recommenders Spark utilities | Spark extra, Java/JDK, Spark session, Spark DataFrames with user/item/rating columns |
| NCF | `recommenders.models.ncf.dataset.Dataset`, `recommenders.models.ncf.ncf_singlenode.NCF` | PyTorch; train/test files expected by NCF dataset helper; negative sampling/candidate pool preparation |
| Wide&Deep | `recommenders.models.wide_deep` utilities and model class | PyTorch; encoded wide and deep feature sets; explicit rating or ranking pool workflow |
| VAE | `StandardVAE`, `MultVAE` | PyTorch; user-item matrix preparation and batch training loop |
| RBM | `recommenders.models.rbm.rbm.RBM` | TensorFlow; visible unit count and possible rating levels; rating matrix conversion |
| SASRec/SSEPT | `recommenders.models.sasrec` | PyTorch; ordered user sequences, sampler, negative item candidates |
| DeepRec | `recommenders.models.deeprec` models, iterators, hparams utilities | TensorFlow; model-specific YAML hparams and files; often external resources |
| NewsRec | `recommenders.models.newsrec` models and iterators | TensorFlow; MIND-style news/behavior files, word/user dictionaries, embeddings |
| Surprise | `recommenders.models.surprise.surprise_utils` | Experimental `scikit-surprise`; Surprise trainset/algo objects |
| LightFM | `recommenders.models.lightfm.lightfm_utils` | Experimental `lightfm`; sparse interactions and optional feature matrices |
| Vowpal Wabbit | `recommenders.models.vowpal_wabbit.vw.VW` | Experimental VW package/binary and compatible feature formatting |
| xLearn | Example-level FM/FFM workflow | Experimental xLearn package, often CMake/build tools, LibFFM-style data |
| GeoIMC/RLRMC | `recommenders.models.geoimc`, `recommenders.models.rlrmc` | Experimental pymanopt-compatible stack and matrix-completion feature inputs |

## Small utility functions often seen in model notebooks

```python
from recommenders.utils.python_utils import binarize, get_top_k_scored_items

binarize(a, threshold)
get_top_k_scored_items(scores, top_k, sort_top_k=False)
```

- Use `binarize` to turn rating arrays or columns into implicit/binary relevance before evaluation.
- Use `get_top_k_scored_items` only when you already have a score matrix and need top item indices/scores. For SAR top-k, prefer `recommend_k_items`.
