# Modeling Workflows

These workflows are designed for agents using Recommenders without reopening the original repository. They assume data has already been loaded, validated, de-duplicated, and split when needed. Route those upstream steps to the data-preparation sub-skill, and route metric computation to the evaluation sub-skill.

## Workflow: choose a model family

1. Identify data signal:
   - User-item interactions only: start with SAR on CPU.
   - User-item interactions at Spark scale: consider Spark ALS only if Spark is installed and allowed.
   - Item text/content only: start with TF-IDF.
   - News recommendation with MIND-style files: consider NewsRec only if TensorFlow and data artifacts exist; otherwise use TF-IDF as a baseline.
   - Tabular click-through/ad features: use LightGBM utilities and LightGBM training.
   - Sequential sessions: consider SASRec/SSEPT or DeepRec sequential models only with PyTorch/TensorFlow installed.
2. Identify backend budget:
   - Base CPU only: SAR, TF-IDF, Cornac helpers, LightGBM helper workflows.
   - Spark allowed: ALS, Spark LightGBM, SARplus, Spark evaluation.
   - Deep-learning/GPU allowed: NCF, VAE, RBM, Wide&Deep, NewsRec, DeepRec, SASRec/SSEPT.
   - Experimental allowed: Surprise, LightFM, Vowpal Wabbit, xLearn, GeoIMC/RLRMC dependencies.
3. Decide deliverable shape:
   - Pair scores for existing user-item pairs: call `predict` where available.
   - Top-k recommendations: call `recommend_k_items`, `predict_ranking`, or construct a candidate pool and keep top-k per user.
   - Item-to-item content suggestions: use TF-IDF `recommend_top_k_items`.
4. Validate output columns:
   - Ranking/evaluation handoff should include `userID`, `itemID`, and `prediction`.
   - Rating metric handoff should align prediction rows with true rating rows.

## Workflow: CPU SAR collaborative filtering

Use when the user has a pandas dataframe of interactions and wants a fast single-node recommender baseline.

### Inputs

- `train`: dataframe with `userID`, `itemID`, numeric `rating`; include `timestamp` only when time decay is requested.
- `test_users` or `test`: dataframe containing at least `userID`; if pairwise predictions are requested, include `itemID` too.
- No duplicate user-item interactions for the selected training columns. Aggregate duplicates upstream if needed.

### Minimal recipe

```python
import pandas as pd
from recommenders.models.sar import SAR

train = pd.DataFrame(
    {
        "userID": ["u1", "u1", "u2", "u2", "u3", "u3", "u4", "u4"],
        "itemID": ["i1", "i2", "i1", "i3", "i2", "i4", "i3", "i4"],
        "rating": [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0],
        "timestamp": [1, 2, 1, 3, 2, 4, 3, 4],
    }
)

model = SAR(
    col_user="userID",
    col_item="itemID",
    col_rating="rating",
    col_timestamp="timestamp",
    similarity_type="jaccard",
    timedecay_formula=False,
    threshold=1,
)
model.fit(train)

top_k = model.recommend_k_items(
    train[["userID"]].drop_duplicates(),
    top_k=2,
    remove_seen=True,
)
print(top_k[["userID", "itemID", "prediction"]])
```

### Pairwise predictions

Use `predict(test_pairs)` when the user asks for scores for specific existing or candidate pairs:

```python
test_pairs = pd.DataFrame({"userID": ["u1", "u2"], "itemID": ["i3", "i4"]})
preds = model.predict(test_pairs)
```

### Validation

- `set(top_k.columns)` should include `{"userID", "itemID", "prediction"}`.
- With `remove_seen=True`, no `(userID, itemID)` in `top_k` should appear in the training interactions.
- If routing to evaluation, pass `top_k` and a true/held-out dataframe to the evaluation sub-skill.

### Bundled smoke

```bash
python sub-skills/modeling/scripts/sar_tiny_smoke.py --top-k 2
```

