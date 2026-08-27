# OPF API Reference

Use this reference for concrete NuPIC legacy Online Prediction Framework (OPF) API names, input/output shapes, inference keys, and checkpoint methods. For CSV headers and model-param schema details, route to [`../../data-and-configuration/`](../../data-and-configuration/). For algorithm internals behind OPF, route to [`../../htm-algorithms/`](../../htm-algorithms/). For package installation failures, route to root [`../../../references/troubleshooting.md`](../../../references/troubleshooting.md).

## Core entry points

| Task | API | Input shape | Output/side effect |
| --- | --- | --- | --- |
| Create an OPF model | `nupic.frameworks.opf.model_factory.ModelFactory.create(modelConfig, logLevel=40)` | `modelConfig` dict with top-level `model` and nested `modelParams` | OPF `Model`, usually `HTMPredictionModel` for `model: HTMPrediction` |
| Load a saved model | `ModelFactory.loadFromCheckpoint(savedModelDir, newSerialization=False)` | Directory containing `model.pkl` for legacy pickle, or `model.data` when `newSerialization=True` | Loaded OPF `Model` |
| Enable prediction output | `model.enableInference(inferenceArgs=None)` | Usually `{'predictedField': '<fieldName>'}` | Sets inference state and predicted field |
| Disable prediction output | `model.disableInference()` | none | Stops inference output |
| Run one record | `model.run(inputRecord)` | Dict-like typed input record keyed by field names | `ModelResult` |
| Save direct model checkpoint | `model.save(saveModelDir)` | Empty/nonexistent dir or existing model checkpoint dir | Writes `model.pkl` and optional `modelextradata/` |
| Save capnp checkpoint | `model.writeToCheckpoint(checkpointDir)` | Empty/nonexistent dir or existing capnp checkpoint dir | Writes `model.data` |
| Finish learning | `model.finishLearning()` | none | Permanently enters finished-learning mode; do not expect to resume learning |
| Reset temporal state | `model.resetSequenceStates()` | none | Marks a sequence boundary |
| Inspect field metadata | `model.getFieldInfo(includeClassifierOnlyField=False)` | bool | Field metadata list |
| Runtime stats | `model.getRuntimeStats()` | none | Dict of model-specific statistics |

Installed API signatures observed for this legacy repo include:

```text
ModelFactory.create(modelConfig, logLevel=40)
ModelFactory.loadFromCheckpoint(savedModelDir, newSerialization=False)
FileRecordStream.__init__(streamID, write=False, fields=None, missingValues=None, bookmark=None, includeMS=True, firstRecord=None)
```

## Model config shape for `ModelFactory.create`

A direct OPF model config is a Python dict, often loaded from YAML:

```yaml
model: HTMPrediction
version: 1
aggregationInfo:
  fields:
  - [consumption, mean]
  hours: 1
  minutes: 0
predictAheadTime: null
modelParams:
  inferenceType: TemporalMultiStep
  sensorParams:
    verbosity: 0
    encoders:
      consumption:
        fieldname: consumption
        name: consumption
        type: RandomDistributedScalarEncoder
        resolution: 0.88
        seed: 1
      timestamp_timeOfDay:
        fieldname: timestamp
        name: timestamp_timeOfDay
        type: DateEncoder
        timeOfDay: [21, 1]
  spEnable: true
  spParams: {columnCount: 2048, inputWidth: 946, globalInhibition: 1}
  tmEnable: true
  tmParams: {columnCount: 2048, cellsPerColumn: 32, inputWidth: 2048}
  clParams:
    regionName: SDRClassifierRegion
    steps: '1,5'
    alpha: 0.1
```

Important nesting rules:

- `model` is top-level, not inside `modelParams`.
- `modelParams.sensorParams.encoders` holds OPF encoders keyed by encoder name.
- `modelParams.spParams`, `modelParams.tmParams`, and `modelParams.clParams` configure SP, TM, and classifier regions used by `HTMPredictionModel`.
- `clParams.steps` may be a comma-separated string such as `'1,5'`; result step keys are integers.
- Some generated configs also include `modelParams.predictedField`. Direct scripts should still call `model.enableInference({'predictedField': field})` explicitly so the runtime state is obvious.

Supported inference type names in this code family include:

```text
TemporalNextStep
TemporalClassification
NontemporalClassification
TemporalAnomaly
NontemporalAnomaly
TemporalMultiStep
NontemporalMultiStep
```

## Input record shape for `model.run`

`model.run(inputRecord)` expects one typed record at a time:

```python
{
    'timestamp': datetime.datetime(2010, 7, 2, 0, 0),
    'consumption': 21.2,
}
```

