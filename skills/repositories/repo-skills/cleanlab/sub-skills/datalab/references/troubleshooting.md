# Datalab troubleshooting

## Install and import issues

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `Datalab is not available...` | Optional Datalab dependencies are missing. | Install `cleanlab[datalab]` or `cleanlab[all]`. |
| `Cannot import required image packages...` | CleanVision/image extras are missing. | Install `cleanlab[image]` or `cleanlab[all]`. |
| `Please pass a single dataset, not a DatasetDict.` | A split was not selected from a Hugging Face dataset. | Pass one split, not the full `DatasetDict`. |
| `Label column '...' not found in dataset.` | `label_name` is wrong or missing. | Set `label_name` to the real label column. |
| `Invalid task: ...` | Task string is not supported. | Use `classification`, `regression`, or `multilabel`. |

## Audit configuration issues

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `No issue types were specified...` | `issue_types={}` was passed. | Pass `None` for defaults or a non-empty dict of issue types. |
| `Invalid issue type: ... for task ...` | Typo, unsupported workflow, or unregistered custom manager. | Check `list_possible_issue_types()` and register custom managers first. |
| `Either pred_probs or features must be provided to find label issues.` | Regression/classification label workflow lacks model output. | Pass `pred_probs` or `features` as required by the task. |
| `pred_probs must be a 2D array...` | Classification / multilabel probabilities have the wrong shape. | Pass a 2D array. For regression, pass a 1D prediction vector. |
| `knn_graph is provided, but not sufficiently large...` | A sparse graph with too few neighbors was supplied for the requested k. | Increase the graph density or lower the requested `k`. |
| `No labels were provided. The 'label' issue type will not be run.` | Unlabeled audit. | Expected for unlabeled data; use only feature-based checks. |
| `features must be provided to check for null values.` | Null issue was requested without features. | Pass a feature matrix. |
| `Expected labels to be a numpy array...` when using `data_valuation` on multilabel data | The current manager expects NumPy labels, but multilabel Datalab stores list-of-lists labels. | Use classification/regression for `data_valuation`, or verify the multilabel path before depending on it. |

## Image-specific issues

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `image_key` confusion | The image column is not a Hugging Face image column. | Use a `datasets.Dataset` and point `image_key` at the PIL image field. |
| `image_issue_types` does nothing | The nested dict was omitted. | Use `issue_types={"image_issue_types": {...}}`. |
| `Spurious correlations have not been calculated...` | Correlation info was requested too early. | Run image-property checks first, then request `spurious_correlations`. |
| Spurious correlations not shown in `issue_summary` | This is expected. | Read `lab.get_info("spurious_correlations")` instead. |

## Readout and reporting issues

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `No issues available for retrieval...` | `find_issues()` never completed successfully. | Fix the earlier error and rerun `find_issues()`. |
| `No columns found for issue type '...'` | That issue type was not run or failed. | Verify the issue was included and finished successfully. |
| `Issue type ... not found in the summary.` | The issue was not added to the summary table. | Check the `find_issues()` run and the task/inputs. |
| `report()` shows no issue sections | The summary is empty or all rows are filtered out. | Run `find_issues()` with real issue types or call `show_all_issues=True`. |
| Scores look inconsistent | Dataset-level and per-example scores are being compared directly. | Compare only scores from the same issue type. |

## Custom manager mistakes

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Class creation fails immediately | `issue_name` is missing. | Define `issue_name` on the subclass. |
| Verbosity errors | `verbosity_levels` contains non-lists or non-strings. | Use a dict of ints to lists of strings. |
| `make_summary()` errors | The summary score is outside `[0, 1]`. | Normalize your score before calling `make_summary()`. |
| Duplicate manager warning | The custom `issue_name` already exists. | Use a unique name or accept the overwrite explicitly. |
| Report section is missing | The manager never populated `self.issues` / `self.summary`. | Make sure `find_issues()` sets both before returning. |

## Quick interpretation reminders

- Per-example scores help you sort and inspect records.
- Dataset-level summary scores tell you how severe an issue is overall.
- Lower scores mean more severe issues.
- For `non_iid`, `class_imbalance`, `underperforming_group`, and `spurious_correlations`, the summary is usually more important than any single row.
