---
name: inference
description: "Guides agents through tensorflow-yolov3 frozen .pb image and video
  inference, tensor contract checks, preprocessing, postprocessing, NMS, and
  empty-detection troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# tensorflow-yolov3 inference sub-skill

Use this sub-skill when the user wants to run, adapt, debug, or explain **frozen `.pb` image/video inference** for this TensorFlow 1.x YOLOv3 implementation. Trigger phrases include image demo, video demo, camera inference, frozen graph, `yolov3_coco.pb`, PB tensor names, preprocessing, postprocessing, NMS, empty detections, and bounding-box output format.

Do not use this sub-skill to create the PB or checkpoint files; route checkpoint conversion and graph freezing to the conversion skill. Do not use it for long training or mAP evaluation, except to explain the inference outputs that feed later evaluation.

## Operating contract

The original demo workflow uses these defaults:

- Frozen graph: `./yolov3_coco.pb`
- Image demo media: `./docs/images/road.jpeg`
- Video demo media: `./docs/images/road.mp4`; camera mode is selected by using video path `0`
- Classes: `./data/classes/coco.names`
- Anchors/config default: `./data/anchors/basline_anchors.txt`
- `input_size = 416`
- `num_classes = 80`
- Score threshold: `0.3`
- NMS IoU threshold: `0.45`
- Required frozen-graph return tensors:
  - `input/input_data:0`
  - `pred_sbbox/concat_2:0`
  - `pred_mbbox/concat_2:0`
  - `pred_lbbox/concat_2:0`
- Postprocessed detection rows are `[xmin, ymin, xmax, ymax, score, class]` in original image coordinates.

Before writing or running an inference script, check the contract safely without model execution. From the working directory that contains the PB/media/data paths, run the bundled checker by path:

```bash
python sub-skills/inference/scripts/pb_inference_contract.py \
  --pb ./yolov3_coco.pb \
  --image ./docs/images/road.jpeg \
  --classes ./data/classes/coco.names \
  --anchors ./data/anchors/basline_anchors.txt \
  --input-size 416 \
  --num-classes 80
```

If the sub-skill has been exported elsewhere, replace the script path with that exported location. The checker validates paths, class count, anchor shape, and PB tensor names without running a TensorFlow session.

## Standard workflow

1. Confirm the user has a frozen PB whose tensor names match the contract above. If the PB is missing, use conversion guidance instead of pretending inference can run.
2. Confirm the image or video path is readable, and decide whether output should be shown in a GUI window or saved to a file for headless environments.
3. Load the frozen graph and request the four return tensors above.
4. Read the image/frame, preserve its original `(height, width)`, letterbox-resize to `[416, 416]`, normalize to `[0, 1]`, and add a batch dimension.
5. Run the session for the three prediction tensors.
6. Reshape each prediction to `(-1, 5 + num_classes)`, concatenate all scales, run postprocessing at score threshold `0.3`, and run class-wise NMS at IoU threshold `0.45`.
7. Treat the final detections as `[xmin, ymin, xmax, ymax, score, class]`. Convert `class` to `int` before indexing class names.
8. Draw or serialize results. In headless systems, save images/video frames instead of calling `Image.show()` or `cv2.imshow()`.

## Bundled references

- [Workflows](references/workflows.md): image, video, camera, and headless adaptations.
- [API reference](references/api-reference.md): tensor contract, helper function behavior, and detection formats.
- [Troubleshooting](references/troubleshooting.md): missing files, wrong CWD/config paths, empty detections, GUI/video problems, and TensorFlow compatibility.

## Inference caveats to surface early

- `core.utils` reads the class file during import through the default argument of `draw_bbox`; importing it outside a working directory where `./data/classes/coco.names` exists can fail before inference starts.
- The demo scripts use TensorFlow 1.x graph/session APIs. TensorFlow 2.x environments need compatibility mode or a TF1 environment.
- The video demo opens an OpenCV GUI window and raises an error on end-of-file; production code should handle EOF cleanly and save outputs when no display is available.
- The source preprocessing helper is named `image_preporcess` and performs a BGR-to-RGB conversion internally; avoid accidental double channel swaps when refactoring.