Expected signal: JSON summary reporting non-empty recommendations, columns `userID`, `itemID`, `prediction`, and `remove_seen_ok: true`.

## Workflow: CPU TF-IDF content-based item recommendation

Use when the user has item metadata text and wants similar items without user histories.

### Inputs

- Item dataframe with stable id column, such as `item_id`.
- One or more text columns, such as `title`, `abstract`, `description`, or `full_text`.
- At least `k + 1` items with non-empty text.

### Minimal no-network recipe

```python
import pandas as pd
from recommenders.models.tfidf.tfidf_utils import TfidfRecommender

items = pd.DataFrame(
    {
        "item_id": ["paper-a", "paper-b", "paper-c", "paper-d"],
        "title": [
            "graph neural recommenders",
            "graph embeddings for ranking",
            "kitchen recipe retrieval",
            "neural collaborative filtering",
        ],
        "abstract": [
            "collaborative filtering on user item graphs",
            "ranking items with graph representation learning",
            "ingredients and cooking instructions",
            "matrix factorization with neural networks",
        ],
    }
)

recommender = TfidfRecommender(id_col="item_id", tokenization_method="none")
clean = recommender.clean_dataframe(items, ["title", "abstract"], "cleaned_text")
tf, vectors = recommender.tokenize_text(clean, text_col="cleaned_text", ngram_range=(1, 2))
recommender.fit(tf, vectors)
item_recs = recommender.recommend_top_k_items(clean, k=1)
print(item_recs)
```

### Choosing tokenization

- Use `tokenization_method="none"` for deterministic local automation.
- Use `"nltk"` only when NLTK token data is installed.
- Use `"bert"` or `"scibert"` only when tokenizer assets are already available and network/cache policy allows them. The default constructor is `"scibert"`, but that is not the safest smoke-test setting.

### Validation

- Output columns are `item_id`, `rec_rank`, `rec_score`, and `rec_item_id` for `id_col="item_id"`.
- Each query item should have at most `k` rows.
- Self-recommendations should not appear because the implementation drops the query item from its own similar-item list.

### Bundled smoke

```bash
python sub-skills/modeling/scripts/tfidf_tiny_smoke.py --top-k 1
```

Expected signal: JSON summary reporting a vocabulary size, non-empty recommendations, and `self_recommendations: 0`.

## Workflow: Cornac model scoring and ranking

Use when the user selects a Cornac model such as MF/BPR and needs outputs compatible with Recommenders metrics.

```python
import pandas as pd
import cornac
from recommenders.models.cornac.cornac_utils import predict, predict_ranking

ratings = pd.DataFrame(
    {
        "userID": [1, 1, 2, 2, 3, 3],
        "itemID": [1, 2, 1, 3, 2, 3],
        "rating": [5.0, 4.0, 4.0, 5.0, 3.0, 5.0],
    }
)
train_set = cornac.data.Dataset.from_uir(ratings[["userID", "itemID", "rating"]].itertuples(index=False), seed=42)
model = cornac.models.MF(k=8, max_iter=20, seed=42).fit(train_set)

pair_scores = predict(model, ratings)
rank_scores = predict_ranking(model, ratings, remove_seen=True)
```

Notes:

- `predict` is appropriate for rating metrics because it scores only rows in the input dataframe.
- `predict_ranking` scores all training users by all training items; this can grow as `n_users * n_items`.
- With `remove_seen=True`, rows present in the provided interaction dataframe are removed from ranking output.
- For full top-k BPR output, Recommenders' `BPR` wrapper has `recommend_k_items(...)`; keep training iterations small in smoke checks.

## Workflow: LightGBM supervised click/ranking helper

Use when the user has tabular features and a binary or numeric label, not a plain collaborative-filtering matrix.

