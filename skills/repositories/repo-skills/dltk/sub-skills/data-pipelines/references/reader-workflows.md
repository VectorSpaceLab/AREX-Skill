# Reader workflows

This guide is for implementing a new reader without opening the DLTK checkout.
It describes the public contract observed in `dltk/io/abstract_reader.py` and
the tutorial/application readers.

## 1. Define the generator boundary

Implement exactly:

```text
read_fn(file_references, mode, params=None)
```

The function is normally a Python generator. `file_references` may be `None`
when the source is synthetic or does not need a file, or it may be a row-like
collection. The IXI examples treat each row as an array-like record whose first
field is an ID, whose second field is sex (`1`/`2` shifted to `0`/`1`), and whose
age is at field index `11`. The MRBrainS example uses `[subject_id,
subject_folder]`. Do not hard-code one row schema into a reusable reader;
validate the selected schema before reading files.

For each sample, make a clear branch:

- **TRAIN/EVAL:** read and orient images, normalize, apply only permitted
  training augmentation, extract full volumes or patches, and yield
  `{'features': {...}, 'labels': {...}}` with stable dtypes and shapes.
- **PREDICT:** read only features and any metadata needed by a separate
  post-processing path, yield one record, then immediately `return` for that
  subject/function. Do not parse labels or index `params` after this branch.

The tutorial and several application readers yield a PREDICT record and then
continue; that is a documented source hazard, not a safe template. Continuing
can yield a second record, access absent labels, or try `params['extract_examples']`
when a serving caller supplied no parameters.

A minimal output policy is:

```text
TRAIN/EVAL: {'features': {'x': float32_array},
             'labels': {'y': int32_or_float32_array}}
PREDICT:    {'features': {'x': float32_array}}
```

If a caller needs `subject_id` or the original SimpleITK image for preserving
origin/spacing/direction, keep that metadata in a parallel Python-side record
or use a separate post-processing input. The legacy `Reader` removes keys not
present in its `dtypes` tree and TensorFlow cannot materialize a SimpleITK
object from `Dataset.from_generator`.

## 2. Build the shape and dtype trees together

The source tutorial uses:

```text
reader_params = {
  'n_examples': 1,
  'example_size': [128, 224, 224],
  'extract_examples': True,
}
example_shapes = {
  'features': {'x': [128, 224, 224, 1]},
  'labels': {'y': []},
}
dtypes = {
  'features': {'x': tf.float32},
  'labels': {'y': tf.int32},
}
```

For segmentation, the application shape is feature `[4, 128, 128, 3]` and
label `[4, 128, 128]`; for regression, a patch label is `[1]`. The shape of a
single yielded item must match the shape tree exactly. A scalar label uses
`[]`; an image label with one channel is not interchangeable with a scalar.
The input batch later has a leading batch dimension.

`Reader(read_fn, dtypes)` stores the dtype tree. Then:

```text
input_fn, init_hook = reader.get_inputs(
    file_references, mode,
    example_shapes=example_shapes,
    shuffle_cache_size=10,
    batch_size=4,
    params=reader_params)
```

Calling `input_fn()` returns TensorFlow feature and label dictionaries. Attach
`init_hook` to the TF1 `MonitoredTrainingSession`/Estimator operation that
consumes the input function. The hook initializes the iterator after session
creation; omitting it commonly leaves the iterator uninitialized.

## 3. Understand nested cleanup

Before yielding into `Dataset.from_generator`, DLTK recursively compares the
record with `self.dtypes`:

- extra dictionary entries are deleted;
- expected keys missing from the record raise `ValueError`;
- a dictionary/value or list/non-list mismatch raises `ValueError`;
- list lengths must match at each inspected level;
- dictionaries nested inside lists are not inspected recursively.

This is not a substitute for validating NumPy dtype and shape. Validate those
before the yield, and use a synthetic malformed-map test to ensure a bad
contract fails before a training graph is built. See
`../scripts/validate_reader_contract.py`.

## 4. Serving inputs

Use the same `Reader` only when the exported model consumes the same feature
names. `reader.serving_input_receiver_fn(placeholder_shapes)` creates
placeholders from `dtypes['features']`:

```text
placeholder shape = [None] + placeholder_shapes['features'][feature_name]
```

A fixed patch export can pass a concrete spatial shape. A full-volume export
may pass `{'features': {'x': [None, None, None, channels]}}` only if the model
supports dynamic spatial dimensions. Labels in `placeholder_shapes` are not
used to create serving placeholders. Confirm the model's rank/channel contract
with the sibling model-building route before exporting.

## 5. SimpleITK reader recipe

1. Construct a path from a validated row, not from an untrusted string that can
   escape the intended dataset root.
2. `sitk_image = sitk.ReadImage(path)` and
   `array = sitk.GetArrayFromImage(sitk_image)`.
3. Normalize each modality independently when that is the selected experiment
   policy, then `np.stack(modalities, axis=-1).astype(np.float32)`.
4. Read a label without a channel dimension and cast it to `np.int32`.
5. If training augmentation is enabled, pass `[images, label]` to a synchronized
   spatial operation and apply image-only intensity operations to `images`.
6. Yield patches or the full volume with a stable dictionary shape.

`GetArrayFromImage` exposes the voxel array in array indexing order rather than
SimpleITK's physical coordinate naming. Treat the result as `[z, y, x]` until
verified against the image direction/spacing, and preserve the `sitk.Image` if
later output must restore metadata.

## 6. Bounded checks before Estimator use

Run the bundled scripts first. Then use one or two tiny in-memory records:

- a valid multimodal image `[4, 6, 6, 2]` and label `[4, 6, 6]`, with a
  synchronized flip/patch assertion;
- a malformed nested shape/dtype map (for example `features.x` is a dict in
  one structure and an array in the other), which must fail before graph
  construction;
- a PREDICT call with `params=None`, which must emit one feature record and no
  label access.

Keep native DLTK/TensorFlow tests bounded and environment-gated. Do not start
full application training or use external downloads as a reader validation.
