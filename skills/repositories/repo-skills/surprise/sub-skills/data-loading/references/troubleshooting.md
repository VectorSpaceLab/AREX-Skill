# Data-loading troubleshooting

Use this when `Reader`, `Dataset`, `Trainset`, built-in caches, or predefined folds behave unexpectedly.

| Symptom | Likely cause | Fix / check |
| --- | --- | --- |
| `ValueError: line_format parameter is incorrect.` | `line_format` contains a token other than `user`, `item`, `rating`, or optional `timestamp`, or omits a required token. | Use a space-separated format such as `"user item rating"`, `"user item rating timestamp"`, or `"timestamp rating item user"`. Do not put delimiters inside `line_format`. |
| `ValueError: Impossible to parse line. Check the line_format and sep parameters.` | The actual delimiter does not match `sep`, a row has too few fields, or the `timestamp` expectation is wrong. | Inspect one raw row; set `sep` to the file delimiter and align `line_format` with the column order. For headers, set `skip_lines=1`. |
| `ValueError` while casting the rating to float | The rating field is nonnumeric, or `line_format`/dataframe column order points Surprise at a user/item column as the rating. | Confirm the parsed third semantic field is numeric. In dataframes, pass `df[[user_col, item_col, rating_col]]`, not the original display order. |
| `FileNotFoundError` from `load_from_file` | The single ratings file path is wrong after shell/user expansion. | Check the path with normal filesystem tools and pass a string path to `Dataset.load_from_file(path, reader)`. |
| `ValueError: File ... does not exist.` from `load_from_folds` | One train/test file in a fold tuple is missing. | Pass `[(train_file, test_file), ...]`; verify every path exists before constructing the dataset. Even one fold must be wrapped in a list. |
| Predefined folds load but no train/test pairs appear | `PredefinedKFold().split(data)` was not used, or `folds_files` was empty. | Use `from surprise.model_selection import PredefinedKFold` and iterate `for trainset, testset in PredefinedKFold().split(data): ...`. |
| Dataframe load succeeds but users/items are strange | Column names were trusted. Surprise ignores names and reads by position. | Always slice/reorder the dataframe to `[user, item, rating]` immediately at the call site. Add an assertion such as `trainset.to_inner_uid(expected_raw_user)`. |
| `to_inner_uid`, `to_inner_iid`, `to_raw_uid`, or `to_raw_iid` raises `ValueError` | The id is not present in this trainset, the raw id type is wrong, or an inner id from another split is being reused. | Use raw ids exactly as loaded. File ids are strings; dataframe ids keep their Python values. Recompute inner ids for each trainset/split. |
| `knows_user()` or `knows_item()` returns false for an expected raw id | These methods expect inner ids, not raw ids. | Convert first: `uid = trainset.to_inner_uid(raw_uid)` then `trainset.knows_user(uid)`. |
| Built-in load waits for input | `Dataset.load_builtin(..., prompt=True)` cannot find the cached file and is asking whether to download. | In non-interactive runs, prefer local files/dataframes/folds. If download is allowed, use `prompt=False`; if offline, pre-stage the cache file. |
| Built-in data is cached in an unexpected folder | `SURPRISE_DATA_FOLDER` was unset or set after Surprise computed built-in paths. | Set `SURPRISE_DATA_FOLDER` before importing Surprise in that process. Use `get_dataset_dir()` to confirm the active data folder. |
| `ValueError: unknown dataset ...` or `unknown reader ...` | The built-in name is not one of the supported ids. | Use `"ml-100k"`, `"ml-1m"`, or `"jester"`, or configure a custom `Reader` manually. |
| Zero or negative ratings disappear | Upstream preprocessing filtered them, or code assumed zero means missing. Surprise's data layer itself preserves them. | Use `rating_scale` that covers the values, load through file/df, and inspect `list(trainset.all_ratings())` or `trainset.ur`/`ir` for `0` or negative ratings. |
| Timestamp values are unavailable in a testset | `construct_testset()` drops timestamps and returns `(raw_uid, raw_iid, rating)` triples. | Keep a separate copy of timestamp metadata if downstream code needs it; Surprise's standard testsets do not carry timestamps. |
| `build_anti_testset()` ratings are not what you expected | `fill=None` uses `trainset.global_mean`; a numeric `fill` is cast to float. | Pass an explicit `fill` if a sentinel is needed, e.g. `trainset.build_anti_testset(fill=0)`. |

## Quick self-checks

From this sub-skill directory:

```bash
python scripts/load_custom_file_smoke.py
python scripts/load_from_dataframe_smoke.py
python scripts/load_predefined_folds_smoke.py
```

These scripts intentionally exercise malformed separator, dataframe column-order, and missing-fold cases while keeping all data in temporary files or memory.
