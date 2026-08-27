# HPO API Reference

This reference focuses on stable, commonly used NNI HPO experiment surfaces.

## Trial APIs

Import from `nni` inside trial code.

| API | Use | Notes |
| --- | --- | --- |
| `nni.get_next_parameter()` | Receive one sampled hyperparameter set from the tuner. | Each trial should call it once; repeated calls are undefined. |
| `nni.get_next_parameters()` | Alias of `get_next_parameter()`. | Prefer singular spelling in new code. |
| `nni.get_current_parameter(tag=None)` | Read the cached current parameter set or one key after `get_next_parameter()`. | Returns `None` before parameters are received. |
| `nni.report_intermediate_result(metric)` | Send per-epoch or periodic metric to NNI. | Metric can be numeric or a dict with numeric `default`. Assessors consume this stream. |
| `nni.report_final_result(metric)` | Send final optimization result to NNI. | Metric can be numeric or a dict with numeric `default`; tuners consume this result. |
| `nni.get_experiment_id()` | Return experiment ID for logging. | Standalone runs return a standalone marker. |
| `nni.get_trial_id()` | Return current trial job ID for logging. | Displayed in the web portal trial table. |
| `nni.get_sequence_id()` | Return current trial sequence number. | Useful for naming outputs. |

Metric rules:

- Built-in tuners optimize a scalar reward. A plain `int` or `float` is accepted.
- A dict metric should include numeric `default`; extra keys are auxiliary visualization data.
- If an assessor is configured, report useful intermediate values consistently and in the same direction as `optimize_mode`.
- If trial code parses CLI defaults, merge NNI parameters into defaults before model construction.

## Experiment And Config APIs

Core imports:

```python
from nni.experiment import Experiment
from nni.experiment.config import ExperimentConfig
```

Typical construction:

```python
config = ExperimentConfig('local')
config.search_space = {'x': {'_type': 'uniform', '_value': [0, 1]}}
config.trial_command = 'python3 train.py'
config.trial_code_directory = '.'
config.trial_concurrency = 1
config.max_trial_number = 10
config.tuner.name = 'random'
experiment = Experiment(config)
experiment.run(8080)
```

High-value fields:

| YAML field | Python property | Purpose |
| --- | --- | --- |
| `experimentName` | `experiment_name` | Display name in WebUI and CLI. |
| `searchSpaceFile` | `search_space_file` | Path to JSON/YAML search space file. Mutually exclusive with `searchSpace`. |
| `searchSpace` | `search_space` | Inline search-space object. Mutually exclusive with `searchSpaceFile`. |
| `trialCommand` | `trial_command` | Shell command for each trial. |
| `trialCodeDirectory` | `trial_code_directory` | Directory whose files are sent to the training service. |
| `trialConcurrency` | `trial_concurrency` | Requested concurrent trials. Actual concurrency depends on resources. |
| `trialGpuNumber` | `trial_gpu_number` | Number of GPUs requested per trial; `0` hides GPU in local mode. |
| `maxExperimentDuration` | `max_experiment_duration` | Total experiment budget such as `10m`, `0.5h`, or `1d`. |
| `maxTrialNumber` | `max_trial_number` | Maximum number of trials to create. |
| `maxTrialDuration` | `max_trial_duration` | Per-trial time budget. |
| `nniManagerIp` | `nni_manager_ip` | Manager IP used by non-local training machines. |
| `debug` | `debug` | Verbose logging and looser internal validation. |
| `logLevel` | `log_level` | `trace`, `debug`, `info`, `warning`, `error`, or `fatal`. |
| `experimentWorkingDirectory` | `experiment_working_directory` | Directory for logs, checkpoints, and metadata. |
| `tuner` | `tuner` | Built-in, registered, or custom tuner config. |
| `assessor` | `assessor` | Optional early-stopping assessor config. |
| `trainingService` | `training_service` | Local, remote, or cloud training-service config. |
| `sharedStorage` | `shared_storage` | Shared storage config for remote/cloud workflows. |

Path rules:

- In YAML files, relative paths are relative to the directory containing the YAML file.
- In Python assignment, relative paths are relative to the current working directory.
- NNI expands `~` and normalizes relative paths when loading/saving configs.

## Search-Space Types

Common built-in HPO search spaces are JSON objects whose values are parameter specs with `_type` and `_value`.

