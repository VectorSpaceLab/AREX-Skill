---
name: auto-annotation
description: "Implement CVAT local auto-annotation functions and reason about
  serverless native-function deployment, label matching, ROI, and tracking
  flows."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# CVAT auto-annotation

Use this sub-skill when the user needs to automate annotation with a Python function or a CVAT native function: build detection/interaction/tracking/re-identification logic, run `annotate_task`, create native functions, run agents, or understand the CPU/GPU serverless deployment story for built-in Nuclio models.

## Route first

- Read `references/function-protocols.md` for the confirmed AA function protocols, helper factories, prompt/result constraints, and CLI/API mappings.
- Read `references/serverless-models.md` for CPU/GPU serverless deployment patterns, model categories, and deployment hazards.
- Read `references/troubleshooting.md` for label mapping, shape validation, backend, import, and deployment errors.
- Use `scripts/aa_detection_template.py` for a safe starter implementation and `scripts/cvat_serverless_deploy_notes.py` for a non-executing command checklist.

## Choose the right mode

- **Immediate mode**: call `cvat_sdk.auto_annotation.annotate_task(client, task_id, function, ...)` from Python or use `cvat-cli task auto-annotate`.
- **Native function mode**: create a server-side function with `cvat-cli function create-native` and run an agent process with `cvat-cli function run-agent`.
- **Serverless deployment mode**: deploy built-in CVAT Nuclio functions when the user wants reusable server-side detectors/interactors.

If the task is primarily general SDK scripting, route to `../sdk-automation/SKILL.md`. If it is primarily task/project shell automation, route to `../cli-automation/SKILL.md`.

## Protocols at a glance

### Detection functions

Implement `spec` and `detect`.

- `spec` returns a `DetectionFunctionSpec` with label definitions.
- `detect(context, image)` returns a sequence of tags/shapes.
- Helper factories such as `label_spec`, `skeleton_label_spec`, `keypoint_spec`, `attribute_spec`, `rectangle`, `mask`, `polygon`, `skeleton`, `keypoint`, and `tag` make valid objects easier to construct.
- `frame_id` must be 0 and `id`/`source` must not be set in returned annotations.

### Interaction functions

Implement `spec`, `detect`, and optionally `preprocess_image`.

- `spec` is an `InteractionFunctionSpec` with minimum positive points and optional negative points/bounding boxes.
- `detect(context, pp_image, prompts)` returns `InteractionResultShape` objects.
- CVAT UI currently only processes returned shapes of type `mask`.
- `InteractionResultAttributes.CONFIDENCE` is the only supported result attribute spec id.

### Tracking functions

Implement `spec`, `init_tracking_state`, `track`, and optionally `preprocess_image`.

- `spec.supported_shape_types` declares the trackable shapes.
- `init_tracking_state` analyzes the first image and shape.
- `track` predicts a later position or returns `None` when tracking fails.

## CLI and API entry points

- `task auto-annotate` uses a local function module or source file and can clear existing annotations, allow unmatched labels, set a confidence threshold, and convert masks to polygons.
- `function create-native` registers a local function implementation with the server.
- `function run-agent` polls the server for requests and executes them against the local function.

## Safety defaults

- Keep model loading local and deterministic; avoid hidden downloads in the function path unless the user explicitly wants them.
- Put heavyweight model weights, checkpoints, or Nuclio build contexts outside the runtime skill and describe them as deployment inputs.
- Require the operator to match labels and shapes before running automatic annotation on real data.
- For GPU serverless functions, treat driver/runtime compatibility as a hard prerequisite and do not imply CPU validation covers GPU execution.
