# DLTK input API reference

This reference distills the public source modules at DLTK 0.2.1, commit
`f94d3bb509eb0741164149acbef0788769a869e4`. The signatures below were also
checked with Python `inspect.signature` against the DLTK 0.2.1 package. The
package is a TensorFlow 1.x/Python 3.7-era API; do not silently modernize its
semantics while claiming source compatibility.

## Preprocessing

| Function | Observed signature | Contract |
| --- | --- | --- |
| `whitening` | `whitening(image)` | Casts to `float32`; returns `(image - mean) / std` when `std > 0`, otherwise an all-zero array with the same shape. Statistics are over the whole array, including channels if present. |
| `normalise_zero_one` | `normalise_zero_one(image)` | Casts to `float32`; maps global min/max to `[0, 1]`. A constant array becomes zero. |
| `normalise_one_one` | `normalise_one_one(image)` | Calls zero-one normalization, then `* 2` and `- 1`; a constant array becomes `-1`. |
| `resize_image_with_crop_or_pad` | `resize_image_with_crop_or_pad(image, img_size=(64, 64, 64), **kwargs)` | Intended to center-crop or symmetrically pad each spatial dimension and pass `kwargs` to `np.pad`. It asserts `image.ndim == len(img_size)` or `image.ndim - 1 == len(img_size)`. |

For the intended channel-last case, use `img_size` for spatial dimensions and
preserve the final channel dimension. The legacy implementation builds a list
of slices and calls `image[slicer]`; modern NumPy releases can require a tuple
for multi-axis indexing, so this old helper may raise `IndexError` outside its
original dependency range. A safe reimplementation should use
`image[tuple(slicer)]`, append `(0, 0)` for the channel to `pad_width`, and test
both crop and pad without changing the documented output shape. This is a
compatibility repair, not evidence that the old implementation supported modern
NumPy.

Normalization is not a registration or foreground-mask operation. Decide
whether background voxels participate in the statistics before choosing a
normalizer, and record that choice with the experiment.

## Augmentation and patch extraction

| Function | Observed signature | Output and caveats |
| --- | --- | --- |
| `flip` | `flip(imagelist, axis=1)` | With probability 0.5, flips one ndarray or each member of a list along `axis`; a singular ndarray is returned as an ndarray. A list is modified by replacing members. The random decision is not seeded by the function. |
| `add_gaussian_offset` | `add_gaussian_offset(image, sigma=0.1)` | Adds one random offset per final channel using broadcasting. Mutates `image` in place and returns it. |
| `add_gaussian_noise` | `add_gaussian_noise(image, sigma=0.05)` | Adds element-wise Gaussian noise. Mutates `image` in place and returns it. |
| `elastic_transform` | `elastic_transform(image, alpha, sigma)` | Requires equal-length `alpha` and `sigma`; generates random displacement fields and uses `scipy.ndimage.map_coordinates(..., order=0, mode='reflect')`. It returns a new array and is not a safe image/label synchronization or label interpolation primitive. |
| `extract_class_balanced_example_array` | `extract_class_balanced_example_array(image, label, example_size=[1, 64, 64], n_examples=1, classes=2, class_weights=None)` | Requires `image.shape[:-1] == label.shape`, a channel-last image, and spatial `example_size`. Returns `(patch_images, patch_labels)` with leading batch dimension. |
| `extract_random_example_array` | `extract_random_example_array(image_list, example_size=[1, 64, 64], n_examples=1)` | Takes one ndarray or a list/tuple of aligned arrays and returns one batched ndarray or a list of batched arrays. All aligned arrays must have compatible shapes. |

The augmentation implementation has several source-observable details worth
preserving in a reader contract:

- `flip([image, label], axis=...)` is the source pattern for one synchronized
  random decision. Use a mutable list; although the docstring mentions tuples,
  assigning a flipped member can fail for a tuple when the random branch runs.
- `add_gaussian_offset` and `add_gaussian_noise` mutate arrays. Use a copy when
  retaining the normalized input or when an image is shared by multiple labels.
  Never add them to integer labels.
- `extract_random_example_array` samples random starts with a range based on
  `shape - example_size`; an exact-size dimension falls back to start zero. Test
  the resulting shape and do not rely on it as a deterministic sampler.
- `extract_class_balanced_example_array` converts an integer `classes` to
  `range(classes)`, requires `n_examples >= number_of_classes`, and uses
  `class_weights` only when its length matches the selected classes. It samples
  available class centers without replacement, clamps centers to valid patch
  bounds, and truncates each class to the smallest availability ratio. Missing
  classes can therefore produce fewer patches than requested. Ensure every class
  needed by the loss has voxels in the label fixture before calling it.
- The source uses `np.int` while computing patch radii. That alias is removed in
  modern NumPy; use a compatible TF1 environment or an explicitly reviewed
  integer replacement rather than assuming the original helper runs unchanged.

A useful synchronized synthetic case is an image of shape `[Z, Y, X, 2]` and a
label of `[Z, Y, X]`: choose one spatial slice, apply the same flip/patch start
to both, and assert that the label remains aligned with both image channels.

## Reader classes

### `IteratorInitializerHook`

`IteratorInitializerHook()` subclasses `tf.train.SessionRunHook`. Its
`after_create_session(self, session, coord)` calls the function stored in
`iterator_initializer_func`. `Reader.get_inputs` sets that function to run the
`tf.data` iterator initializer. The hook is therefore required when using the
returned input function in a TF1 monitored session or Estimator call.

### `Reader`

Observed constructor:

```text
Reader(read_fn, dtypes)
```

`dtypes` is a nested structure of TensorFlow `tf.DType` objects corresponding
to every TensorFlow-visible component yielded by the generator. The source
`Reader` does not infer dtypes from NumPy values.

Observed method signatures:

```text
get_inputs(self, file_references, mode, example_shapes=None,
           shuffle_cache_size=100, batch_size=4, params=None)
serving_input_receiver_fn(self, placeholder_shapes)
```

`get_inputs` returns `(input_fn, iterator_initializer_hook)`. Calling the
`input_fn` creates a dataset from the generator, repeats indefinitely, shuffles
with `shuffle_cache_size`, batches by `batch_size`, prefetches one batch, and
returns `(next_dict['features'], next_dict.get('labels'))`. `example_shapes`
are **one-element** shapes; batching adds a leading batch dimension. For
example, a feature shape `[4, 128, 128, 3]` is observed by a model as
`[batch, 4, 128, 128, 3]`, and scalar label shape `[]` becomes `[batch]`.

The reader's nested cleaner recursively deletes example keys absent from the
`dtypes` mapping and raises for missing expected keys or dict/list-versus-value
shape mismatches. It explicitly does not recurse into dictionaries nested in
lists. It also adds `ex['labels'] = None` when a record has no labels, before
checking that the record is a dictionary. Keep non-Tensor metadata out of the
TensorFlow-visible contract or declare a Tensor-compatible representation; a
SimpleITK object cannot be yielded through a dtype tree.

`serving_input_receiver_fn(placeholder_shapes)` returns a function that creates
one placeholder for every key in `dtypes['features']`, with shape
`[None] + placeholder_shapes['features'][key]` and the matching dtype. It
returns `tf.estimator.export.ServingInputReceiver(inputs, inputs)`, so the
receiver features and receiver tensors are the same feature dictionary. The
function does not create label placeholders. Use `None` only for dimensions
that the downstream exported model can actually accept.
