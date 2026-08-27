# Metadata Workflows

This reference explains the meta-learning metadata, AutoSklearn2 selector and
portfolio context, `metadata_directory`, and the large metadata regeneration
pipeline. It is meant for planning and maintenance; it is not a green light to
run a full refresh in a normal task.

## User-facing metadata knobs

| Surface | Meaning | Maintenance notes |
|---|---|---|
| `initial_configurations_via_metalearning` | Number of SMAC initial configurations proposed from meta-learning. Defaults to a positive value for classic estimators. | Set to `0` for a vanilla search or for metadata-generation runs that must not bootstrap from the metadata being regenerated. |
| `metadata_directory` | Directory containing ASLib-style metadata used by classic auto-sklearn meta-learning. `None` means use packaged metadata. | Custom directories must match the bundled ASLib layout and metric/task/density naming. A mismatch usually surfaces as missing files or no usable configurations. |
| `dataset_name` passed to `fit` | Classic metadata can ignore a dataset with the same name as the current dataset to avoid leakage. | Preserve stable lowercase dataset names when regenerating metadata; name mismatches can defeat exclusion. |
| `AutoSklearn2Classifier` | Experimental classifier that chooses a portfolio strategy through a selector. | It does not expose `metadata_directory`; selector/portfolio data is packaged under metric-specific data files and selector pickles are cached per version/sklearn/metric/data hash. |

## Classic meta-learning internals

Classic meta-learning reads an ASLib problem for the current metric, task type,
and sparsity. The loaded problem supplies dataset meta-features,
algorithm/configuration runs, and concrete configurations. The meta-learner then
uses distance-based nearest datasets and returns suggested configurations for
SMAC.

Important invariants:

- Multilabel classification is treated as multiclass for metadata lookup.
- The ASLib reader requires `algorithm_runs.arff` and `feature_values.arff`; it
  can also read `configurations.csv`, `feature_costs.arff`, and related optional
  files.
- Configuration values are completed from the current configuration-space
  defaults and inactive hyperparameters are deactivated before use.
- When adding a new dataset to a meta-base, an existing lowercased dataset name
  is removed first, which is how classic metadata avoids same-dataset leakage.

## AutoSklearn2 selector and portfolio context

`AutoSklearn2Classifier` uses a different mechanism from classic
`metadata_directory` metadata.

- Supported selector metrics are `balanced_accuracy`, `roc_auc`, and `log_loss`.
- Each selector metric has training data with keys for `metafeatures`,
  `strategies`, `y_values`, per-method minima/maxima, tie-break order, and
  selector configuration.
- The selector meta-feature table contains `NumberOfFeatures` and
  `NumberOfInstances`; predictions choose a strategy for the dataset shape.
- The selected strategy determines resampling (`holdout-iterative-fit` or
  `cv-iterative-fit` with 3/5/10 folds) and whether Successive Halving is used.
- The strategy name selects a matching portfolio JSON file. The portfolio is
  passed through a SMAC callback, either standard portfolio seeding or the
  Successive Halving variant.
- Selector pickles are cached under a user cache location keyed by package
  version, scikit-learn version, metric, and training-data hash. If the cache is
  unwritable, selector creation can fail before fitting.
- AutoSklearn2 restricts the classifier include list to selected estimators and
  `no_preprocessing`, sets `initial_configurations_via_metalearning=0`, and
  passes `metadata_directory=None`.

## Metadata regeneration pipeline

The broad source workflow has a script-readme recipe and four numbered stages,
plus the AutoML runner and task-list utility. Treat it as a production workflow,
not as a local smoke test.

### Inputs and task lists

The task-list utility defines large `classification_tasks` and `regression_tasks`
OpenML task ID lists and a `load_task(task_id)` helper that downloads an OpenML
task, returns train/test splits, feature-type metadata, task type, and a
lowercase dataset name. Changing these lists changes the scope of generated
metadata.

Before running anything, record:

- task family: `classification` or `regression`;
- exact OpenML task IDs;
- exact metrics;
- working directory;
- total time limit, per-run time limit, seed, memory limit, and whether this is
  a unit-test-scale run;
