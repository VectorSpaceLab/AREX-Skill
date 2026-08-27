# Image utilities troubleshooting

Use this guide for failures owned by the image utilities sub-skill: optional image dependencies, package data lookup, array/data-format mismatches, image loading, text drawing, and graph refresh after model edits.

## Quick diagnostic

Run the bundled synthetic diagnostic first when the environment is uncertain:

```bash
python scripts/check_image_utilities.py
```

Default behavior should pass without Pillow or imageio; it reports those packages as optional. Add `--require-optional` only when the requested task explicitly needs `draw_text` or GIF generation.

## Failure modes

| Symptom | Likely cause | Resolution |
|---|---|---|
| `ImportError: Failed to import PIL. You must install Pillow` | `draw_text` needs Pillow, and `GifGenerator.callback` also uses `draw_text` for frame labels. | Install Pillow or install the package's optional `vis_utils` extra. If GIF generation is requested, ensure imageio is installed too. |
| `ImportError: Failed to import imageio. You must install imageio` | `GifGenerator` writer construction needs imageio. | Install imageio or the `vis_utils` extra. Pillow may still be required later for text overlay on frames. |
| Font warning followed by text drawn in a different style | Requested font file, such as `FreeSans.ttf`, was not found among system fonts. | This is non-fatal. Use an installed font name or accept Pillow's default font fallback. |
| `ValueError: alpha needs to be between [0, 1]` | `overlay` received an alpha outside the valid closed interval. | Clamp or validate alpha before calling. Use `alpha=0` for the second array only and `alpha=1` for the first array only. |
| `ValueError: array1 and array2 must have the same shapes` | The heatmap/display image arrays were not resized, colorized, or batched consistently before blending. | Convert both arrays to identical HWC or identical tensor shapes before `overlay`; route heatmap resizing/semantic choices to the visualization workflow. |
| `bgr2rgb` appears to flip width instead of color | Input is channels-first, but `bgr2rgb` reverses the last axis. | Use `array[:, ::-1, ...]` for batched channels-first tensors or convert to HWC before `bgr2rgb`. |
| `stitch_images` raises unpacking/broadcast errors | Images are not 3D HWC arrays of identical shape, or the list contains grayscale 2D images. | Convert grayscale to 3-channel display arrays or add a channel dimension consistently; resize all images before stitching. |
| `lookup_imagenet_labels` raises `KeyError` | Index is outside 0-999 or does not match standard ImageNet output ordering. | Validate model output dimension and class-index convention. For custom classifiers, use a task-specific label map. |
| `lookup_imagenet_labels` cannot open label JSON | keras-vis was installed without package data. | Reinstall from a complete package source or wheel that includes `resources/imagenet_class_index.json`; avoid partial source copies for runtime. |
| Older snippets mention a singular ImageNet label helper that is unavailable | Some examples use stale names, while keras-vis 0.5.0 exposes `lookup_imagenet_labels`. | Use `utils.lookup_imagenet_labels(index_or_indices)` and remember it returns a list. |
| `find_layer_idx` raises `No layer with name ...` | Layer names are exact strings and may differ after model construction, nesting, or repeated layer instances. | Inspect `[layer.name for layer in model.layers]`, choose the exact name, then pass it to `find_layer_idx`. |
| Edited `layer.activation` has no effect | Keras 2.x graph tensors were already built before the attribute edit. | Assign the return value of `utils.apply_modifications(model, custom_objects=...)` before visualizing. |
| `apply_modifications` fails while saving/loading | The model is not serializable through legacy HDF5, HDF5 support is unavailable, or custom objects were omitted. | Provide `custom_objects`, remove unserializable lambdas where possible, or rebuild the model architecture manually with the desired activation. |
| `normalize` output contains NaN/Inf | Input contains NaN/Inf, or downstream code expected special handling for invalid values. | Clean or mask invalid values before normalization. Constant finite arrays map to `min_value`. |
| Data-format checks work in isolation but fail in a later model call | Code changed global `K.image_data_format()` and did not restore it. | Save the old format and restore it in a `finally` block around diagnostics. |
| `load_img` resizing has swapped dimensions or unexpected dtype | `load_img` passes `target_size` directly to scikit-image resize and casts resized output to `uint8`. | Treat `target_size` as scikit-image output shape, verify row/column order, and normalize/cast explicitly after loading if the model expects another range. |
| `load_img(..., grayscale=True)` fails on newer scikit-image | The legacy wrapper uses the older positional grayscale argument. | Use an environment compatible with keras-vis 0.5.0, or load/convert the image yourself and pass the resulting array to keras-vis workflows. |

## Optional dependency decision tree

1. Only blending arrays with `overlay`, normalizing arrays, using `slicer`, or looking up labels: Pillow and imageio are not required.
2. Drawing labels on images with `draw_text`: Pillow is required.
3. Generating optimization GIFs with `GifGenerator`: imageio is required to open the writer; Pillow is also required when frames are annotated.
4. Loading static images with `load_img`: scikit-image is required by the base package dependency set; Pillow may still be involved indirectly for some image plugins, depending on the file type.

## Data-format mismatch checklist

- Confirm whether the object is a model tensor/batch or a display image.
- For model tensors, use the active Keras `image_data_format` and `get_img_shape` for reporting.
- For display utilities (`draw_text`, `stitch_images`, most RGB/BGR handling), convert to HWC.
- For `overlay`, make both arrays exactly the same shape before blending; decide heatmap semantics elsewhere.
- For `slicer`, author slices in canonical `(samples, channels, spatial...)` order and include the sample axis.

## Graph-refresh checklist after activation edits

1. Find the exact output layer with `utils.find_layer_idx(model, layer_name)`.
2. Modify the layer attribute, such as replacing a final `softmax` activation with a linear activation for visualization.
3. Call `model = utils.apply_modifications(model, custom_objects=...)` and use the returned model.
4. Recompute `layer_idx` if the model was rebuilt and later code stores layer objects or indices separately.
5. If serialization fails, use a manually rebuilt model rather than assuming the attribute edit was applied.
