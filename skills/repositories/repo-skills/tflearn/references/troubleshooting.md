# TFLearn Troubleshooting

Use this cross-cutting reference for failures that occur before a task belongs clearly to one sub-skill. For workflow-specific problems, follow the nearest sub-skill troubleshooting file.

## Import Fails on Modern TensorFlow

Symptoms:

```text
ImportError: cannot import name 'is_sequence' from 'tensorflow.python.util.nest'
ModuleNotFoundError: No module named 'tensorflow.contrib'
```

Likely cause: the current TFLearn source is TensorFlow-v1-style and imports private/contrib TensorFlow symbols removed from modern TensorFlow 2.x.

Fix:

1. Use an isolated legacy runtime with TensorFlow 1.15.x when the goal is to run existing TFLearn code.
2. If the task is migration, do not keep debugging environment variables; plan a port to TensorFlow 2/Keras or patch TFLearn imports intentionally.
3. Run `python scripts/check_tflearn_env.py` to confirm versions and importability.

## protobuf 4.x Descriptor Error

Symptom:

```text
TypeError: Descriptors cannot not be created directly.
```

Fix inside the TFLearn environment:

```bash
python -m pip install "protobuf==3.20.3"
```

Then rerun the environment check. Avoid downgrading protobuf in a shared modern environment unless explicitly approved.

## Empty or Polluted TensorFlow Collections

Symptoms:

```text
tf collection "TRAIN_OPS" is empty
No input data! Please add an 'input_data' layer
Feed dict asks for variable named '...' but no such variable is known to exist
```

Likely causes:

- Missing `tflearn.input_data` or custom placeholders not added to `tf.GraphKeys.INPUTS`.
- Missing `tflearn.regression`, so no `TrainOp` was created.
- Reusing a notebook default graph after building another model.
- Feed dictionaries keyed by the wrong layer/placeholder names.

Fix:

1. Build each independent model in `with tf.Graph().as_default():`.
2. Ensure the graph has at least one input collection entry and one train op before `DNN.fit`.
3. Prefer named feeds for non-trivial models: `model.fit({'input': X}, {'target': Y}, ...)`.
4. Use [layers-and-ops troubleshooting](../sub-skills/layers-and-ops/references/troubleshooting.md) for collection and shape issues, then [training-and-persistence troubleshooting](../sub-skills/training-and-persistence/references/troubleshooting.md) for feed/save/load failures.

## Dataset Download or Optional Dependency Failure

Symptoms:

```text
HTTPError / URLError while loading mnist, cifar10, imdb, oxflower17, svhn, titanic
ImportError: No module named h5py / dask / pandas / gym / scipy
```

Fix:

- Do not treat download failure as proof that TFLearn itself is broken.
- For smoke tests, replace loaders with tiny in-memory arrays or CSV fixtures.
- Install only the optional dependency needed for the selected workflow.
- Use [data-input-pipelines](../sub-skills/data-input-pipelines/SKILL.md) for data preparation and [advanced-model-recipes](../sub-skills/advanced-model-recipes/SKILL.md) for long example adaptation.

## GPU Questions

CPU validates TFLearn's selected API behavior. GPU only changes acceleration/device placement for most workflows in this skill.

When a user specifically asks for GPU:

1. Verify the TensorFlow runtime sees the device (`tf.test.is_gpu_available()` in TF1-era code).
2. Confirm the TensorFlow/CUDA/cuDNN versions are a compatible historical stack.
3. Run a minimal TensorFlow device allocation before running any TFLearn training.
4. Do not present CPU smoke results as GPU proof.

## Original Example Is Too Slow or Unsafe

Many TFLearn example patterns train for many epochs, download datasets, use notebooks/plots, or require optional services. Default to the bundled scripts:

```bash
python scripts/check_tflearn_env.py
python sub-skills/layers-and-ops/scripts/layer_graph_smoke.py
python sub-skills/training-and-persistence/scripts/tiny_dnn_regression_smoke.py --epochs 2
python sub-skills/advanced-model-recipes/scripts/custom_trainer_smoke.py --epochs 1
```

Only scale up epochs, data, plotting, downloads, or GPU after the user approves the required runtime and cost.
