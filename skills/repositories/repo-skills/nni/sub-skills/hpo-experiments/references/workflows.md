# HPO Experiment Workflows

This reference is self-contained guidance for building and debugging NNI HPO experiments. It uses current experiment config names: YAML uses camelCase fields, while Python `ExperimentConfig` uses snake_case properties.

## Minimal Local CLI Experiment

Use this shape when the user wants a reproducible project directory and `nnictl` launch.

```yaml
experimentName: local-hpo-demo
searchSpaceFile: search_space.json
trialCommand: python3 train.py
trialCodeDirectory: .
trialConcurrency: 1
maxTrialNumber: 20
maxExperimentDuration: 1h
tuner:
  name: TPE
  classArgs:
    optimize_mode: maximize
trainingService:
  platform: local
  useActiveGpu: false
```

Companion `search_space.json`:

```json
{
  "learning_rate": {"_type": "loguniform", "_value": [0.0001, 0.1]},
  "batch_size": {"_type": "choice", "_value": [16, 32, 64]},
  "dropout": {"_type": "uniform", "_value": [0.0, 0.5]}
}
```

Companion `train.py` pattern:

```python
import nni

params = nni.get_next_parameter()
learning_rate = params.get('learning_rate', 0.01)
# train/evaluate using the sampled values
for epoch in range(3):
    nni.report_intermediate_result({'default': 0.70 + 0.01 * epoch, 'epoch': epoch})
nni.report_final_result({'default': 0.75, 'learning_rate': learning_rate})
```

Launch and inspect:

```bash
python scripts/validate_search_space.py search_space.json
nnictl create --config config.yml --port 8080
nnictl trial ls
nnictl experiment status
nnictl log stdout --tail 50
nnictl stop
```

Use `python` instead of `python3` on Windows unless the user environment provides `python3`.

## Python Experiment API Route

Use the Python route when the user wants to construct configs in code, generate configs, or control the experiment lifecycle programmatically.

```python
from nni.experiment import Experiment
from nni.experiment.config import ExperimentConfig

config = ExperimentConfig('local')
config.experiment_name = 'python-api-hpo-demo'
config.search_space = {
    'learning_rate': {'_type': 'loguniform', '_value': [1e-4, 1e-1]},
    'batch_size': {'_type': 'choice', '_value': [16, 32, 64]},
}
config.trial_command = 'python3 train.py'
config.trial_code_directory = '.'
config.trial_concurrency = 1
config.max_trial_number = 20
config.tuner.name = 'TPE'
config.tuner.class_args = {'optimize_mode': 'maximize'}
config.training_service.use_active_gpu = False

experiment = Experiment(config)
experiment.run(8080)
```

Important differences from YAML:

- YAML config fields are camelCase, for example `searchSpaceFile`, `trialCommand`, and `trainingService`.
- Python properties are snake_case, for example `search_space_file`, `trial_command`, and `training_service`.
- Relative paths in YAML are resolved from the YAML file directory; relative paths assigned in Python are resolved from the current working directory.
- NNI converts relative config paths to absolute paths when loading/saving an `ExperimentConfig`.

## Trial Code Checklist

- Call `nni.get_next_parameter()` or `nni.get_next_parameters()` once near startup; repeated calls in a trial are undefined.
- Merge sampled parameters into parser defaults or config defaults; `nni.utils.merge_parameter(base_params, override_params)` mutates and returns `base_params`.
- Report intermediate metrics only after the trial has received parameters when running inside NNI.
- Report final metrics as a number or a dict whose `default` key is numeric; extra keys can be displayed in the web portal.
- Use `nni.get_experiment_id()`, `nni.get_trial_id()`, and `nni.get_sequence_id()` for run-aware logging, not as routing inputs.
- Treat standalone runs as a smoke path: trial APIs return standalone IDs outside NNI, but launcher behavior, metric transport, and scheduling are only exercised under an experiment.

## Search-Space Repair Workflow

1. Parse strictly as JSON first when the file is named `.json`; remove comments and trailing commas.
2. Check each parameter object has both `_type` and `_value`.
3. Verify `_type` spelling and arity:
   - two values: `randint`, `uniform`, `loguniform`, `normal`, `lognormal`.
   - three values: `quniform`, `qloguniform`, `qnormal`, `qlognormal`.
   - non-empty list: `choice`.
