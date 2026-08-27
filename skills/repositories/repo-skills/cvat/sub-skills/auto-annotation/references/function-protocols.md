# CVAT auto-annotation function protocols

CVAT supports several auto-annotation modes through `cvat_sdk.auto_annotation` and the `cvat-cli` task/function commands.

## Immediate annotation

Use `annotate_task(client, task_id, function, ...)` when the function runs locally and the user wants annotations applied to an existing task immediately.

Common options:

- `clear_existing`: remove annotations already present on the task.
- `allow_unmatched_labels`: ignore labels the function knows about but the task does not.
- `conf_threshold`: filter detections by confidence.
- `conv_mask_to_poly`: convert mask shapes to polygons where supported.

## Detection functions

Confirmed pieces:

- `DetectionFunctionSpec(labels=[...])`
- `DetectionFunctionContext` with `frame_name`, `conf_threshold`, and `conv_mask_to_poly`
- `DetectionFunction` protocol with `spec` and `detect`
- Helper factories for specs and annotations:
  - `label_spec`
  - `skeleton_label_spec`
  - `keypoint_spec`
  - `attribute_spec`
  - `checkbox_attribute_spec`
  - `number_attribute_spec`
  - `radio_attribute_spec`
  - `select_attribute_spec`
  - `text_attribute_spec`
  - `tag`
  - `shape`
  - `mask`
  - `polygon`
  - `rectangle`
  - `skeleton`
  - `keypoint`

Constraints to remember:

- Labels, sublabels, and attributes must have unique ids within their scope.
- Detection outputs must not set `id` or `source`.
- `frame_id` on output shapes must be `0`.
- Labels and attributes are matched by name against the CVAT task labels.

## Interaction functions

Interaction functions are prompt-driven and can be used in native AI tools/UI flows.

Key facts:

- `InteractionFunctionSpec` declares `min_pos_points`, optional `min_neg_points`, and optional `min_bounding_boxes`.
- `InteractionFunctionContext` is currently empty but exists for future use.
- `InteractionResultShape` objects currently matter most when `type == "mask"`.
- `InteractionResultAttributes.CONFIDENCE` is the supported result attribute spec id.
- `preprocess_image` is optional and can be cached across repeated `detect` calls.

## Tracking functions

Tracking functions support shape propagation through a video.

Key facts:

- `TrackingFunctionSpec.supported_shape_types` must contain valid CVAT shape types.
- `TrackingFunctionContext` is empty.
- `TrackingFunctionShapeContext.original_shape_type` identifies the shape being tracked.
- `TrackableShape` and `Track` return values represent tracking state and predictions.
- `preprocess_image` is optional here as well.

## CLI and native-function mapping

| User need | CLI/API | What it does |
|---|---|---|
| Annotate a task locally | `task auto-annotate` / `annotate_task` | Runs the function against an existing task. |
| Register a reusable server-side function | `function create-native` | Creates a native function resource in CVAT. |
| Run a background agent | `function run-agent` | Polls CVAT and executes requests for the native function. |

## Practical label-matching advice

- Keep the function's label names close to the task/project label names.
- Use the same attribute names and values when you want CVAT to remap ids cleanly.
- If the function should not return some labels for a given task, enable `allow_unmatched_labels` and document the omission.
- For ROI-style annotation, the CVAT UI may crop the image before sending it to the model; the function still returns shapes in full-frame coordinates.
