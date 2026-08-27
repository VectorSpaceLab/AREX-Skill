# Inference API reference

These DLTK 0.2.1 signatures define the geometry, assembly, and metric contracts used by this route:

```text
SlidingWindow(img_shape, window_shape, has_batch_dim=True, striding=None)
sliding_window_segmentation_inference(session, ops_list, sample_dict,
                                      batch_size=1, striding=None)
dice(predictions, labels, num_classes)
abs_vol_difference(predictions, labels, num_classes)
crossentropy(predictions, labels, logits=True)
```

The package's deployment code is TensorFlow 1.x code. `SlidingWindow` and the assembly helper themselves use NumPy and a TensorFlow-like session/operation interface, but a real saved-model deployment still requires the TF1 graph runtime and `tf.contrib.predictor`.

## `SlidingWindow`

`img_shape` and `window_shape` are spatial shapes. With the default `has_batch_dim=True`, each emitted slicer is a list whose first item is `slice(None)` for batch, followed by one spatial slice per axis, followed by `slice(None)` for channels. The iterator advances in row-major-like carry order. `striding` is the step between positions, not an overlap count; a smaller step means more overlap. If it is omitted, the constructor uses `window_shape` as the step. At a boundary it emits a final slice ending at the image boundary, with `low = image_dim - window_dim`.

The implementation has intentionally minimal validation. A window larger than its image, a non-positive step, mismatched ranks, or an invalid type can create negative/empty slices or fail late. Validate before constructing it. Pass a list or tuple for `striding`; the implementation uses a truth-value check, so a NumPy array can raise an ambiguous-truth-value error.

## `sliding_window_segmentation_inference`

Expected contract:

- `sample_dict` maps one or more input placeholders to NumPy arrays. The first value determines the runtime shape and is normally `[batch, spatial..., channels]`; all values must be slice-compatible with the same spatial windows.
- The first placeholder's static shape provides `pl_bshape = static_shape[1:-1]`, the input value provides `inp_bshape = actual_shape[1:-1]`, and the first op's static shape provides `op_bshape = op_shape[1:-1]`.
- For rank-matched outputs, each result is allocated as `[input_batch] + inp_bshape + [output_channels]`. An output with a different rank does not receive a useful accumulator; keep deployment ops rank-compatible.
- `out_diff = pl_bshape - op_bshape`. The input arrays are padded spatially by `diff // 2` on the left and the remainder on the right. This is how a valid/convolutional model whose output patch is smaller than its input patch is aligned back to the full input volume. Negative differences are not a supported way to request a larger output patch: NumPy padding will fail.
- If `striding` is omitted, equal input/output patch shapes default to `max(1, op_bshape // 2)` (50% step/overlap), while a smaller output defaults to `op_bshape` (non-overlapping output tiles). Explicit strides override both defaults.
- The helper advances a padded-input `SlidingWindow` and an output-volume `SlidingWindow` together. For every op it adds the returned patch to `out_dummies[idx][out_slicer]` and increments `out_dummy_counter[idx][out_slicer]`. With `batch_size == 1` this happens one session call at a time. With a larger `batch_size`, windows are concatenated on axis 0, run together, split back into individual windows, and assembled at their paired output slices. `batch_size` is the number of windows per session call; it is not the volume's input batch dimension.
- The final return is `[o / c for o, c in zip(out_dummies, out_dummy_counter)]`. There is no zero-counter guard. Bad geometry can therefore produce a divide-by-zero warning/NaN or a negative/empty-slice error instead of an actionable message. Use `sliding_window_plan.py` first.

A model with static batch `1` may not accept a batched session call. For `batch_size > 1`, the fetched op should have a dynamic/compatible batch dimension and the model must accept the concatenated patch batch. The smoke script uses a synthetic dynamic batch to exercise this assembly path.

## Predictor tensor access

## Predictor tensor access: public signature first