| Type | `_value` shape | Meaning |
| --- | --- | --- |
| `choice` | non-empty list | Select one option. Options may be numbers, strings, or nested branch dicts. |
| `randint` | `[lower, upper]` | Integer in `[lower, upper)`. Use `quniform` with `q=1` when ordering matters across tuners. |
| `uniform` | `[low, high]` | Float uniformly sampled between `low` and `high`. |
| `quniform` | `[low, high, q]` | Quantized uniform, clipped to bounds. |
| `loguniform` | `[low, high]` | `exp(uniform(log(low), log(high)))`; bounds must be positive. |
| `qloguniform` | `[low, high, q]` | Quantized loguniform; bounds and `q` must be positive. |
| `normal` | `[mu, sigma]` | Normally distributed float; `sigma` should be positive. |
| `qnormal` | `[mu, sigma, q]` | Quantized normal; `sigma` and `q` should be positive. |
| `lognormal` | `[mu, sigma]` | `exp(normal(mu, sigma))`; `sigma` should be positive. |
| `qlognormal` | `[mu, sigma, q]` | Quantized lognormal; `sigma` and `q` should be positive. |

Nested search spaces:

```json
{
  "layer": {
    "_type": "choice",
    "_value": [
      {"_name": "linear", "width": {"_type": "choice", "_value": [64, 128]}},
      {"_name": "dropout", "rate": {"_type": "uniform", "_value": [0.1, 0.5]}}
    ]
  }
}
```

For built-in tuners, branch dicts inside `choice` should include `_name`. TPE, Random, Grid Search, Anneal, and Evolution support nested choices; other tuners may reject them or treat them poorly.

## Built-in Tuners

Common names used in config are case-insensitive in practice, but examples usually use names like `TPE`, `Random`, `GridSearch`, `Evolution`, `Hyperband`, `BOHB`, `GP`, `PBT`, `DNGO`, `SMAC`, `Anneal`, and `Batch`.

Optional dependency reminders from NNI packaging:

| Tuner | Extra dependency route |
| --- | --- |
| `Anneal` | install NNI with the `Anneal` extra for `hyperopt`. |
| `SMAC` | install the `SMAC` extra for `ConfigSpaceNNI` and `smac4nni`. |
| `BOHB` | install the `BOHB` extra for `ConfigSpace` and `statsmodels`. |
| `PPOTuner` | install the `PPOTuner` extra for `gym`. |
| `DNGO` | install the `DNGO` extra for `pybnn`. |

Use `Random` or `TPE` to smoke-test plumbing before diagnosing optional tuner dependency stacks.

## Custom Tuner Base API

Subclass `nni.tuner.Tuner`.

Required methods for most custom tuners:

```python
from nni.tuner import Tuner

class MyTuner(Tuner):
    def update_search_space(self, search_space):
        self.space = search_space

    def generate_parameters(self, parameter_id, **kwargs):
        return {'x': 0.5}

    def receive_trial_result(self, parameter_id, parameters, value, **kwargs):
        pass
```

Advanced hooks:

- `generate_multiple_parameters(self, parameter_id_list, **kwargs)` can produce multiple parameter sets at once.
- `trial_end(self, parameter_id, success, **kwargs)` can track completion/failure.
- Raise `nni.NoMoreTrialError` when the search space is fully explored.
- `import_data(self, data)` can consume `nnictl experiment import` records for supporting tuners.

## Custom Assessor Base API

Subclass `nni.assessor.Assessor`.

```python
from nni.assessor import Assessor, AssessResult

class MyAssessor(Assessor):
    def assess_trial(self, trial_job_id, trial_history):
        if len(trial_history) >= 3 and trial_history[-1] < 0.1:
            return AssessResult.Bad
        return AssessResult.Good
```

Assessor caveats:

- `trial_history` contains the intermediate metrics that trial code reported.
- The history is guaranteed to grow, but NNI does not guarantee every update triggers assessment.
- A trial can continue reporting after a bad result, and retried trials can have inconsistent histories.
- If the user reports dict metrics, make sure the assessor expects that shape or report simpler numeric intermediate values.

## Utility APIs

- `nni.utils.extract_scalar_reward(value, scalar_key='default')` extracts a numeric reward from a number or metric dict and raises when the required scalar is absent.
- `nni.utils.merge_parameter(base_params, override_params)` updates a dict or namespace in place with sampled values and returns it.
- `nni.utils.ClassArgsValidator` can validate custom algorithm `classArgs` during algorithm registration.
