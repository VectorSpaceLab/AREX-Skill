# Data Preparation Workflows

## Purpose

Use these recipes to move from a user's raw recommendation data to model-ready and metric-ready dataframes without reopening source notebooks.

## Validate a user interaction CSV

1. Inspect columns and a few rows.
2. Decide the intended workflow: explicit rating prediction, implicit top-k ranking, chronological evaluation, Spark-scale data, or content-based recommendation.
3. Run the bundled validator:

```bash
python sub-skills/data-preparation/scripts/validate_interactions.py --input interactions.csv --require-rating --require-timestamp --min-interactions-per-user 2
```

4. Fix reported column, null, duplicate, or minimum-interaction issues before training.
5. Route model choice to the modeling sub-skill and metrics to the evaluation sub-skill.

## Create a quick pandas train/test split

```python
from recommenders.datasets.python_splitters import python_random_split

train, test = python_random_split(interactions, ratio=0.75, seed=42)
```

Use this for smoke tests or examples where temporal order does not matter.

## Create a chronological split

```python
from recommenders.datasets.python_splitters import python_chrono_split

train, test = python_chrono_split(
    interactions,
    ratio=0.75,
    min_rating=2,
    filter_by="user",
    col_user="userID",
    col_item="itemID",
    col_timestamp="timestamp",
)
```

Use this when timestamps encode real order. If the user has no timestamp column, do not invent one; use random or stratified splitting.

## Create a stratified split

```python
from recommenders.datasets.python_splitters import python_stratified_split

train, test = python_stratified_split(
    interactions,
    ratio=0.75,
    min_rating=2,
    filter_by="user",
    col_user="userID",
    col_item="itemID",
    seed=42,
)
```

Use this when each user needs train/test representation. Increase `min_rating` only when the data has enough observations per user or item.

## Filter sparse users/items first

```python
from recommenders.datasets.split_utils import min_rating_filter_pandas, filter_k_core

filtered = min_rating_filter_pandas(interactions, min_rating=2, filter_by="user")
core = filter_k_core(filtered, core_num=2, col_user="userID", col_item="itemID")
```

Filtering changes the evaluation population. Tell the user when cold-start users/items are removed.

## Build candidate pairs and negative samples

```python
from recommenders.datasets.pandas_df_utils import user_item_pairs, negative_feedback_sampler

candidates = user_item_pairs(users, items, user_col="userID", item_col="itemID")
training = negative_feedback_sampler(
    positives,
    col_user="userID",
    col_item="itemID",
    col_label="label",
    col_feedback="feedback",
    ratio_neg_per_user=1,
    seed=42,
)
```

Use negative sampling for implicit-feedback classification/ranking workflows. Keep the positive label convention stable across model and metric steps.

## Convert to sparse matrix

```python
from recommenders.datasets.sparse import AffinityMatrix

affinity = AffinityMatrix(interactions, col_user="userID", col_item="itemID", col_rating="rating")
X, users, items = affinity.gen_affinity_matrix()
```

Keep `users` and `items` mappings if the model output needs conversion back to ids.

## Convert to LibFFM

```python
from recommenders.datasets.pandas_df_utils import LibffmConverter

converter = LibffmConverter(filepath="train.libffm")
libffm_rows = converter.fit_transform(features, col_rating="rating")
```

Use this for factorization-machine style workflows. Validate categorical and numeric feature columns first.

## Prepare content metadata for TF-IDF

For content-based recommendations, validate that the item id column is unique and text columns are non-empty. Then route to the modeling sub-skill's TF-IDF workflow.

## Spark preparation path

Use Spark splitters only after verifying `[spark]`, Java, and Spark runtime. The workflow is similar to pandas splitters, but the input and output are Spark dataframes and downstream metrics/models must also be Spark-aware.
