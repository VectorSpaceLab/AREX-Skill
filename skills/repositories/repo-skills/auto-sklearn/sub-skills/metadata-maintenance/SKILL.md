---
name: metadata-maintenance
description: "Maintain auto-sklearn meta-learning metadata, AutoSklearn2
  selector and portfolio context, metadata_directory usage, regeneration
  planning, submodule checks, and focused repository test workflows safely."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# Metadata Maintenance

Use this sub-skill when the user asks about maintaining meta-learning metadata,
`metadata_directory`, AutoSklearn2 selector or portfolio files, metadata
regeneration scripts, ASLib outputs, the `automl_common` submodule, or focused
repository maintenance and test workflows around those areas.

Do **not** use this sub-skill for ordinary estimator usage, input validation,
metrics, search limits, parallelism, or custom components. Route those requests
to the sibling operating areas for estimators, data/metrics/validation,
search/parallelism, or custom components. Historical NIPS benchmark scripts are
reference-only context; do not present them as bundled runnable helpers.

## Safety contract

- Default to **plan-only**. A full metadata refresh depends on OpenML account and
  network access and on long AutoML runs; it is not safe for a normal short
  Researcher task.
- Never launch OpenML downloads, metadata-generation AutoML jobs, full ASLib
  regeneration, or full pytest unless the user explicitly approves the runtime,
  network, disk, and dirty-tree implications.
- Prefer the bundled dry helper [`scripts/metadata_command_template.py`](scripts/metadata_command_template.py)
  to produce explicit commands or JSON plans from known task IDs and metrics. It
  does not import auto-sklearn, contact OpenML, or run AutoML.
- Treat generated metadata files as repository artifacts: verify layout, inspect
  diffs, and keep the working tree clean after tests.

## Operating facts to preserve

- The installed package imports as `autosklearn`; the inspected development
  version reported `0.16.0dev` / `0.16.0.dev0`.
- `AutoSklearnClassifier` and `AutoSklearnRegressor` accept
  `initial_configurations_via_metalearning` and `metadata_directory`; when
  `metadata_directory=None`, packaged metadata is used.
- `AutoSklearn2Classifier` lives under `autosklearn.experimental.askl2`, trains
  or loads local selector pickles for supported metrics, selects one of several
  portfolio strategies, and intentionally passes `metadata_directory=None` to
  its parent classifier.
- AutoSklearn2 selector training data uses only `NumberOfFeatures` and
  `NumberOfInstances` as selector meta-features for its packaged strategy
  choice. Its portfolio JSON files are metric-specific.
- The bundled ASLib-style metadata directories contain combinations of metric,
  task family, and density, each with files such as `algorithm_runs.arff`,
  `configurations.csv`, `description.txt`, `feature_costs.arff`,
  `feature_runstatus.arff`, `feature_values.arff`, and `readme.txt`.
- The `autosklearn.automl_common` package area is a git submodule and must be
  initialized for source-tree maintenance and contributor tests.

## Fast decision flow

1. **Classify the request.**
   - User wants to run or use AutoML normally: route elsewhere.
   - User wants to change metadata task lists, scripts, ASLib files, selector
     data, portfolio data, or repository tests: continue here.
2. **Decide whether execution is safe.**
   - If the task asks for a complete refresh, respond with a safe plan first and
     require explicit approval for OpenML/network/long-run execution.
   - If the task is a contributor edit to scripts or selector code, prepare
     focused static checks and narrow pytest commands before any expensive test.
3. **Load bundled references as needed.**
   - Metadata and ASLib pipeline: [`references/metadata-workflows.md`](references/metadata-workflows.md)
   - Contributor/submodule/test guidance: [`references/repo-maintenance.md`](references/repo-maintenance.md)
   - Failure diagnosis: [`references/troubleshooting.md`](references/troubleshooting.md)
4. **Use the dry helper for command planning.**
   ```bash
   python scripts/metadata_command_template.py --help
   python scripts/metadata_command_template.py \
     --task-type classification \
     --task-id 245 \
     --metric balanced_accuracy \
     --working-directory ./metadata-work \
     --format json
   ```
5. **Verify outputs before suggesting replacement.** For metadata runs, check
   the working-directory layout and required ASLib files. For maintenance tests,
   confirm that submodules import, focused checks pass, and generated files are
   removed or intentionally committed.

## Common later workflows

### Produce a safe plan instead of refreshing metadata

Use this when the user asks to update meta-learning datasets, add metrics, or
rerun metadata generation but has not provided a long-running execution window.
Collect explicit task IDs and metrics, then run the bundled helper with
`--format json` or command output. State that the plan is dry and that the broad
metadata generator normally expands large task lists and may create many
one-day-per-task/metric commands.

### Prepare focused tests for a metadata-script contributor

Use this when a contributor edits metadata scripts, ASLib reading/writing,
AutoSklearn2 selector code, or the submodule boundary.

- Run cheap static inspections first: parser help, import checks, and format or
  type checks scoped to changed files if the project tooling is available.
- Use pytest selectors such as `-k "metadata_generation or metalearning or selector"`
  only after warning that the metadata-generation test can contact OpenML and
  run bounded AutoML jobs.
- Use the repository pytest defaults: tests live under `test`, pytest is run with
  `--forked`, CI adds `--timeout=600 --timeout-method=thread -s`, and CI checks
  for dirty generated files after tests.
