# Cross-cutting troubleshooting

Read this when a Surprise workflow fails before it reaches a narrower sub-skill.

## Install or import fails

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'surprise'` | The package is not installed in the active environment. | Install `scikit-surprise`, then re-run a local import smoke check. |
| Editable install fails while building extensions | Missing build/runtime dependencies such as Cython, NumPy, or SciPy. | Create a clean Python 3.10+ environment, install the package dependencies, and retry the editable install. |
| `pip check` reports conflicts | The environment has incompatible package versions. | Rebuild the environment or resolve the conflicting packages before using the skill. |

## Dataset and reader problems

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Built-in dataset loading prompts or downloads unexpectedly | The built-in cache is empty. | Use local files, dataframes, or predefined folds for automation, or pre-stage the cache and set `SURPRISE_DATA_FOLDER`. |
| `Reader` parsing errors | `line_format`, separator, or skipped-lines settings do not match the file. | Confirm the file layout and align `line_format`, `sep`, and `skip_lines`. |
| `load_from_df` seems to ignore column names | Column order, not names, controls the dataframe loader. | Pass the dataframe columns in user-item-rating order. |
| Predefined folds fail to load | One or more train/test files are missing or malformed. | Build the fold list from existing files and keep the train/test pair ordering correct. |

## Raw id and trainset confusion

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `to_inner_uid` / `to_inner_iid` raises | The id is not known to the trainset. | Check that the id exists in the trainset before converting it. |
| Prediction output uses ids you cannot map back | Raw and inner ids were mixed up. | Use raw ids at public boundaries and convert only inside `Trainset` logic. |
| Recommendation output looks incomplete | A user had no candidate items left in the anti-testset. | Seed the output map if every user key must exist. |

## Evaluation, search, and CLI problems

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `ValueError: Prediction list is empty.` | The testset was empty or prediction generation failed. | Confirm the testset is non-empty and that the algorithm was fitted before scoring. |
| FCP cannot be computed | There are not enough comparable predictions per user. | Prefer RMSE/MAE/MSE for tiny or sparse examples. |
| `Wrong CV object` | `cv` is neither `None`, an integer, nor a splitter with `split(data)`. | Use `KFold`, `ShuffleSplit`, `LeaveOneOut`, `RepeatedKFold`, `PredefinedKFold`, or an integer. |
| Search refit fails on predefined folds | `refit=True` or `refit="..."` was used with fold-loaded data. | Use `refit=False` or refit on a non-fold dataset. |
| `-reader parameter is needed` | The CLI loaded custom or predefined-fold files without a reader expression. | Pass a trusted `Reader(...)` string alongside `-load-custom` or `-folds-files`. |
| CLI `-params` or `-reader` syntax errors | The CLI evaluates those strings as Python expressions. | Quote them carefully and use trusted Python literals only. |

## Serialization and dump problems

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `dump.load` roundtrip fails | The file was not created by Surprise or the pickle is corrupted. | Write the dump into a temp directory and only load trusted files. |
| Loaded predictions do not match the originals | The algorithm or testset changed after serialization. | Reuse the same fitted model and same testset when validating the roundtrip. |

## Where to go next

- Data loading and trainset construction: [`sub-skills/data-loading/`](../sub-skills/data-loading/SKILL.md)
- Prediction algorithms and custom estimators: [`sub-skills/prediction-algorithms/`](../sub-skills/prediction-algorithms/SKILL.md)
- Evaluation, tuning, and CLI evaluation: [`sub-skills/evaluation-and-search/`](../sub-skills/evaluation-and-search/SKILL.md)
- Recommendations, ranking, and serialization: [`sub-skills/recommendation-and-analysis/`](../sub-skills/recommendation-and-analysis/SKILL.md)
