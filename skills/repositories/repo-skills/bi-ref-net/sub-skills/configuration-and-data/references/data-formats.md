# Data Formats Reference

This reference describes the BiRefNet dataset tree and the pairing rules implemented by `MyData(datasets, data_size, is_train=True)`.

## Directory layout

Each dataset lives under a task directory and must expose separate image and ground-truth folders:

```text
<data-root>/
  <task>/
    <dataset>/
      im/
      gt/
```

Examples of valid dataset selections:

- one dataset: `DIS-TR`
- combined datasets: `TR-HRSOD+TR-UHRSD`

`MyData` splits the `datasets` string on `+` and scans each dataset folder in order.

## File pairing rules

`MyData` uses these rules when building image/label pairs:

- The image folder is scanned for files with one of these exact suffixes: `.png`, `.jpg`, `.PNG`, `.JPG`, `.JPEG`.
- For each image file, the label is searched in `gt/` using the same basename and the same allowed suffix list.
- A basename is valid when exactly one image file and exactly one label file exist for that basename.
- Matching is based on basename, not on the original extension.
- If no matching label is found, the dataset object reports the missing path and raises a count mismatch error.

## Returned samples

When `is_train=True`, `MyData[index]` returns:

1. image tensor
2. label tensor
3. class label id or `-1`

When `is_train=False`, `MyData[index]` returns:

1. image tensor
2. label tensor
3. original label path

## Training-time transforms

Training samples go through this sequence:

1. optional background color synthesis
2. `preproc(...)`
3. tensor conversion and normalization when fixed-size training is active

`preproc(...)` applies, in order:

- `flip`
- `crop`
- `rotate`
- `enhance`
- `pepper`

If `background_color_synthesis` is enabled, the active preproc list is reduced to `flip` only in the checked defaults.

## Background color synthesis

When enabled, the loader:

- treats the label as an alpha matte
- composites the foreground against a synthetic background
- samples backgrounds that are black/gray/white, object-similar, or arbitrary colors

This is a training-only augmentation.

## Dynamic-size collation

`custom_collate_fn(batch)` is used when `dynamic_size` is set.

Behavior:

- The configured dynamic-size range is sorted before sampling.
- One width and one height are sampled for the whole batch.
- Each dimension is floor-rounded to a multiple of 32.
- Every sample in the batch is resized to that same batch size before collation.

If `dynamic_size` is not set, the loader uses the fixed `size` from `Config`.

## Inference-size handling

For `is_train=False`, the dataset path keeps the original image size until the final inference resize step, then floor-rounds both dimensions to the nearest multiple of 32 before tensor conversion.

This means inference inputs should be large enough that the floor-rounded size is still meaningful for the model.

## Auxiliary classification filename assumption

If `auxiliary_classification` is enabled, `MyData` reads the class name from the ground-truth filename.

Required format:

- the basename must contain at least four `#`-separated fields
- the class name is taken from field index `3`

A file name that does not expose that field will fail during class-id lookup.

## Memory behavior

If `load_all` is enabled, the dataset preloads every image and label into RAM.

Keep that mode off unless the dataset is small and the host has enough memory for repeated copies in multi-process loading.
