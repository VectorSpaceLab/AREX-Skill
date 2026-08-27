# OPF Troubleshooting

Use this reference after package/runtime installation has been checked. For Python 2.7, `nupic.bindings`, `numpy`, `pycapnp`, or capnproto setup failures, start with root [`../../../references/troubleshooting.md`](../../../references/troubleshooting.md). For CSV/model-param validation, use [`../../data-and-configuration/`](../../data-and-configuration/). For SP/TM/classifier internals, use [`../../htm-algorithms/`](../../htm-algorithms/).

## Symptom-to-recovery table

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `No predicted field was enabled! Did you call enableInference()?` | `model.enableInference({'predictedField': ...})` was not called, or inference args omitted the key | Call `model.enableInference({'predictedField': '<exact field name>'})` immediately after model creation or checkpoint load when needed. |
| `ModelFactory` creates a model but `result.inferences` lacks multi-step keys | Inference type or classifier steps do not request multi-step predictions; inference disabled; model still warming up | Check `modelParams.inferenceType` (`TemporalMultiStep`/`NontemporalMultiStep` for multi-step), `modelParams.clParams.steps`, and `model.isInferenceEnabled()`. Run more typed records before deciding predictions are absent. |
| `KeyError` for predicted field inside `model.run` | Input record lacks the field named in `enableInference`, or a CSV/model-param field-name mismatch exists | Compare CSV name row, encoder `fieldname`, optional `modelParams.predictedField`, and `enableInference` value. Fix the names in one place, then validate through [`../../data-and-configuration/`](../../data-and-configuration/). |
| Multi-step confidence lookup raises `KeyError` | Best prediction is `None`, step key is absent, step was treated as string, or confidence dict does not contain that value | Use integer step keys and guard warm-up: `value = best.get(1); conf = allPred.get(1, {}).get(value) if value is not None else None`. |
| `TypeError`, encoder errors, timestamp parser errors, or nonsensical predictions after reading CSV | Raw CSV strings were passed to `model.run` | Convert by the CSV type row before `model.run`: `float`, `int`, `datetime.datetime.strptime`, `bool`, or `str`. Use `scripts/opf_prediction_smoke.py` as a bounded typed-read example. |
| `KeyError: 'model'`, `KeyError: 'modelParams'`, `KeyError: 'sensorParams'`, or unsupported model type from `ModelFactory` | Model params are nested incorrectly or a generated file wrapper was passed instead of the model-config dict | Pass the dict whose top level includes `model: HTMPrediction` and `modelParams: {...}`. If a swarm produced `MODEL_PARAMS` or `modelConfig`, load that exact dict rather than the whole module namespace. |
| `KeyError`/`AssertionError` involving task labels in experiment runner | `--tasks` consumed the experiment directory as another task label, or label is misspelled | First run `--listTasks`. Then run selected tasks as `--tasks LabelA LabelB . EXPERIMENT_DIR` with a standalone dot before the directory. |
| Runner reports “Exactly ONE experiment must be specified” | Missing experiment directory or extra positional arguments | Use `python -m nupic.frameworks.opf.experiment_runner [options] EXPERIMENT_DIR`. Quote paths with spaces. |
| Runner reports mutually exclusive options | Combined `-c`, `--listCheckpoints`, `--listTasks`, `--load`, or combined `-c` with `--noCheckpoint` | Choose exactly one action. Use a separate command for list/create/load/run. |
| `--load` cannot find a checkpoint | Passed a filesystem path or `<label>.nta` instead of the label, or checkpoint is not under `EXPERIMENT_DIR/savedmodels` | Run `--listCheckpoints EXPERIMENT_DIR`; pass the displayed label only: `--load MyCheckpoint EXPERIMENT_DIR`. |
| `ModelFactory.loadFromCheckpoint` fails to open `model.pkl` or `model.data` | Passed the checkpoint parent directory instead of the checkpoint directory, or `newSerialization` flag does not match saved format | For direct API pass the directory containing `model.pkl` or `model.data`. Use `newSerialization=True` for `model.data`. For experiment checkpoints, the actual directory is `EXPERIMENT_DIR/savedmodels/<label>.nta/`. |
| Save refuses to delete an existing path | Target exists but is not a recognized model checkpoint directory | Choose a new empty directory or delete/rename the old non-model path yourself after confirming it is safe. The legacy API intentionally refuses to overwrite arbitrary directories. |
| `ImportError: No module named nupic`, `nupic.bindings`, `capnp`, or compiled-region errors | Runtime is not a NuPIC legacy environment or compiled dependencies are missing | Use root [`../../../references/troubleshooting.md`](../../../references/troubleshooting.md). Expect Python 2.7-era NuPIC, compiled `nupic.bindings`, `numpy` 1.12.x compatibility, and `pycapnp`/capnproto for serialization. |
| `SyntaxError: Missing parentheses in call to 'print'` while trying old examples | Legacy NuPIC examples and scripts use Python 2 print statements | Run legacy examples under Python 2.7, or adapt print statements with `from __future__ import print_function` and `print(...)`. The bundled scripts in this sub-skill avoid Python 2 print syntax. |

