# Data Preparation API Reference

## Purpose

Read this when you need concrete Recommenders dataset, splitter, dataframe, sparse, and conversion API names. Signatures below were verified from an installed base package inspection for Recommenders 1.2.1.

## Default column names

Most Python workflows default to:

| Meaning | Default column |
|---|---|
| User id | `userID` |
| Item id | `itemID` |
| Explicit or implicit rating/feedback | `rating` |
| Event time | `timestamp` |
| Model score | `prediction` |

Prefer these defaults unless the user's data already has clear custom names. If custom names are used, pass the matching `col_user`, `col_item`, `col_rating`, `col_timestamp`, or related parameters consistently across splitters, models, and metrics.

## Dataset loaders and download helpers

- `recommenders.datasets.movielens.load_pandas_df(size='100k', header=None, local_cache_path=None, title_col=None, genres_col=None, year_col=None)` loads MovieLens ratings into pandas and can optionally include item metadata columns.
- `recommenders.datasets.movielens.load_spark_df(...)` is the Spark variant and needs the Spark extra/runtime.
- `recommenders.datasets.movielens.MockMovielensSchema()` creates small MovieLens-like data for tests and examples without downloading the full public dataset.
- `recommenders.datasets.criteo.load_pandas_df(...)` and `load_spark_df(...)` cover Criteo tabular click data; Spark loading needs `[spark]`.
- `recommenders.datasets.mind` provides MIND news data download/extraction and news/user-history preprocessing helpers.
- `recommenders.datasets.amazon_reviews` provides Amazon Reviews download/preprocessing for sequential recommendation data.
- `recommenders.datasets.covid_utils` provides CORD-19 dataframe cleaning/text retrieval helpers used by TF-IDF content recommendation.
- `recommenders.datasets.wikidata` provides Wikidata lookup helpers for knowledge-graph enrichment; expect network/API constraints.
- `recommenders.datasets.download_utils.maybe_download`, `is_valid_zip`, `download_path`, and `unzip_file` are general download/cache helpers. Treat them as network/file-system utilities, not pure transformations.

## Python splitter signatures

- `python_random_split(data, ratio=0.75, seed=42)` returns train/test pandas dataframes by random row split.
- `python_chrono_split(data, ratio=0.75, min_rating=1, filter_by='user', col_user='userID', col_item='itemID', col_timestamp='timestamp')` orders by timestamp after optional minimum-interaction filtering.
- `python_stratified_split(data, ratio=0.75, min_rating=1, filter_by='user', col_user='userID', col_item='itemID', seed=42)` preserves representation by user or item.
- `numpy_stratified_split(X, ratio=0.75, seed=42)` stratifies array-like interaction matrices.

Use chronological splitting for time-aware evaluation and sequential models. Use stratified splitting when every user or item should have train/test coverage. Use random splitting for tiny smoke tests where order does not matter.

## Split utilities

- `process_split_ratio(ratio)` validates split ratios and multiple splits.
- `min_rating_filter_pandas(data, min_rating=1, filter_by='user', col_user='userID', col_item='itemID')` removes users or items with too few ratings.
- `filter_k_core(data, core_num=0, col_user='userID', col_item='itemID')` applies k-core style filtering.
- `split_pandas_data_with_ratios(data, ratios, seed=42, shuffle=False)` underlies multi-way split handling.

## Dataframe utilities

- `user_item_pairs(user_df, item_df, user_col='userID', item_col='itemID', user_item_filter_df=None, shuffle=True, seed=None)` creates candidate pairs while optionally filtering seen pairs.
- `filter_by(data, filter_by_df, filter_by_cols)` keeps rows matching another dataframe.
- `negative_feedback_sampler(df, col_user='userID', col_item='itemID', col_label='label', col_feedback='feedback', ratio_neg_per_user=1, n_neg_per_user=None, pos_value=1, neg_value=0, seed=42)` samples negative user-item pairs for implicit-feedback classification/ranking tasks.
- `has_columns(df, columns)` and `has_same_base_dtype(df_1, df_2, columns=None)` are useful before metric/model calls.
- `PandasHash` and `lru_cache_df` support dataframe hashing/caching patterns.

## LibFFM conversion

`LibffmConverter(filepath=None)` converts pandas data into libffm-style rows:

- `fit(df, col_rating='rating')` learns feature-field mappings.
- `transform(df)` converts another dataframe with the learned mapping.
- `fit_transform(df, col_rating='rating')` does both.
- `get_params()` returns learned conversion metadata.

Use this when workflows need field-aware factorization machine data. Validate that the rating/label column and categorical/numerical columns are present before conversion.

## Sparse affinity matrices

`AffinityMatrix(df, items_list=None, col_user='userID', col_item='itemID', col_rating='rating', col_pred='prediction', save_path=None)` maps user-item dataframes to sparse matrices.

Key methods:

- `gen_affinity_matrix()` builds a sparse user-by-item matrix.
- `map_back_sparse(X, kind)` maps sparse predictions or ratings back into dataframe form. Use the correct `kind` for ratings versus predictions.

Sparse conversion is useful before VAE/RBM-style workflows and when a model expects matrix input instead of long-form interactions.

## Optional Spark data APIs

The package also exposes Spark splitters and Spark dataset loaders. Treat these as optional until the runtime has:

1. `recommenders[spark]` installed.
2. A compatible Java/JDK runtime.
3. A working local or cluster Spark session.
4. Dataset sizes appropriate for the Spark job.

Do not use a successful pandas split as proof that Spark splitters work.
