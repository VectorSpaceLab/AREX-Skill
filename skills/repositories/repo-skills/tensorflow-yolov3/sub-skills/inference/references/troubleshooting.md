# Inference troubleshooting

## Quick triage order

1. Run the bundled contract checker with explicit paths.
2. Confirm TensorFlow can import the PB and return the four expected tensors.
3. Confirm class count equals `num_classes` and prediction reshape uses `5 + num_classes`.
4. Confirm image/video frames are readable and have the expected color channel convention.
5. If inference runs but detections are empty, lower the score threshold temporarily and inspect prediction score ranges.

## PB exists, but CWD/config paths are wrong

Symptoms:

- `FileNotFoundError: ./data/classes/coco.names`
- import fails before the inference function is called;
- the PB file exists, but `core.utils` fails to import from a notebook, service process, or different working directory.

Cause:

- The utility module imports the config and reads the class file through `draw_bbox`'s default argument at import time.
- Defaults such as `./data/classes/coco.names` are relative to the current working directory, not to the utility file.

Fixes:

- Run from the directory that contains the expected `data/` layout.
- Pass explicit paths to `scripts/pb_inference_contract.py` to separate path problems from PB problems.
- In new code, load class names from an explicit path and pass the resulting dictionary to `draw_bbox(image, bboxes, classes=class_names)`.
- If modifying config values, do it before importing utilities that read class names at import time.
- For packaged applications, avoid relying on `./data/...`; resolve paths from an application config or environment variable.

## Missing or wrong PB tensor names

Symptoms:

- graph import fails with a requested return element not found;
- `input/input_data:0` is missing;
- one or more prediction tensors such as `pred_sbbox/concat_2:0` are missing.

Likely causes:

- The PB was frozen by a different YOLOv3 implementation.
- The graph was imported or exported with a name prefix.
- Output node names were changed during conversion/freezing.
- The file is not a TensorFlow frozen graph.

Fixes:

- Re-run the contract checker and inspect the reported missing tensor.
- If the graph is known to be compatible but has renamed tensors, pass all expected names with `--expected-tensors` and update the inference script consistently.
- If the PB came from another implementation, do not assume the postprocessing format is identical. Verify whether outputs are decoded boxes or raw feature maps.
- If the user only has a checkpoint, use the conversion workflow to freeze with the expected output node names.

## PB is present but detections are empty

Empty detections can be valid, but diagnose these causes before declaring the model unusable:

| Check | Why it matters | Action |
|---|---|---|
| Score threshold | Demo threshold `0.3` may be too high for a poor image, custom model, or class mismatch. | Temporarily test `0.05` or log max `objectness * class_prob`. |
| Class count | Reshaping with `85` when the graph was trained for another class count corrupts rows. | Set `num_classes` to the class-file count and confirm graph final dimension is `5 + num_classes`. |
| Class file | Wrong class order does not always make detections empty, but makes labels wrong and can hide expected classes. | Use the exact `.names` file used for training/freezing. |
| Anchors/config | Anchors are baked into graph construction; mismatch during training/conversion can produce poor boxes. | Verify the graph was built with the intended anchor file and input size. |
| Color channels | Accidental BGR/RGB double conversion can depress scores. | Compare one known image with the source demo behavior; avoid changing channel order without testing. |
| Input size | Feeding a different size than expected can fail or degrade outputs. | Use `416` unless the graph was designed for another size. |
| PB weights | A graph with random or wrong weights can import cleanly and output no useful boxes. | Confirm the PB came from trained COCO/custom checkpoint. |
| Image content | Some images genuinely contain no trained classes. | Test a simple image containing a known COCO object. |

Diagnostic snippet after session execution:

```python
flat = np.concatenate([
    np.reshape(pred_sbbox, (-1, 5 + num_classes)),
    np.reshape(pred_mbbox, (-1, 5 + num_classes)),
    np.reshape(pred_lbbox, (-1, 5 + num_classes)),
], axis=0)
objectness_max = float(np.max(flat[:, 4]))
class_prob_max = float(np.max(flat[:, 5:]))
combined_max = float(np.max(flat[:, 4:5] * flat[:, 5:]))
print(objectness_max, class_prob_max, combined_max)
```

If `combined_max` is below the score threshold, lower the threshold for diagnosis. If all values are near zero on obvious objects, suspect weights, classes, preprocessing, or graph mismatch.

## Image read and preprocessing failures

Symptoms:

- `cv2.imread(...)` returns `None`;
- `cv2.cvtColor` raises an assertion error;
- output boxes are shifted or scaled incorrectly.

Fixes:

- Check the image path and file permissions.
- Use Pillow or OpenCV to verify dimensions before inference.
- Keep `original_image_size = image.shape[:2]` before letterbox resizing.
- Pass `[input_size, input_size]`, not `(width, height)` from the original image.
- Ensure postprocessing receives the original `(height, width)` tuple.

## OpenCV/Pillow GUI problems

Symptoms:

- `Image.show()` silently does nothing;
- `cv2.imshow()` fails on a server or container;
- Qt/X11/display errors appear;
- the process hangs waiting for a window event.

Fixes:

- Save results to an image or video file instead of showing a GUI.
- Use `opencv-python-headless` in non-GUI environments.
- If a GUI is required, confirm `DISPLAY`/Wayland/X11 forwarding and OpenCV GUI backend support.
- Convert RGB arrays to BGR before `cv2.imwrite` or `cv2.VideoWriter`.

## Video and camera failures

Symptoms:

- `ValueError("No image!")` at the end of a video;
- `VideoCapture` opens but returns no frames;
- camera index `0` does not work;
- saved video has wrong colors.

Fixes:

- Treat `return_value == False` as normal EOF for file videos.
- Check `vid.isOpened()` before entering the loop.
- For camera input, try another index and confirm device permissions.
- Always release `VideoCapture` and `VideoWriter`.
- Convert RGB/BGR consistently before display or saving.

## TensorFlow version and protobuf issues

Symptoms:

- `AttributeError` for `tf.Session`, `tf.GraphDef`, or `tf.gfile`;
- protobuf descriptor errors during TensorFlow import;
- graph import works in one environment and fails in another.

Fixes:

- Prefer a TensorFlow 1.x-compatible environment for this repository.
- In TensorFlow 2.x, use `tf.compat.v1` APIs and disable eager behavior in execution scripts.
- If TensorFlow 1.x fails with protobuf descriptor errors, pin protobuf to a TensorFlow-compatible 3.x release.
- The bundled contract checker uses compatibility fallbacks for graph import, but actual inference scripts still need a working TF graph/session runtime.

## Class and anchor file problems

Symptoms:

- class index out of range during drawing;
- labels are incorrect;
- the contract checker reports an anchor count other than 18;
- NMS succeeds but boxes appear nonsensical.

Fixes:

- Ensure the class file has exactly one non-empty class name per line.
- Keep class order identical to training.
- Ensure the anchor file has 18 comma-separated positive numbers: three scales, three anchors per scale, width/height per anchor.
- Do not silently mix COCO class names with a custom-trained PB.

## NMS and Soft-NMS surprises

Symptoms:

- too many overlapping boxes remain;
- expected boxes disappear;
- `method` assertion fails.

Fixes:

- Use only `method="nms"` or `method="soft-nms"`.
- Increase IoU threshold to keep more overlapping boxes; decrease it to suppress more.
- Soft-NMS decays scores instead of hard-removing all overlaps, but low final scores can still be filtered out.
- Confirm NMS receives rows in `[xmin, ymin, xmax, ymax, score, class]` format, not raw prediction rows.