## Predicted-field checklist

When predictions are empty or the wrong field is predicted, verify these in order:

1. CSV name row contains the field, e.g. `consumption`.
2. CSV type row declares the expected type, e.g. `float`.
3. Model params encoder for that field has matching `fieldname: consumption`.
4. Classifier-related params request the desired steps, e.g. `clParams.steps: '1,5'`.
5. Direct code calls `model.enableInference({'predictedField': 'consumption'})`.
6. Every record passed to `model.run` contains `record['consumption']` as a typed numeric value.
7. Result extraction uses integer steps: `best[1]`, not `best['1']`.

If any item fails, fix data/config first; OPF debugging is usually misleading until the data path is consistent.

## Model params nesting checks

Use this minimal shape when localizing nesting errors:

```python
assert modelConfig['model'] == 'HTMPrediction'
params = modelConfig['modelParams']
assert params['sensorParams']['encoders']
assert 'spEnable' in params
assert 'tmEnable' in params
assert 'clParams' in params
```

Common wrong shapes:

- Passing `{'MODEL_PARAMS': {...}}` to `ModelFactory.create` instead of the inner dict.
- Moving `model: HTMPrediction` under `modelParams`.
- Moving `sensorParams.encoders` to top level.
- Changing encoder keys but leaving each encoder's `fieldname` unchanged.
- Treating `clParams.steps` as an output-only setting and forgetting result extraction must use those step keys.

## Result inference lookup patterns

Robust code should not assume every key appears immediately:

```python
inferences = result.inferences or {}
best = inferences.get('multiStepBestPredictions', {})
all_predictions = inferences.get('multiStepPredictions', {})

for step in (1, 5):
    value = best.get(step)
    if value is None:
        print('step %s has no prediction yet' % step)
        continue
    confidence = all_predictions.get(step, {}).get(value)
    print(step, value, confidence)
```

If the output is keyed by enum constants in a custom wrapper, try importing `InferenceElement` from `nupic.frameworks.opf.opf_utils` and use `InferenceElement.multiStepBestPredictions` / `InferenceElement.multiStepPredictions` as keys. The legacy public OPF examples use string keys.

## Experiment runner recovery sequence

1. Confirm the directory contains `description.py`.
2. Print help without running: `python scripts/opf_experiment_help.py --summary`.
3. In the NuPIC environment, check import: `python scripts/opf_experiment_help.py --check-import`.
4. List task labels: `python -m nupic.frameworks.opf.experiment_runner --listTasks EXPERIMENT_DIR`.
5. Use `--testMode` or a selected small task before a long run.
6. List checkpoints before loading: `python -m nupic.frameworks.opf.experiment_runner --listCheckpoints EXPERIMENT_DIR`.
7. Load by label only: `python -m nupic.frameworks.opf.experiment_runner --load LABEL EXPERIMENT_DIR`.

## Checkpoint shape validator

Direct load path must point at one of these directories:

```text
legacy_pickle_checkpoint/
  model.pkl
  modelextradata/       # optional

capnp_checkpoint/
  model.data
```

Experiment load path is resolved by label:

```text
EXPERIMENT_DIR/
  savedmodels/
    LABEL.nta/
      model.pkl or model.data
```

If a user supplies `EXPERIMENT_DIR/savedmodels`, ask for the exact label or list checkpoints. If a user supplies `LABEL.nta` to `--load`, strip the `.nta` suffix.
