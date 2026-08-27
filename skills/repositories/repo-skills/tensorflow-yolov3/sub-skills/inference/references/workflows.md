# Frozen PB inference workflows

This reference covers image, video, and camera inference with a frozen TensorFlow graph. It assumes the user already has a compatible `.pb`; if they only have Darknet weights or checkpoints, use the conversion workflow first.

## 1. Prerequisite contract check

From the working directory that contains the PB/media/data paths, run the bundled checker by path:

```bash
python sub-skills/inference/scripts/pb_inference_contract.py \
  --pb ./yolov3_coco.pb \
  --image ./docs/images/road.jpeg \
  --classes ./data/classes/coco.names \
  --anchors ./data/anchors/basline_anchors.txt \
  --input-size 416 \
  --num-classes 80
```

If the sub-skill has been exported elsewhere, replace the script path with that exported location.

The checker does **not** run inference. It confirms:

- the PB, image, class-name file, and anchor file exist and are non-empty;
- the class file contains `num_classes` non-empty names;
- the anchor file has 18 numeric values, reshaped as `(3, 3, 2)`;
- TensorFlow can import the frozen graph and return the expected tensors:
  - `input/input_data:0`
  - `pred_sbbox/concat_2:0`
  - `pred_mbbox/concat_2:0`
  - `pred_lbbox/concat_2:0`

For a custom model, change `--num-classes`, `--classes`, and, if the graph was frozen with different node names, `--expected-tensors`.

## 2. Image inference workflow

Default image workflow values:

| Field | Default |
|---|---|
| PB file | `./yolov3_coco.pb` |
| Image file | `./docs/images/road.jpeg` |
| Input size | `416` |
| Number of classes | `80` |
| Score threshold | `0.3` |
| NMS IoU threshold | `0.45` |
| Class names | `./data/classes/coco.names` |

Operational steps:

1. Load the frozen graph with return elements:

   ```python
   return_elements = [
       "input/input_data:0",
       "pred_sbbox/concat_2:0",
       "pred_mbbox/concat_2:0",
       "pred_lbbox/concat_2:0",
   ]
   return_tensors = utils.read_pb_return_tensors(graph, pb_file, return_elements)
   ```

2. Read the image with OpenCV and record `original_image_size = image.shape[:2]` as `(height, width)`.
3. Resize with letterbox padding to `[input_size, input_size]`, normalize to `[0, 1]`, and add a batch dimension so the feed value is shaped like `[1, 416, 416, 3]`.
4. Run only the three output tensors:

   ```python
   pred_sbbox, pred_mbbox, pred_lbbox = sess.run(
       [return_tensors[1], return_tensors[2], return_tensors[3]],
       feed_dict={return_tensors[0]: image_data},
   )
   ```

5. Concatenate scale outputs:

   ```python
   pred_bbox = np.concatenate([
       np.reshape(pred_sbbox, (-1, 5 + num_classes)),
       np.reshape(pred_mbbox, (-1, 5 + num_classes)),
       np.reshape(pred_lbbox, (-1, 5 + num_classes)),
   ], axis=0)
   ```

6. Postprocess and NMS:

   ```python
   bboxes = utils.postprocess_boxes(pred_bbox, original_image_size, input_size, 0.3)
   bboxes = utils.nms(bboxes, 0.45, method="nms")
   ```

7. Each returned row is `[xmin, ymin, xmax, ymax, score, class]` in original image coordinates. Cast `class` to `int` before indexing class names.
8. For an interactive desktop, draw boxes and show the image. For servers, notebooks, CI, or SSH sessions, save the result instead of using `Image.show()`.

### Headless-safe image output

Avoid GUI calls when no display is available:

```python
image = utils.draw_bbox(original_image, bboxes, classes=class_names)
Image.fromarray(image).save("detections.jpg")
```

If using OpenCV to save an RGB array, convert back to BGR first:

```python
cv2.imwrite("detections.jpg", cv2.cvtColor(image, cv2.COLOR_RGB2BGR))
```

## 3. Video-file workflow

Default video workflow values:

| Field | Default |
|---|---|
| PB file | `./yolov3_coco.pb` |
| Video file | `./docs/images/road.mp4` |
| Input size | `416` |
| Number of classes | `80` |
| GUI window | OpenCV window named `result` |
| Quit key | `q` |

Operational steps:

1. Run the PB contract check once before opening the video.
2. Open the source with `cv2.VideoCapture(video_path)`.
3. For each frame, perform the same preprocessing, session run, postprocessing, and NMS as image inference.
4. Record elapsed inference time per frame if useful.
5. Draw boxes on the RGB frame.
6. Either show it with OpenCV or write frames to `cv2.VideoWriter`.

Production adaptation points:

- Check `vid.isOpened()` before the loop.
- Treat `return_value == False` as normal end-of-file for video files, not necessarily an exception.
- Release `VideoCapture` and any `VideoWriter` in `finally` blocks.
- Use `cv2.destroyAllWindows()` only when a GUI window was opened.
- On a headless machine, avoid `cv2.namedWindow()` and `cv2.imshow()`; write an output video instead.

## 4. Camera workflow

The source video workflow switches to camera input by using `video_path = 0`. When adapting it:

- Confirm the camera index (`0`, `1`, etc.) exists and the process has permission to read it.
- Camera frames may have variable resolution; always recompute `frame_size = frame.shape[:2]` per frame.
- If the camera stream drops a frame, decide whether to continue, retry, or exit; do not throw an unhandled `ValueError("No image!")` in a long-running application.
- Camera display still requires a GUI stack unless saving or streaming frames elsewhere.

## 5. Working outside the repository root

The original helpers use relative config defaults such as `./data/classes/coco.names`. If a user has a PB but runs from another current working directory, common failures occur before inference. Safer options are:

- run from the directory that contains the expected `data/` and `docs/` layout;
- pass explicit PB/media/classes/anchors paths to the bundled contract checker;
- when writing a new inference script, load class names from an explicit path and pass the resulting dictionary to `draw_bbox` instead of relying on the import-time default;
- if reusing the original config module, update the config paths before importing utilities that read them at import time.

## 6. Expected detections and serialization

A robust downstream interface should serialize detections as dictionaries or rows derived from:

```text
xmin ymin xmax ymax score class_id class_name
```

Rules:

- Coordinates are clipped to the original image bounds.
- `score` is `objectness * best_class_probability` after thresholding.
- `class_id` is numeric and should index the selected class-name file.
- Empty detections are valid output; diagnose them with the checklist in [Troubleshooting](troubleshooting.md) before assuming the PB is broken.
