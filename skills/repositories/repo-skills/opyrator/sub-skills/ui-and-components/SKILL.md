---
name: ui-and-components
description: "Launch and reason about Opyrator's Streamlit UI, schema-driven
  widgets, FileContent values, reusable output components, and custom UI hooks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# UI and Components

Use this sub-skill when the user asks how Opyrator renders an interactive Streamlit UI, how Pydantic schemas become widgets, how `FileContent` values move through uploads/downloads, or how to add custom input/output renderers.

## Route here for

- Launching or embedding the Streamlit UI with `launch_ui(opyrator_path, port=8501)` or `render_streamlit_ui(Opyrator(...))`.
- Predicting which Pydantic field shapes become text inputs, sliders, file uploaders, enums, dict editors, nested-object sections, or list editors.
- Designing schema-only UI behavior with `Field(...)` metadata such as `title`, `description`, `default`, `example`, ranges, `max_length`, `mime_type`, and enum types.
- Handling `opyrator.components.types.FileContent`, including upload validation, base64 round-tripping, `as_bytes()`, `as_str()`, and media previews/downloads.
- Using reusable component outputs such as `ClassificationOutput` and `ScoredLabel`.
- Adding `render_input_ui(streamlit, input_data)` on an input model or `render_output_ui(streamlit[, input=...])` on output models.
- Troubleshooting Streamlit/protobuf compatibility, old Streamlit session-state imports, unsupported schema shapes, file media handling, and missing optional demo dependencies.

## Do not handle here

- Function compatibility, callable import strings, CLI `call`, `export`, `deploy`, or general command routing: use [wrapping-and-cli](../wrapping-and-cli/SKILL.md).
- FastAPI app creation, OpenAPI service behavior, request/response endpoint structure, or OpenAPI schema patching: use [api-services](../api-services/SKILL.md).
- Root-level package installation and version pinning decisions that affect all workflows: start at the [root skill router](../../SKILL.md) and the [root troubleshooting guide](../../references/troubleshooting.md).

## Operating workflow

1. Confirm that the callable already satisfies Opyrator's shared callable contract: one parameter named `input` typed as a Pydantic `BaseModel`, and a Pydantic `BaseModel` or list of models as return type. For the shared contract and API consequences, route through [api-services](../api-services/SKILL.md).
2. For UI launch choices, use [workflows](references/workflows.md#launch-or-embed-the-streamlit-ui). Prefer `opyrator launch-ui module:function --port 8051` for an interactive server, or `render_streamlit_ui(Opyrator(...))` only inside a Streamlit script.
3. For schema-to-widget mapping, use [component reference](references/component-reference.md#input-widget-classification). Check the predicate order before changing a Pydantic field shape.
4. For files and media outputs, use [FileContent workflows](references/workflows.md#handle-filecontent-inputs-and-outputs) and the [FileContent reference](references/component-reference.md#filecontent-and-media-fields).
5. For custom renderers, use [custom UI hook workflows](references/workflows.md#add-custom-input-or-output-renderers). Keep fallback behavior explicit for output renderers that may fail.
6. If UI import, launch, schema classification, or media rendering fails, use [troubleshooting](references/troubleshooting.md) before modifying the callable.

## Bundled helper

- [`scripts/schema_smoke.py`](scripts/schema_smoke.py): safe deterministic smoke helper that builds a showcase-style Pydantic model, classifies its schema with `opyrator.ui.schema_utils`, verifies `FileContent` round-tripping, and checks custom renderer discovery without launching Streamlit or opening a browser.

Run it from this sub-skill directory in an environment where Opyrator is installed:

```bash
python scripts/schema_smoke.py --json
```

Expected success signal: exit code `0`, `status: "ok"`, all expected field classifications present, `file_round_trip.round_trip_bytes_match: true`, and the hook summary matches the expected hook summary.