```python
import lightgbm as lgb
from recommenders.models.lightgbm.lightgbm_utils import NumEncoder

cate_cols = ["site", "ad_id", "device"]
nume_cols = ["hour", "price"]
label_col = "clicked"

encoder = NumEncoder(cate_cols=cate_cols, nume_cols=nume_cols, label_col=label_col, threshold=2)
train_x, train_y = encoder.fit_transform(train_df)
valid_x, valid_y = encoder.transform(valid_df)

train_data = lgb.Dataset(train_x, label=train_y.reshape(-1))
valid_data = lgb.Dataset(valid_x, label=valid_y.reshape(-1), reference=train_data)
params = {"objective": "binary", "metric": "binary_logloss", "verbosity": -1}
model = lgb.train(params, train_data, valid_sets=[valid_data], num_boost_round=20)
proba = model.predict(valid_x)
```

Notes:

- `NumEncoder` mutates/derives categorical filtering state from training data. Fit on training only, then transform validation/test.
- Use operations-and-tuning for parameter grids, early stopping choices, benchmark runs, or deployment.
- Use evaluation for AUC/logloss/ranking metric calculation.

## Optional workflow: Spark ALS

Only proceed when Spark is explicitly available.

Checklist:

1. Confirm the Spark extra and Java/JDK/PySpark runtime are installed.
2. Build a Spark session with enough memory for the dataset.
3. Provide a Spark DataFrame with integer-compatible user/item columns and numeric rating column.
4. Split data using Spark data-preparation helpers or Spark-native splits.
5. Fit PySpark ML `ALS` with explicit `userCol`, `itemCol`, and `ratingCol`.
6. Transform candidate pairs or generate recommendations.
7. Use Spark evaluation helpers in the evaluation sub-skill.

Do not mark Spark ALS verified from this sub-skill unless a future backend-specific verification run executes a Spark smoke/native case.

## Optional workflow: deep-learning collaborative models

Families: NCF, EmbeddingDotBias, Wide&Deep, VAE, RBM, SASRec/SSEPT, DeepRec sequence/graph models.

Checklist before importing model modules:

1. Check the framework import required by the model: PyTorch for NCF/EmbeddingDotBias/Wide&Deep/VAE/SASRec, TensorFlow for RBM/DeepRec/NewsRec-style models.
2. Confirm CPU or GPU execution budget. Many notebooks are written for GPU but can be slow on CPU even when the framework imports.
3. Prepare model-specific data layout: contiguous ids/files for NCF, matrices for VAE/RBM, ordered sequences and negative samples for SASRec/SSEPT, YAML hparams and iterators for DeepRec.
4. Use tiny epochs and fixture data for smoke checks; do not run full notebooks as routine validation.
5. After generating predictions/top-k candidates, route metric calls to evaluation.

## Optional workflow: NewsRec versus TF-IDF

Use this decision when a user asks for news/article recommendation.

- Choose TF-IDF when the task is item-to-item article similarity, the data is a dataframe of text fields, or no TensorFlow/MIND files are available.
- Choose NewsRec when the task requires personalized news ranking from user behavior logs and MIND-style `news`/`behaviors` files, with dictionaries/embeddings and TensorFlow available.
- If the user asks for NRMS/NAML/NPA/LSTUR but the framework or MIND files are missing, state the missing prerequisites and offer a TF-IDF baseline.

## Optional workflow: experimental model families

Experimental families can be useful, but require explicit dependency acceptance.

- Surprise: use for small explicit-rating SVD-style baselines. Requires `scikit-surprise`. Use Recommenders surprise helpers to convert predictions to dataframes.
- LightFM: use for sparse interaction matrices with optional feature matrices. Requires `lightfm`.
- Vowpal Wabbit: use for online/contextual learning. Requires the VW package/binary and compatible feature formatting.
- xLearn: use for FM/FFM workflows with LibFFM-style data. May need native build tools.
- GeoIMC/RLRMC: use for matrix completion methods requiring pymanopt-compatible dependencies.

Do not silently install or claim these dependencies; route install/tuning/deployment planning to operations-and-tuning when the user accepts the optional path.
