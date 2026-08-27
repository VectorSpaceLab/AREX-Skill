# Verified public API reference

These are the important entry points for the package contract. Use Python
introspection in the active environment when a newer release may differ.

## Writer and reader

```python
DatasetWriter(
    fname: str,
    fields: Mapping[str, Field],
    page_size: int = 4 * (1 << 21),
    num_workers: int = -1,
)

DatasetWriter.from_indexed_dataset(
    dataset, indices=None, chunksize=100, shuffle_indices=False
)
DatasetWriter.from_webdataset(shards, pipeline)

Reader(fname, custom_handlers={})
```

`DatasetWriter` creates the custom `.beton` file. `Reader` validates the format
version, reconstructs field handlers and metadata, and exposes `num_samples`,
`field_names`, `handlers`, `metadata`, `page_size`, and `alloc_table` for
structural checks. The writer's mapping order is part of the file contract.

## Loader

```python
Loader(
    fname, batch_size, num_workers=-1, os_cache=True,
    order=OrderOption.SEQUENTIAL, distributed=False, seed=None,
    indices=None, pipelines={}, custom_fields={}, drop_last=True,
    batches_ahead=3, recompile=False, order_kwargs={}
)
```

`OrderOption` has `SEQUENTIAL`, `RANDOM`, and `QUASI_RANDOM`. `Loader` is
iterable, has length determined by `drop_last` and the selected `indices`, and
has `filter(field_name, condition)` for a material predicate scan. Omitted
pipeline entries use field defaults; an explicit `None` disables a field.

## Fields and decoders

Public built-ins are `IntField`, `FloatField`, `RGBImageField`, `BytesField`,
`NDArrayField`, `TorchTensorField`, and `JSONField`. Their decoders include
`IntDecoder`, `FloatDecoder`, `NDArrayDecoder`, `BytesDecoder`,
`SimpleRGBImageDecoder`, `RandomResizedCropRGBImageDecoder`, and
`CenterCropRGBImageDecoder`.

Important constructors:

```python
RGBImageField(write_mode='raw', max_resolution=None,
              smart_threshold=None, jpeg_quality=90,
              compress_probability=0.5)
NDArrayField(dtype, shape)
TorchTensorField(dtype, shape)
RandomResizedCropRGBImageDecoder(output_size,
                                 scale=(0.08, 1.0),
                                 ratio=(0.75, 4/3))
CenterCropRGBImageDecoder(output_size, ratio)
```

`SimpleRGBImageDecoder()` requires constant image resolution; use a crop/resize
decoder for variable-resolution files.

## Common operations

`ffcv.transforms` exports `ToTensor`, `ToDevice`, `ToTorchImage`, `Convert`,
`View`, `Squeeze`, `NormalizeImage`, `RandomResizedCrop`,
`RandomHorizontalFlip`, `RandomTranslate`, `Cutout`, `ImageMixup`,
`LabelMixup`, `MixupToOneHot`, `Poison`, `ReplaceLabel`, `ModuleWrapper`, and
random brightness/contrast/saturation operations. Native transforms operate on
NumPy HWC data until `ToTensor`; torch modules are wrapped automatically.

A custom transform subclasses `ffcv.pipeline.operation.Operation` and provides
`generate_code()` plus `declare_state_and_memory(previous_state)`. Its callable
normally receives input and an allocated destination; set
`callable.with_indices = True` to receive sample ids as a third argument.
