---
name: layers-and-ops
description: "Build TFLearn TensorFlow v1 graph components, layer APIs,
  operations, collections, shapes, and train-op wiring."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Layers and Ops

Use this sub-skill when the task is to construct, inspect, or debug TFLearn graph components: input layers, dense/dropout/reshape layers, convolution/recurrent/embedding/normalization layers, merge/multi-output branches, estimator `regression`, activations, objectives, metrics, optimizers, initializers, regularizers, variables, summaries, and TensorFlow graph collections.

Do not use this sub-skill for full training loops, checkpoint save/load, dataset loading, or long model-family examples. Route those to `training-and-persistence`, `data-input-pipelines`, or `advanced-model-recipes` respectively.

## Runtime assumptions

- TFLearn is a TensorFlow-v1-style package. The verified package baseline is TFLearn 0.5.0 with TensorFlow 1.15.5 and CPU execution.
- Use `tensorflow.compat.v1` and disable v2 behavior before building graphs when the surrounding runtime may be TensorFlow 2.x.
- CPU is sufficient for the graph-construction workflows here. CUDA only changes performance/device placement and is not required by this sub-skill.

## Read first

- API choices, shapes, names, and collection side effects: [references/api-reference.md](references/api-reference.md)
- Concrete graph-construction workflows and validation commands: [references/workflows.md](references/workflows.md)
- Failure diagnosis for shapes, names, collections, TensorFlow versions, scopes, recurrent layers, and GPU assumptions: [references/troubleshooting.md](references/troubleshooting.md)
- Safe local graph smoke check: [scripts/layer_graph_smoke.py](scripts/layer_graph_smoke.py)

## Operating checklist

1. **Start with a clean TensorFlow graph.** Prefer `with tf.Graph().as_default():` or `tf.reset_default_graph()` before constructing a new network in notebooks/tests.
2. **Create or register inputs.** Prefer `tflearn.input_data(shape=[None, ...], name="...")`; if using raw placeholders, add them to `tf.GraphKeys.INPUTS` yourself before relying on TFLearn feed helpers.
3. **Choose layers by rank.** Dense layers accept rank >=2 and flatten extra dimensions; conv1d/2d/3d require rank 3/4/5 respectively; recurrent layers expect rank >=3; embedding expects rank 2 integer-id inputs.
4. **Use operation names intentionally.** String activations, losses, metrics, optimizers, initializers, and regularizers are resolved by TFLearn registries; use the valid names in the API reference or pass callables/classes.
5. **Use `regression` only to create train-op metadata.** It returns the incoming prediction tensor while adding a target placeholder and `TrainOp` to graph collections. Actual `fit`, `predict`, `save`, and `load` belong to `training-and-persistence`.
6. **Validate collections before handing off.** Check `INPUTS`, `TARGETS`, `TRAIN_OPS`, `LAYER_TENSOR/<name>`, `LAYER_VARIABLES/<scope>`, `ACTIVATIONS`, and `REGULARIZATION_LOSSES` as applicable.
7. **Run the bundled smoke script** when verifying a new environment or debugging graph basics:

   ```bash
   python scripts/layer_graph_smoke.py --help
   python scripts/layer_graph_smoke.py
   python scripts/layer_graph_smoke.py --skip-session-run
   ```

## Quick routing by task

| User intent | Use this sub-skill for | Then route elsewhere if needed |
|---|---|---|
| Build an MLP/CNN/RNN graph | Layer API choice, shapes, names, scopes, variables, train-op collection | Actual `.fit()`/callbacks/checkpoints: `training-and-persistence` |
| Attach preprocessing/augmentation to an input layer | The `input_data(data_preprocessing=..., data_augmentation=...)` attachment point | Creating/validating preprocessing objects or loading files: `data-input-pipelines` |
| Add custom TensorFlow ops with TFLearn ops | Objectives, metrics, optimizers, summaries, variables, `TrainOp`-ready tensors | Custom training loop orchestration: `training-and-persistence` |
| Debug invalid activation/loss/metric/shape | Registry names, expected ranks, collection side effects | Environment/import failures beyond this scope: root troubleshooting |
| Adapt a large architecture example | Primitive layer behavior and graph pieces | Recipe selection and expensive example reduction: `advanced-model-recipes` |

## Hard boundaries

- Do not include instructions to download datasets, run original examples, or train for many epochs.
- Do not require the original repository checkout; all operational details needed by this sub-skill are in the references and bundled script.
- Do not link public runtime instructions to source repository paths or private inspection environments.
