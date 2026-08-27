# Metadata Troubleshooting

Use this matrix when metadata maintenance or focused tests fail. Prefer diagnosis
and a safe plan over rerunning the full metadata pipeline.

| Symptom | Likely cause | Safe response |
|---|---|---|
| OpenML task loading fails, hangs, or asks for credentials | Metadata scripts depend on OpenML package configuration, network access, and sometimes account/API setup. | Do not retry indefinitely. Confirm network/account approval, run only a tiny approved task subset, and document unavailable OpenML as a blocker for regeneration. |
| Command list is enormous or would run for days | Broad metadata generation expands many classification/regression OpenML task IDs and multiple metrics; production commands use one-day total limits and long per-run limits. | Stop and produce a dry plan. Ask for approved task IDs, metrics, machine budget, and whether the goal is evidence collection or packaged metadata replacement. |
| Working-directory pipeline stages cannot find inputs | Stage output layout mismatch: commands write `configuration/...`, retrieval writes `configuration_results/...`, metafeatures writes `metafeatures/...`, final ASLib writes `metadata/...`. | Inspect the working directory tree and compare it to the stage layout in `metadata-workflows.md`. Do not rerun all stages until the missing predecessor output is identified. |
| `04`-style ASLib assembly reports missing result directories | Retrieval skipped combinations with no usable validation trajectories or no best configurations. | Check whether the task/metric/density combination was generated, whether `validation_trajectory_*.json` exists, and whether the absence should be documented. |
| Final ASLib directory is missing files | Earlier stage failed or the assembly skipped a combination. Required files include `algorithm_runs.arff`, `feature_values.arff`, and `description.txt`; complete packages also include `configurations.csv`, `feature_costs.arff`, `feature_runstatus.arff`, and `readme.txt`. | Do a file checklist per output directory. Regenerate only the missing predecessor stage if approved. |
| Classic estimator ignores custom metadata or raises metadata loading errors | `metadata_directory` points to the wrong level, has metric/task/density naming mismatch, or lacks ASLib files. | Point `metadata_directory` at the parent containing ASLib-style subdirectories, then load one directory through the ASLib reader before a full estimator fit. |
| AutoSklearn2 fails before fitting with selector-cache errors | Selector pickle cache location is not writable, or selector data/version hash changed and retraining is required. | Set a writable user cache location for the process, or pre-create/cache selectors in an approved environment. Do not edit classic `metadata_directory` expecting AutoSklearn2 to use it. |
| AutoSklearn2 portfolio selection gives unexpected resampling | Selector chose one of the packaged strategies based on number of features and instances and the selected metric. | Inspect metric, dataset shape, selected strategy, and portfolio filename. Remember unsupported metrics fall back to the balanced-accuracy selector. |
| `automl_common` imports fail | Submodule not initialized or checked out at the wrong commit. | Run submodule status. If uninitialized or mismatched, update submodules before debugging Python code. |
| Full pytest is very slow or appears stuck | Metadata tests can contact OpenML and run bounded AutoML; CI permits long timeouts. | Use focused `-k` selectors or `--last-failed`. Ask before full pytest. Apply BLAS thread limits for parallelism stability. |
| CI fails due to dirty tree after tests | Metadata/test runs left generated files or cache output. | Compare `git status --porcelain` before/after. Delete temporary generated files or explicitly keep intentional artifacts. |
| ConfigSpace or NumPy ABI import error | Binary dependencies are incompatible in the active environment. | Rebuild or reinstall compatible dependency versions. A known working maintenance environment used NumPy 1.26.x for ConfigSpace ABI compatibility; avoid leaking environment-specific paths. |
| `roc_auc` commands fail for multiclass tasks | The broad command generator skips ROC AUC for tasks whose OpenML classification labels are not binary. | Filter task IDs/metrics explicitly. For a dry plan, remove `roc_auc` unless the task is known binary. |
| Results contain default-only or invalid configurations | The runner intentionally skips the default configuration and only records valid configurations that improved the trajectory. Too-small budgets can leave no usable configuration. | Increase approved budget or mark the combination missing; do not fabricate ASLib entries. |

## Triage order

1. Confirm the user approved network, OpenML, runtime, and disk usage.
2. Identify the exact stage and working-directory layout.
3. Check submodule status and imports if source maintenance is involved.
4. Validate the smallest file set or parser help before rerunning expensive jobs.
5. Use the dry helper to rebuild explicit commands and compare them to what was
   actually run.
6. Inspect dirty-tree state before handoff.

## Signals that a full refresh is not appropriate

- The user only asked for guidance, review, or a command plan.
- No OpenML account/network permission was granted.
- No task IDs or metrics were specified.
- The environment budget is shorter than the metadata-generation run limits.
- The working tree already has unexpected generated files.
- The purpose is ordinary AutoML use rather than maintaining packaged metadata.
