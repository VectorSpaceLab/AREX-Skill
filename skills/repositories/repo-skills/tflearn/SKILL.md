---
name: tflearn
description: "Use and troubleshoot TFLearn, a TensorFlow-v1-style high-level
  deep learning API for layers, data feeds, DNN training, checkpoints, and model
  recipes."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# TFLearn Repo Skill

Use this repo skill when a task names **TFLearn**, imports `tflearn`, builds TensorFlow-v1-style graphs with TFLearn layers, prepares TFLearn data feeds, trains with `tflearn.DNN`/`tflearn.Trainer`, saves/restores TFLearn checkpoints, or adapts TFLearn example families for small safe experiments.

TFLearn is a legacy high-level API over TensorFlow graph mode. Prefer this skill for package usage, migration triage, compatibility diagnosis, and safe recipe adaptation. Do not use it as a general TensorFlow 2/Keras guide unless the task is specifically about porting or replacing TFLearn code.

## Installation Baseline

Use an isolated legacy environment for runnable TFLearn workflows. A public baseline that matches this skill is **Python 3.7.x** with TensorFlow 1.15-compatible pins:

```bash
python -m pip install "tensorflow==1.15.5" "protobuf==3.20.3" "numpy<1.19" six Pillow
python -m pip install tflearn
```

TensorFlow 1.15 wheels are not available for many modern Python versions, so create a dedicated Python 3.7 environment rather than trying to retrofit a current Python 3.11+ or 3.13 environment. Install optional packages such as `h5py`, `scipy`, `dask`, `pandas`, `gym`, or GPU TensorFlow only when the selected workflow needs them. Read [Compatibility](references/compatibility.md) before mutating an existing environment.

## First Checks

1. Read [Repository Provenance](references/repo-provenance.md) when checking whether this skill matches a checkout or package version.
2. Read [Compatibility](references/compatibility.md) before installing or debugging imports. The verified runtime for this skill is TFLearn `0.5.0` with TensorFlow `1.15.5`, NumPy `1.18.x`, and protobuf `3.20.x` on CPU.
3. Run the root environment check when a user reports import/runtime trouble:

   ```bash
   python scripts/check_tflearn_env.py --help
   python scripts/check_tflearn_env.py
   ```

4. Use [Troubleshooting](references/troubleshooting.md) for cross-cutting import, graph/session, optional dependency, GPU, and example-safety failures.
5. For workflows that cross data validation, graph construction, training, and checkpointing, read [Integrated Recipes](references/integrated-recipes.md) before diving into sub-skills.

## Route by Task

| Task signal | Load |
| --- | --- |
| `input_data`, `fully_connected`, `conv_2d`, `lstm`, `merge`, `regression`, activations, losses, metrics, optimizers, variables, summaries, graph collections, shape errors | [layers-and-ops](sub-skills/layers-and-ops/SKILL.md) |
| CSV/tabular loading, target columns, one-hot labels, sequence padding/vectorization, dataset loaders, HDF5/Dask feeds, image preprocessing, data augmentation | [data-input-pipelines](sub-skills/data-input-pipelines/SKILL.md) |
| `DNN.fit`, prediction/evaluation, validation sets, callbacks, TensorBoard, checkpoints, `save`/`load`, `get_weights`, restore scopes, feed dictionaries | [training-and-persistence](sub-skills/training-and-persistence/SKILL.md) |
| Vision/NLP/generative/RL/recommender recipes, `SequenceGenerator`, estimators, custom TensorFlow graph with `TrainOp`/`Trainer`, shrinking examples to tiny fixtures | [advanced-model-recipes](sub-skills/advanced-model-recipes/SKILL.md) |

## Minimal Usage Pattern

```python
import tensorflow.compat.v1 as tf
import tflearn

tf.disable_v2_behavior()

with tf.Graph().as_default():
    net = tflearn.input_data(shape=[None, 4], name="input")
    net = tflearn.fully_connected(net, 8, activation="relu")
    net = tflearn.fully_connected(net, 2, activation="softmax")
    net = tflearn.regression(net, optimizer="adam", loss="categorical_crossentropy", name="target")
    model = tflearn.DNN(net, tensorboard_verbose=0)
```

For real training, pair the graph with numeric arrays or named feed dictionaries and then use the training sub-skill. Keep one fresh `tf.Graph()` per independent model rebuild to avoid stale collections.

## Safe Validation Helpers

- [`scripts/check_tflearn_env.py`](scripts/check_tflearn_env.py): shared import/version/signature/backend probe.
- [`sub-skills/layers-and-ops/scripts/layer_graph_smoke.py`](sub-skills/layers-and-ops/scripts/layer_graph_smoke.py): build a tiny graph and inspect collections.
- [`sub-skills/data-input-pipelines/scripts/validate_tflearn_tabular_data.py`](sub-skills/data-input-pipelines/scripts/validate_tflearn_tabular_data.py): validate CSV/target/ignore-column plans before `load_csv` or NumPy conversion.
- [`sub-skills/training-and-persistence/scripts/tiny_dnn_regression_smoke.py`](sub-skills/training-and-persistence/scripts/tiny_dnn_regression_smoke.py): train/predict/save/load a tiny DNN regression model without downloads.
- [`sub-skills/advanced-model-recipes/scripts/custom_trainer_smoke.py`](sub-skills/advanced-model-recipes/scripts/custom_trainer_smoke.py): train a custom TensorFlow graph through `tflearn.TrainOp` and `tflearn.Trainer` on tiny arrays.

## Operating Boundaries

- CPU is sufficient for the selected API, data, graph, training, and recipe-adaptation workflows. CUDA/GPU is optional and unverified by this skill; do not present CPU checks as proof of GPU acceleration.
- Do not run large original example patterns by default. Many TFLearn examples download datasets, open plots, depend on optional libraries, use TensorFlow contrib, or train for many epochs. Use bundled smoke scripts and tiny fixtures first.
- Keep TFLearn guidance in graph mode. Modern TensorFlow 2.x imports may fail because TFLearn uses TensorFlow 1.x private/contrib symbols.
- Do not store checkpoints, TensorBoard logs, or generated model artifacts implicitly in a repository root. Use explicit temporary or experiment directories.