4. For log distributions, require positive bounds or parameters where the eventual sampled value is positive.
5. For nested `choice`, require dict options to include `_name` so built-in tuners can identify which branch was chosen.
6. Match the space to the tuner: TPE, Random, Grid Search, Anneal, and Evolution support nested choices; SMAC, Metis, GP, BOHB, PBT, Hyperband, DNGO have narrower documented support.

## Built-in Tuner Selection

- `TPE`: good default, lightweight, supports all common search-space types and nested spaces.
- `Random`: baseline and smoke-test tuner; use to separate experiment plumbing from algorithm behavior.
- `GridSearch`: exhaustive for small spaces; avoid for large continuous spaces.
- `Evolution`: simple population heuristic; can need many trials.
- `Hyperband` / `BOHB`: budget-aware algorithms; trial code often needs budget handling for meaningful results.
- `Batch`: use when the user provides a fixed list of configurations; search space is mainly `choice`-based.
- `SMAC`, `Anneal`, `BOHB`, `PPO`, `DNGO`: may need optional extras; verify dependencies before launch.
- `GP`, `Metis`, `DNGO`: best with numerical values; non-numeric `choice` values can be problematic.

## Assessor Workflow

Assessors use intermediate results to stop poor trials early.

```yaml
assessor:
  name: Medianstop
  classArgs:
    optimize_mode: maximize
```

Use an assessor when compute is scarce and the trial reports useful intermediate metrics. If all intermediate metrics are noisy, missing, or use the wrong optimization direction, remove the assessor until metric reporting is stable.

## Custom Tuner Or Assessor

A custom tuner should inherit `nni.tuner.Tuner` and implement:

- `update_search_space(self, search_space)`.
- `generate_parameters(self, parameter_id, **kwargs)` or `generate_multiple_parameters(self, parameter_id_list, **kwargs)`.
- `receive_trial_result(self, parameter_id, parameters, value, **kwargs)`.

A custom assessor should inherit `nni.assessor.Assessor` and implement:

- `assess_trial(self, trial_job_id, trial_history)` returning `AssessResult.Good` or `AssessResult.Bad`.
- optional `trial_end(self, trial_job_id, success)`.

Direct config for an unregistered custom tuner:

```yaml
tuner:
  codeDirectory: ./my_tuner
  className: my_tuner.MyTuner
  classArgs:
    optimize_mode: maximize
```

Registered algorithm flow:

```bash
nnictl algo register --meta_path meta_file.yml
nnictl algo list
```

Meta file shape:

```yaml
algoType: tuner
builtinName: mytuner
className: my_tuner.MyTuner
classArgsValidator: my_tuner.MyClassArgsValidator
```

Custom algorithm caveats:

- `codeDirectory` must contain the Python module named in `className`.
- Constructor args must be literal YAML values under `classArgs`.
- Do not rely on the process current working directory inside a tuner or assessor; resolve bundled data relative to `__file__`.
- Validate class args with a `ClassArgsValidator` when registering a reusable algorithm.

## Remote And Cloud Triage

Use local mode first when the problem may be search space, trial code, tuner import, or metric reporting. Escalate to remote/cloud after the local experiment reaches trial execution.

Remote mode checklist:

- `trainingService.platform: remote` and a non-empty `machineList`.
- SSH host, port, user, and exactly one credential route: key file or password.
- Matching NNI versions and compatible Python commands on the manager and training machines.
- `trialCommand` works on the target OS; Linux commonly uses `python3`, Windows commonly uses `python`.
- Use `.nniignore` when `trialCodeDirectory` has many files; remote/cloud services limit file count and total payload size.
- Put secrets in the user's environment or secure config management; do not paste real passwords, tokens, or cloud keys into generated examples.

Cloud service checklist:

- `openpai`, `aml`, `dlc`, `kubeflow`, `frameworkcontroller`, and hybrid services require platform-specific credentials, storage, images, or cluster resources.
- Confirm the user's cloud account, storage mount, Docker image, and compute names before launch.
- Prefer config review and `nnictl ... --help` commands over running cloud launches during troubleshooting unless the user explicitly authorizes cost-incurring work.