Do not pass raw CSV strings for numeric or datetime columns. Translate from the NuPIC CSV type row before calling OPF:

| CSV field type | Python value to pass |
| --- | --- |
| `float` | `float(value)` |
| `int` | `int(value)` |
| `datetime` | `datetime.datetime.strptime(value, format)` |
| `string` | `str(value)` |
| `bool` | boolean value, not arbitrary text |

The input dict must include the predicted field under the exact name used by `enableInference`.

## `ModelResult` shape

`model.run` returns a `ModelResult` object with these public attributes:

| Attribute | Meaning |
| --- | --- |
| `predictionNumber` | 0-based record index for the model result |
| `rawInput` | Original typed input record |
| `sensorInput` | Translated/encoded sensor payload when populated |
| `inferences` | Dict of inference outputs |
| `metrics` | Metric outputs when an OPF task/metric manager computed them |
| `predictedFieldIdx` | Numeric index of predicted field when resolved |
| `predictedFieldName` | Predicted field name |
| `classifierInput` | Classifier input payload when populated |

Inference keys are string-compatible legacy `InferenceElement` names. Common keys:

| Key | Typical value shape | Notes |
| --- | --- | --- |
| `prediction` | tuple/list | Next-step prediction-like output for some inference types |
| `encodings` | tuple/list | Encoded values used by metrics/output |
| `classification` | label/class value | Classification workflows |
| `classConfidences` | dict | Class confidence outputs |
| `anomalyScore` | float | Anomaly workflows |
| `anomalyLabel` | string/list-like label | Anomaly label workflows |
| `multiStepPredictions` | `{step: {predictedValue: confidence}}` | All candidate values and probabilities/confidences by integer step |
| `multiStepBestPredictions` | `{step: predictedValue}` | Best predicted value by integer step |
| `multiStepBucketLikelihoods` | `{step: bucketLikelihood}` | Classifier bucket likelihood diagnostics |
| `multiStepBucketValues` | bucket/value diagnostics | Present in some classifier paths |

Robust extraction helper:

```python
def get_multistep(result, step):
    inferences = result.inferences or {}
    best_by_step = inferences.get('multiStepBestPredictions', {})
    all_by_step = inferences.get('multiStepPredictions', {})
    value = best_by_step.get(step)
    if value is None:
        return None, None
    confidence = all_by_step.get(step, {}).get(value)
    return value, confidence
```

If `result.inferences` is keyed by enum values in a custom context, import `InferenceElement` and try `InferenceElement.multiStepBestPredictions` / `InferenceElement.multiStepPredictions`; the legacy public examples index by the string names shown above.

## Experiment runner API and CLI surface

Python API:

```python
from nupic.frameworks.opf.experiment_runner import runExperiment
model = runExperiment(['--testMode', 'EXPERIMENT_DIR'])
```

Installed module command:

```bash
python -m nupic.frameworks.opf.experiment_runner [options] EXPERIMENT_DIR
```

Options exposed by the runner:

| Option | Meaning |
| --- | --- |
| `-c <CHECKPOINT>` | Create a model and save checkpoint `<CHECKPOINT>` without running tasks |
| `--listCheckpoints` | List checkpoint labels under `EXPERIMENT_DIR/savedmodels/` |
| `--listTasks` | List task labels in `description.py` |
| `--load <CHECKPOINT>` | Load checkpoint label and run tasks |
| `--newSerialization` | Use capnproto serialization (`model.data`) instead of legacy pickle (`model.pkl`) |
| `--tasks LABEL ... .` | Run selected task labels; use standalone `.` before `EXPERIMENT_DIR` |
| `--testMode` | Reduce iteration counts for testing where supported |
| `--noCheckpoint` | Do not checkpoint after each task |

Mutual exclusions:

- Select only one of `-c`, `--listCheckpoints`, `--listTasks`, and `--load`.
- Do not combine `-c` and `--noCheckpoint`.

## Checkpoint directory shapes

Legacy direct `model.save` or experiment default:

```text
checkpoint_dir/
  model.pkl
  modelextradata/   # optional
```

Capnproto/new serialization:

```text
checkpoint_dir/
  model.data
```

Experiment runner parent layout:

```text
EXPERIMENT_DIR/
  savedmodels/
    TaskLabel.nta/
      model.pkl or model.data
```

Pass the directory containing `model.pkl` or `model.data` to `ModelFactory.loadFromCheckpoint`. For experiment runner `--load`, pass only the checkpoint label (`TaskLabel`), not `TaskLabel.nta`.
