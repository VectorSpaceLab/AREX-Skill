# Cross-Cutting Troubleshooting

## Purpose

Use this reference when a DeepCTR task fails before it reaches a specific sub-skill, or when the failure spans installation, TensorFlow compatibility, GPU visibility, or model serialization.

## Fast first check

Run the bundled environment probe:

```bash
python scripts/check_deepctr_env.py --json
```

If that fails, fix installation or backend selection before debugging feature columns or model code.

## Common failure surfaces

| Symptom | Likely cause | Next step | Owning sub-skill |
|---|---|---|---|
| `ModuleNotFoundError: tensorflow` or a NumPy/h5py import error | TensorFlow was not installed first, or the selected TensorFlow build conflicts with Python/NumPy/h5py | Install a compatible TensorFlow build, then reinstall DeepCTR and rerun the probe | `keras-model-workflows` / `estimator-workflows` |
| `AttributeError: module 'tensorflow' has no attribute 'estimator'` | The selected TensorFlow runtime does not expose the legacy Estimator API | Use Keras-style DeepCTR workflows or install a TensorFlow release that still exposes `tf.estimator` | `estimator-workflows` |
| `SparseFeat(name='...', dtype='string') requires use_hash=True` | A string sparse feature was passed directly to the embedding path | Set `use_hash=True` or pre-encode to integers | `data-and-feature-columns` |
| `Unknown layer: DNN` or `Hash` during `load_model` | Whole-model loading needs DeepCTR custom objects | Import `deepctr.layers.custom_objects` and pass it to `load_model` | `keras-model-workflows` |
| History or session fields seem ignored | The input names do not follow the required `hist_` or `sess_` conventions | Rename the fields and include `seq_length` or `sess_length` as needed | `sequence-models` |
| Multi-output losses or predictions are attached to the wrong head | The target list/dict order does not match `model.output_names` | Inspect `model.output_names` and switch to dict-based target packing when in doubt | `multitask-models` |
| TensorFlow prints a version warning or network noise from `deepctr` import | `deepctr.utils.check_version` performs a background PyPI query | Treat the warning as informational; offline or firewalled environments may print a manual-check message | root `deepctr` |
| CUDA warnings appear but CPU training still works | TensorFlow can see the installed build but not a usable GPU runtime | Keep using the CPU workflow or install a TensorFlow build that matches the CUDA/cuDNN stack | `keras-model-workflows` |

## When to stop and reroute

- If the runtime probe reports that `tf.estimator` is unavailable, stop debugging Estimator data issues and switch to Keras-style DeepCTR workflows.
- If the failure is specific to `hist_` / `sess_` naming, jump directly to the sequence sub-skill instead of guessing at the model builder.
- If the failure is only about input schema or padding, jump to the feature-column sub-skill first.

## Public API hygiene

Use public `tensorflow.keras` APIs in user-facing code and keep private `tensorflow.python.*` imports out of generated examples and instructions.
