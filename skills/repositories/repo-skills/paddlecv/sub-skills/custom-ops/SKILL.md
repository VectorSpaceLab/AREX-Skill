---
name: "custom-ops"
description: "Use for PaddleCV custom operator registration, connector/output
  extension, and config DAG validation workflows."
metadata:
  disco-role: "operating"
disable-model-invocation: true
license: Apache 2.0
---

# Custom operators and DAG validation

Use this sub-skill when the user wants to add, modify, or debug a custom PaddleCV operator, connector, output, or graph configuration.

## Covers
- `ppcv.core.workspace.register`, `create`, and `get_global_op`
- `ppcv.ops.base.create_operators`
- `BaseOp`, `ModelBaseOp`, `ConnectorBaseOp`, and `OutputBaseOp`
- config graph validation with `Inputs` and `get_output_keys()`
- the bundled validator script `scripts/check_name.py`

## Excludes
- one-model inference routes handled by `single-model-inference`
- packaged OCR / PP-Structure / ShiTu / Human / Vehicle / TinyPose presets handled by `system-pipelines`
- training, dataset generation, or tutorial reproduction work

## Read these files
- `../../references/api-reference.md` for the registry and base-class contract.
- `../../references/task-catalog.md` for the unittest config families that exercise graph behavior.
- `../../references/workflows.md` for the operator-extension workflow.
- `../../references/troubleshooting.md` for registry, output-key, and graph-link errors.
- `scripts/check_name.py` for the bundled graph validator.

## Typical user requests
- "Add a new PaddleCV operator"
- "Why does my custom config graph fail to resolve an input key?"
- "How do I register a new connector or output op?"
- "Validate this unittest DAG config"

## Core workflow
1. Choose the correct base class: model, connector, or output.
2. Make the class name unique and decorate it with `@register`.
3. Ensure `get_output_keys()` matches the values returned by the op.
4. Align `Inputs` in the YAML with previous op output names.
5. Run `scripts/check_name.py --config ...` against the custom config.
6. Use the unittest config family to confirm the graph shape.

## What to pay attention to
- Model ops own preprocessing, predictor construction, and postprocess logic.
- Connector ops transform intermediate data between model ops.
- Output ops own rendering, saving, and final result shaping.
- `Inputs` links use `{last_op_name}.{last_op_output_name}` syntax.
- The first op in a graph usually reads `input.image` or another `input.*` key.

## Common extension families
- Crop / rotate / compose connectors
- Table matcher and OCR result reconciliation connectors
- Tracking connectors and output writers
- Custom detection, classification, or segmentation ops
- Specialized PP-Structure filters and result concatenation logic

## Common failure modes
- Duplicate registration names.
- Missing imports for the module that defines the custom class.
- Mismatch between declared output keys and returned dict keys.
- Incorrect `Inputs` ordering or output-name spelling.
- Missing optional dependencies for tracker, keypoint, or visualization helpers.

## When to hand off
If the request becomes a user-facing single-model or system preset question, switch to the owning sub-skill rather than continuing to patch the custom DAG here.