Start with the public SavedModel signature and predictor call. This confirms the
export's string keys and ordinary input/output shapes without assuming names such
as `x`, `y_prob`, or `logits`:

```python
import tensorflow as tf
from tensorflow.contrib import predictor

with tf.Graph().as_default():
    with tf.Session() as session:
        meta_graph = tf.saved_model.loader.load(
            session, [tf.saved_model.tag_constants.SERVING], export_dir)
        signature = meta_graph.signature_def[
            tf.saved_model.signature_constants.DEFAULT_SERVING_SIGNATURE_DEF_KEY]
        input_keys = sorted(signature.inputs)
        output_keys = sorted(signature.outputs)
        print('inputs:', input_keys)
        print('outputs:', output_keys)

my_predictor = predictor.from_saved_model(export_dir)
public_output = my_predictor({input_keys[0]: image_with_batch})
print('returned:', sorted(public_output))
```

Use the public call for ordinary exported-model inference whenever it provides the
needed operation. It returns computed values, not graph tensors. Full-volume
`sliding_window_segmentation_inference` has a narrower contract: it needs a
session plus graph operations so it can execute one patch at a time and assemble
aligned outputs. Only after the public signature probe succeeds should a TF1
full-volume integration inspect the predictor's private fields:

```python
# Use exact keys and shapes confirmed by the public signature probe above.
feed_tensor = my_predictor._feed_tensors[input_keys[0]]
output_key = 'y_prob'  # replace only after checking output_keys and its shape
prob_tensor = my_predictor._fetch_tensors[output_key]
prediction = sliding_window_segmentation_inference(
    session=my_predictor.session,
    ops_list=[prob_tensor],
    sample_dict={feed_tensor: image_with_batch},
    batch_size=32)[0]
```

`_fetch_tensors`, `_feed_tensors`, and `session` are private predictor attributes.
They are a verified TF1-specific escape hatch for the sliding helper, not a stable
public API. If the public signature probe or shape check fails, stop and inspect
the export rather than guessing private names. Do not advertise this as modern
TensorFlow 2 predictor support: `tf.contrib` was removed from TF2.

## Output conversion

- Segmentation: `y_prob` is already the probability output in the MRBrainS deploy path. Assemble probabilities first and use `np.argmax(assembled, axis=-1)` to obtain per-voxel class IDs. `pred[0]` removes the synthetic batch before image export.
- If the output is `logits`, do not call it a probability. Use a stable softmax when calibrated probabilities are required; for class IDs, argmax over the last class axis is sufficient. Check the export's inspected output signature and the model contract in [model-building](../../model-building/SKILL.md).
- Regression: the IXI age example fetches `logits` for a batch of random crops and uses `np.mean(y_)` before absolute error. Classification fetches `y_prob`, uses `np.mean(y_, axis=0)`, then `np.argmax`. Keep these aggregation axes distinct.

## Metrics

`dltk.core.metrics.dice` loops over classes and returns one `float32` score per class. It computes `2 * intersection / (prediction_count + label_count)` with no explicit empty-class guard; an absent class in both arrays yields NaN under NumPy. The MRBrainS application reports `np.nanmean(metrics.dice(pred, lbl, num_classes)[1:])`, excluding index 0 as background and ignoring NaN classes. State that policy with the result.

`abs_vol_difference` returns one `float32` value per class:

```text
abs(predicted_voxel_count - label_voxel_count) /
    (label_voxel_count + 1e-6)
```

It is a voxel-count relative difference, not a physical-volume measurement unless the voxel geometry is incorporated separately. This DLTK function uses the removed/deprecated `np.float` alias; a modern NumPy import may fail before calculation. Treat that as an environment compatibility issue, not as permission to silently change metric semantics.

`crossentropy` accepts one-hot labels. With `logits=True` it computes a stable softmax by subtracting the per-voxel maximum; with `logits=False` it uses the supplied probabilities and adds `1e-8` inside `log`.
