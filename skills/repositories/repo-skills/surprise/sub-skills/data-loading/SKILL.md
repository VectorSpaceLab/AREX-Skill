---
name: data-loading
description: "Load, inspect, validate, and split Surprise rating datasets."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# Surprise data loading

Use this sub-skill when the task is to load ratings into Surprise, inspect the resulting `Trainset`, diagnose parser/layout errors, or prepare train/test material from local data. It is intentionally about data ingestion and trainset construction only.

## Fast route

1. Identify the data source:
   - Built-in cache/download: `Dataset.load_builtin(name, prompt=...)`.
   - One ratings file: `Reader(...)` + `Dataset.load_from_file(file_path, reader)`.
   - Pandas dataframe: `Reader(rating_scale=...)` + `Dataset.load_from_df(df[[user, item, rating]], reader)`.
   - Predefined train/test files: `Dataset.load_from_folds([(train_file, test_file), ...], reader)` + `PredefinedKFold().split(data)`.
2. Validate the layout before using an algorithm: check `Reader.line_format`, `sep`, `skip_lines`, dataframe column order, and fold file existence.
3. Build or materialize trainsets:
   - Full local dataset: `trainset = data.build_full_trainset()`.
   - Predefined folds: iterate `for trainset, testset in PredefinedKFold().split(data): ...`.
4. Use raw ids at public prediction/testset boundaries and inner ids only for `Trainset` internals. Convert with `to_inner_uid`, `to_inner_iid`, `to_raw_uid`, and `to_raw_iid`.
5. For details, read [`references/data-loading.md`](references/data-loading.md). For errors, read [`references/troubleshooting.md`](references/troubleshooting.md).

## API selection

| Need | Use | Contract to remember |
| --- | --- | --- |
| Built-in MovieLens/Jester data | `Dataset.load_builtin("ml-100k" | "ml-1m" | "jester")` | May prompt/download if the cache file is absent; cache root comes from `get_dataset_dir()` / `SURPRISE_DATA_FOLDER`. |
| Custom delimited file | `Reader(line_format=..., sep=..., rating_scale=..., skip_lines=...)` then `Dataset.load_from_file(...)` | `line_format` tokens are space-separated field names; `sep` is the actual delimiter in the file. |
| Dataframe | `Dataset.load_from_df(df[[user_col, item_col, rating_col]], reader)` | Column names are ignored; positional order must be user, item, rating. Only `rating_scale` is needed on the reader. |
| Existing train/test folds | `Dataset.load_from_folds(folds_files, reader)` | `folds_files` is a list of `(train_file, test_file)` tuples, and every path must exist up front. |
| Trainset inspection | `n_users`, `n_items`, `n_ratings`, `ur`, `ir`, `all_ratings()`, `build_testset()`, `build_anti_testset()` | `ur`, `ir`, `all_*`, and `knows_*` use inner ids; `build_*testset()` returns raw ids. |

## Bundled smoke scripts

Run these from this sub-skill directory after installing Surprise and any script-specific dependency:

- `python scripts/load_custom_file_smoke.py` — creates a temporary ratings file, loads it with `Reader`/`load_from_file`, checks zero-rating preservation, and verifies a wrong separator fails.
- `python scripts/load_from_dataframe_smoke.py` — creates a tiny dataframe, loads it with explicit column ordering, and checks the bad-ordering trap.
- `python scripts/load_predefined_folds_smoke.py` — creates temporary train/test fold files, loads them with `load_from_folds`, materializes `PredefinedKFold`, and checks nonexistent fold paths fail early.

## Boundaries

This sub-skill excludes algorithm choice, similarity math, cross-validation metrics/search, top-N recommendation generation, and model serialization. Use sibling sub-skills for those tasks: [`../prediction-algorithms/`](../prediction-algorithms/), [`../evaluation-and-search/`](../evaluation-and-search/), and [`../recommendation-and-analysis/`](../recommendation-and-analysis/).
