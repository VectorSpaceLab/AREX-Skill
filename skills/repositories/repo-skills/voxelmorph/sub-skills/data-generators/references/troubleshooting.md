# Troubleshooting

## Purpose

Use this reference when VoxelMorph data loading or generator selection fails before the model code ever runs.

## Common failures and fixes

| Symptom | Likely cause | What to do next |
| --- | --- | --- |
| `file does not exist` or `'%s' is not a file.` | A path was passed where no readable local file exists. | Check the path, verify the file extension, or expand the directory/glob before retrying. |
| `expected a .npz file` | A non-`.npz` file was sent to the NPZ validator. | Use the validator only for `.npz` archives; use a separate probe for NIfTI or MGZ. |
| `missing volume key 'vol'` | The archive does not follow the standard VoxelMorph `.npz` convention. | Add the `vol` key or pass `--allow-single-array-npz` only when the file has exactly one array and that fallback is acceptable. |
| `missing required segmentation key 'seg'` | A semisupervised or supervised workflow was requested without a segmentation array. | Add `seg`, switch to an unsupervised generator, or relax the requirement if the downstream model truly does not use labels. |
| `segmentation is not integer typed` | A label map was stored as float or another non-integral dtype. | Convert the label map to integers before using `load_labels`, `semisupervised`, or surface workflows. |
| `segmentation shape ... differs from volume shape ...` | The volume and segmentation were not aligned or were cropped differently. | Rebuild the data pair so that `vol` and `seg` share the same spatial shape, or explicitly acknowledge the mismatch with `--allow-seg-shape-mismatch` if the workflow can tolerate it. |
| `volume shape ... does not match expected ...` | The local `.npz` file does not match the expected training geometry. | Fix the source data or update the expected shape to the real dataset shape before building a generator. |
| `volume shape ... differs from first valid volume shape ...` | A list mixes incompatible shapes. | Normalize all files to one spatial shape before using a generator that assumes consistency. |
| `Number of image files must match number of seg files.` | `vol_names` and `segs` were not paired one-to-one. | Rebuild the list so that each image path has a matching segmentation path in the same order. |
| `no labels found for argument` | `load_labels` found no files with a supported extension. | Point it at a folder or glob that actually contains supported label-map files. |
| `file ... has non-integral data type` from `load_labels` | The label map is not a discrete integer segmentation. | Convert the labels to integer type or use a different dataset representation. |
| `cleaning segmentation failed` | The mask was too small, too noisy, or not a clean binary object. | Clean or enlarge the mask, or use a different preprocessing strategy before surface extraction. |
| `number of surface point should be greater than 0` | `surf_semisupervised` was called with `nb_surface_pts <= 0`. | Pass a positive surface-point count. |
| `only batch size 1 supported for now` | `surf_semisupervised` was called with a larger batch size. | Use batch size 1 or rewrite the generator for your own batch strategy. |
| `align_seg generator is only implemented for single label` | `align_segs=True` was used with multiple labels. | Reduce the label set to one label or keep segmentation alignment disabled. |
| `shape mismatch` in `conditional_template_creation` | Attribute vectors or atlas batches are not shaped as expected. | Make sure every attribute value is a numeric vector that stacks cleanly across the batch. |
| `no .npz files were provided or discovered` | The validator was invoked with empty input, a bad glob, or a directory containing no `.npz` files. | Fix the list or glob, or point the validator at a directory that actually contains `.npz` files. |

## Generator-specific pitfalls

### `template_creation`

- The current implementation caches zero tensors with a batch dimension of 1.
- If you raise the batch size, re-check the generator output shapes before using it in a downstream model.

### `semisupervised`

- The discrete segmentation is converted to probability channels over the requested label list.
- This is not the same as handing a raw integer label map to the model.
- The generator uses explicit three-axis downsampling, so treat it as a 3D workflow.

### `surf_semisupervised`

- Surface arrays include a final label-index column.
- The generator depends on clean binary masks, signed-distance transforms, and randomized surface sampling.
- If the surface point cloud is empty, inspect the label map and the cleanup threshold first.

### `synthmorph`

- The input is a list or array of preloaded label maps, not filenames.
- If `flip=True`, the same random flip axes are applied to both halves of the pair.
- The dummy target is intentionally empty because the training loop ignores it.

## Validation sequence

When you are unsure where the breakage comes from, validate in this order:

1. Run `scripts/validate_vxm_npz.py` on the file list.
2. Check the input shapes and key names against `references/data-formats.md`.
3. Pick the simplest generator that matches the target task.
4. Hand the resulting arrays to the model owner only after the generator output shape is clear.

## Stop conditions

Stop and fix the data instead of continuing when:

- the file list mixes incompatible spatial shapes,
- a supervised workflow has no discrete segmentation,
- label maps are not integer typed,
- a surface workflow has no usable boundary voxels,
- or you would need a download, a private dataset, or a long preprocessing run to recover the inputs.