- expected output owner and whether generated metadata should replace packaged
  files.

### Stage 1: create commands

The command-generation script writes `metadata_commands.txt` under the working
directory. The current script can use a test subset and otherwise expands the
large task lists for both classification and regression. The generated commands
call the AutoML runner with production defaults of `--time-limit 86400`,
`--per-run-time-limit 1800`, `--task-id`, `-s 1`, and a metric.

Because command generation may contact OpenML to inspect classification labels,
use the bundled dry helper first when you only need a plan:

```bash
python scripts/metadata_command_template.py \
  --task-type classification \
  --task-id 245 \
  --metric balanced_accuracy \
  --working-directory ./metadata-work
```

### Stage 2: run AutoML for configuration generation

The runner loads one OpenML task, builds an AutoSklearn classifier or regressor,
and writes configuration evidence for a single task/metric/seed. Key runner
settings:

- `initial_configurations_via_metalearning=0` to avoid circular metadata use;
- ensemble disabled (`ensemble_class=None`, `ensemble_nbest=0`);
- `resampling_strategy="partial-cv"`;
- production uses 10 folds; unit-test mode uses 2 folds and a restricted include
  list;
- `disable_evaluator_output=True` during the search;
- after the trajectory, each incumbent is validated on the test split with all
  classification or regression scorers;
- validated trajectory JSON is written under
  `configuration/<task-family>/<task-id>/<metric>/validation_trajectory_<seed>.json`;
- trimmed AutoML output is copied beside the validation trajectory.

A production run can take roughly a day per task/metric command and the FAQ
summarizes the whole metadata-generation process as two days per dataset across
metrics. Do not start this stage without explicit approval.

### Stage 3: retrieve metadata

The retrieval script scans validation trajectories under
`configuration/<task-family>/`, keeps the best non-default configuration per
metric/dataset, and writes per-combination outputs under
`configuration_results/<metric>_<task-kind>_<dense-or-sparse>/`:

- `algorithm_runs.arff`
- `configurations.csv`
- `description.results.txt`

It skips combinations with no outputs. Missing `validation_trajectory_*.json`
files therefore produce empty or missing result directories rather than a clean
ASLib package.

### Stage 4: calculate meta-features

The metafeature script reloads OpenML tasks, computes raw and encoded
meta-features, caches calculations through joblib, and writes under
`metafeatures/<task-family>/`:

- `calculation_times.csv`
- `description.features.txt`
- `feature_costs.arff`
- `feature_runstatus.arff`
- `feature_values.arff`

Unit-test mode limits to the first task in each family. Production mode shuffles
and processes all task IDs. Network and OpenML cache state are required.

### Stage 5: create ASLib files

The ASLib script combines retrieved results and metafeatures into final
metadata directories under `metadata/<metric>_<task-kind>_<dense-or-sparse>/`.
Each complete output directory should contain:

- `algorithm_runs.arff`
- `configurations.csv`
- `description.txt`
- `feature_costs.arff`
- `feature_runstatus.arff`
- `feature_values.arff`
- `readme.txt`

The script rounds feature costs, merges feature and result descriptions, adds
scenario metadata, and skips combinations whose results directory does not
exist.

## Minimal ASLib validation checklist

Use this checklist before suggesting that generated metadata can replace
packaged metadata:

1. For every expected metric/task/density combination, check that the final
   metadata directory exists or that its absence is intentionally documented.
2. Confirm required files: `algorithm_runs.arff`, `feature_values.arff`, and
   `description.txt`; strongly prefer all seven files listed above.
3. Inspect `algorithm_runs.arff` attributes: `instance_id`, `repetition`,
   `algorithm`, metric column, `runstatus`.
4. Inspect `feature_values.arff` for dataset names matching the generated
   trajectories and metafeatures.
5. Confirm `configurations.csv` has an `idx` column and hyperparameter columns
   from the active configuration space.
6. Load one final directory through the ASLib reader in a controlled environment
   before replacing packaged files.
7. Review git diff size and generated-file ownership; do not commit temporary
   `configuration`, `configuration_results`, or raw working-directory outputs by
   accident.
