# API reference

## Purpose

Read this for the verified transform, sampler, and loader signatures.

## Verified base transform contract

- `BaseTransform(prob=1)` defines `fit`, `__call__`, and `__repr__` as abstract
  methods.
- Concrete transforms in this package generally accept images as `*images` and
  return either a single image or a list of images.

## Deterministic transforms

### Image transforms

- `Astype(dtype)`
- `Smooth(sigma, sigma_in_physical_coordinates=True, FWHM=False, max_kernel_width=32)`
- `Crop(indices=None)`
- `Resample(resample_params, use_voxels=True, interp_type=1)`
- `Slice(axis, idx, collapse_strategy=0)`
- `Pad(shape=None, pad_width=None, value=0.0)`

### Intensity transforms

- `ImageMath(operation, *args)`
- `BiasCorrection()`
- `StandardNormalize(mean=None, std=None)`
- `RangeNormalize(min=0, max=1)`
- `Clip(lower, upper)`
- `QuantileClip(lower, upper)`
- `Threshold(value, as_upper=False)`

### Math transforms

- `Abs()`, `Ceil()`, `Floor()`, `Log()`, `Exp()`, `Sqrt()`, `Power(value)`

### Shape / spatial / label transforms

- `AddChannel(channels_first=False)`
- `Reorient(orientation)`
- `ApplyAntsTransform(transform)`
- `AffineTransform(array, reference=None)`
- `Shear(shear, reference=None)`
- `Rotate(rotation, reference=None)`
- `Zoom(zoom, reference=None)`
- `Flip(axis=0)`
- `Translate(translation, reference=None)`
- `LabelsToChannels(keep_values=False, channels_first=False)`

### Generic utility transforms

- `CustomFunction(fn, **kwargs)`
- `NumpyFunction(fn, **kwargs)`

## Random transforms

- `RandomCrop(shape)`
- `RandomShear(min_shear, max_shear, reference=None, p=1)`
- `RandomRotate(min_rotation, max_rotation, reference=None, p=1)`
- `RandomZoom(min_zoom, max_zoom, reference=None, p=1)`
- `RandomFlip(axis=0, p=0.5)`
- `RandomTranslate(min_translation, max_translation, reference=None, p=1)`

## Samplers

### `BaseSampler(batch_size, shuffle=False)`

Plain record batching with optional shuffling.

### `SliceSampler(batch_size=24, axis=-1, shuffle=False)`

Creates 2D slices from 3D images and batches the slices.

### `PatchSampler(patch_size, stride, batch_size, shuffle=False)`

Creates 2D patches from 2D images.

### `BlockSampler(block_size, stride, batch_size, shuffle=False)`

Creates 3D blocks from 3D images.

### `SlicePatchSampler(patch_size, stride, axis, batch_size, shuffle=False)`

Slices first, then extracts 2D patches from the slices.

## Loader

### `Loader(dataset, images_per_batch, transforms=None, channels_first=False, shuffle=False, sampler=None)`

- `copy(dataset=None, drop_transforms=False)` returns a new loader with the same
  configuration.
- `to_keras(output_signature=None)` turns the loader into a `tf.data.Dataset`
  wrapper.
- `__iter__()` applies dataset transforms, then loader transforms, then the
  sampler, then channel expansion and conversion to numpy arrays.

## Notes that matter

- Transform dictionaries may use a single key or a tuple key. Tuple keys mean
  the transform should operate on the named values together.
- Transform values may be a single transform or a list/tuple of transforms.
- `channels_first=None` disables the loader's extra channel expansion logic.
- `Loader.__len__()` is based on `images_per_batch`, not sampler batch size.
