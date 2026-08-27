# Troubleshooting

This page collects the failure modes that are specific to dataset preparation,
image preprocessing, and 3D augmentation.

## Important constraint

The repository's original data-loader checks need real dataset folders and are
therefore blocked in a synthetic-only environment. Use the bundled smoke scripts
for code-path checks, and place the real datasets in the documented folders
before running the native repo checks.

## Symptom → cause → action

| Symptom | Likely cause | Action |
| --- | --- | --- |
| `Problem reading data. Check the data paths.` | A `glob` search returned no files. | Confirm the folder names, extensions, and nesting in [data-layout.md](./data-layout.md). |
| `crop size is too big` | `find_random_crop_dim` received a crop larger than the source volume. | Reduce `dim` or verify the source volume dimensions before patch generation. |
| `IMAGE DOES NOT EXIST ...` | COVIDx or COVID CT path roots do not match the manifest entries. | Check whether the manifest stores relative paths and whether the images live under the expected root folder. |
| `FileNotFoundError` while loading a manifest | The loader uses a fixed manifest path or a missing split file. | Mirror the expected manifest names or wrap the loader in a tiny adapter for synthetic checks. |
| `select_full_volume_for_infer` fails with an undefined name | The helper is incomplete outside a subset of branches. | Use `generate_datasets(...)` plus `get_viz_set(...)`, or patch the helper before relying on it for a new dataset branch. |
| A paired augmentation crashes when the label is missing | `RandomRotation`, `RandomShift`, and `RandomZoom` touch `label.any()` and expect a real label array. | Pass a label volume, even for smoke tests, or skip the paired transform when no label exists. |
| Rotation changes the image shape | `random_rotate3D` uses `ndimage.rotate` with the default reshape behavior. | Only assume the output stays 3D; do not assume the original shape is preserved. |
| `load_medical_image(..., rescale=...)` appears to do nothing | The current code path does not assign the rescaled array back into the return value. | Use `rescale_data_volume(...)` directly when you need a resized array. |
| `transform_coordinate_space` returns a warped or blank volume | The two NIfTI affines or shapes are not compatible. | Inspect the source affines with `load_affine_matrix(...)` and verify that both images are registered as expected. |
| `COVIDxDataset` label ids look wrong | The loader uses a fixed label mapping. | Use the built-in mapping: `pneumonia -> 0`, `normal -> 1`, `COVID-19 -> 2`. |
| `CovidCTDataset` class ids look reversed | The loader orders classes as `CT_COVID` first and `CT_NonCOVID` second. | Expect `0` for COVID and `1` for non-COVID. |
| `MRBRAINS` batches come back as NumPy arrays | The loader returns arrays, not tensors, in `__getitem__`. | Convert to tensors in your caller if a later stage expects `torch.Tensor`. |
| `IXI` synthetic smoke passes but T2 looks identical to T1 | The current loader reads the T2 path from the T1 path in source and is therefore easy to misread in tiny tests. | Treat the synthetic smoke as a layout check only; verify the upstream loader before using real IXI data. |
| `RandomCropToLabels` does not crop the label | The helper returns the cropped image and the original label unchanged. | If you need a paired crop, wrap it or replace it with a label-aware crop that updates both arrays. |

## Quick recovery checklist

1. Verify the folder tree against the dataset-specific table.
2. Confirm the file extension and case sensitivity of the glob pattern.
3. Check whether the loader expects labels, image-only input, or cached `.npy` patches.
4. Re-run the synthetic smoke script for the relevant helper before touching real data.
5. Only then move to the native repo checks that require real datasets.
