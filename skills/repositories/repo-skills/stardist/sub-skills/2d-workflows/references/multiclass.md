# 2D multiclass and shape completion

Use multiclass when each retained instance needs one of a fixed set of
foreground classes in addition to its instance id. The label mask remains an
instance mask; a semantic class image alone is not enough.

## Multiclass contract

Set `Config2D(n_classes=K)`, where `K` is the number of foreground classes.
The network adds `prob_class` with `K+1` channels: index `0` is background and
indices `1..K` are foreground classes.

For each image `i`, supply a class specification aligned with `Y[i]`:

- a mapping `{instance_id: class_id}`, where every class id is `1..K`; or
- an image-level class value/list entry when all objects in that image share
  one class.

The instance labels still require `Y[i]` to be integer `YX` with `0` background
and distinct positive ids. Validate mapping keys and class ranges before
training; do not encode classes as negative instance ids.

A normal training call becomes:

```python
conf = Config2D(n_channel_in=3, n_rays=32, grid=(2,2), n_classes=2,
                use_gpu=False)
model = StarDist2D(conf, name="typed-objects", basedir="models")
history = model.train(
    X_train, Y_train, classes=C_train,
    validation_data=(X_val, Y_val, C_val),
)
```

`classes='auto'` is supported for an ordinary model as an ignored value and
for `n_classes==1` as class 1 for every object. It is not supported for
`n_classes>1`; provide one class entry per image. A multiclass config has three
loss weights `(prob, distance, class)` and exactly `n_classes+1` class weights.
A mismatch raises `ValueError` during config creation.

## Target and prediction behavior

`StarDistData2D` yields a third `prob_class` target for multiclass. It has a
background/foreground categorical channel and follows the same grid-adjusted
spatial target shape as the probability output. Negative ignored regions
propagate `-1` targets that disable the relevant losses.

Prediction:

```python
labels, details = model.predict_instances(
    x, axes="YXC", sparse=True, show_tile_progress=False,
)
class_prob = details["class_prob"]  # (n_objects, K+1)
class_id = details["class_id"]      # argmax per retained object
```

The class prediction is attached to surviving instance polygons after
probability filtering/NMS. Keep `labels` and class metadata separate:
`labels==7` means instance 7, not class 7. `class_id` can be `0` if background
has the largest probability; downstream code must define whether to reject,
review, or retain such detections. Assert
`len(class_id)==len(details['prob'])` and
`class_prob.shape == (n_objects,K+1)`.

`return_predict=True` forces dense output and adds the dense class map to the
returned prediction tuple. This is a diagnostic path and can be expensive.

## Shape completion

`train_shape_completion` is a training-time behavior. With the default
`False`, objects clipped by a patch/image boundary are not learned as completed
objects. With `True`, `StarDistData2D` clears border-touching labels when
building the distance target, using a crop `b=train_completion_crop` so the
network can learn from interior evidence.

Choose `train_completion_crop` from the largest expected object extent, not
blindly from the default `32`. The crop must be evenly divisible by every
`grid` value, and `train_patch_size - 2*b` must remain positive and divisible
by the model's U-Net/grid spatial factors. Increase batch size if the crop
removes a large fraction of each patch. This option requires retraining; it
cannot be enabled by an inference argument on an existing model.

## Checks and recovery

- If classes are ignored, inspect `model.config.n_classes`; `None` deliberately
  selects ordinary instance-only behavior.
- If the class loss errors, use three loss weights and `K+1` class weights.
- If `classes='auto'` fails with multiple classes, build explicit mappings for
  every image and validation sample.
- If all objects are class 1, check mapping distribution and class weights
  before changing thresholds; this may be the intended one-class setup.
- If boundary objects are truncated, inspect the persisted config and retrain
  with shape completion and a justified crop. Do not claim an inference-only
  repair.
- `export_TF` warns and removes the multiclass output in this baseline. Keep
  the native model when `class_prob`/`class_id` is required; BioImage.IO/export
  integration belongs to [deployment-integration](../../deployment-integration/SKILL.md).

Generic instance metrics and polygon geometry belong to
[evaluation-geometry](../../evaluation-geometry/SKILL.md).
