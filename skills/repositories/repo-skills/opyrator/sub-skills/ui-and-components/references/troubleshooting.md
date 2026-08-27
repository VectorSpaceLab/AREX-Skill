# Troubleshooting

Use this guide when the Streamlit UI, schema classification, FileContent handling, or component renderers fail.

## Streamlit or protobuf import fails

### Symptoms

- Importing `opyrator.ui.streamlit_ui` raises a `ModuleNotFoundError`, `ImportError`, or protobuf descriptor error.
- The UI works in one environment but fails in another with a Streamlit import traceback before any widgets appear.
- Streamlit complains about session-state internals such as `ReportThread`, `ReportSession`, or `server.server`.

### Likely causes

- A newer Streamlit/protobuf combination is incompatible with this Opyrator snapshot.
- The environment is missing the older compatibility pins required by Streamlit 0.72-era internals.
- The installed Streamlit package exposes a different session-state module layout than the fallback imports expect.

### Recovery steps

1. Confirm the UI import failure happens before any user code runs.
2. Reinstall the legacy-compatible UI stack for this package snapshot:
   - `streamlit==0.72.0`
   - `protobuf==3.20.3`
   - `fastapi==0.63.0`
   - `starlette==0.13.6`
3. From the sub-skill directory, re-run the safe smoke helper:

```bash
python scripts/schema_smoke.py --json
```

4. If the helper still fails on import, inspect the active Python environment before changing the callable itself.

### Escalation

If the broader repository uses a different package version, route version-pin policy questions to the [root troubleshooting guide](../../../references/troubleshooting.md).

## Unsupported property shapes in schema_utils

### Symptoms

- The UI shows `The type of the following property is currently not supported`.
- A field disappears from the UI or falls into the unsupported branch.
- A nested model with `anyOf`, `oneOf`, unusual arrays, or non-byte file shapes does not render.

### Likely causes

- The schema shape is outside the narrow predicate set in `opyrator.ui.schema_utils`.
- The field is not expressed as one of the supported primitives, enums, refs, dicts, object lists, or byte-formatted files.
- The model uses a JSON Schema feature that the renderer does not understand.

### Recovery steps

1. Check the schema with the safe smoke helper or a direct `schema()` call.
2. Rewrite the field into one of the supported shapes if the default UI is desired.
3. If the field must stay custom, add `render_input_ui` or `render_output_ui` on the model instead of forcing the predicate set to grow.
4. For design review, consult [component reference](component-reference.md#predicates-and-edge-cases).

## FileContent media handling looks wrong

### Symptoms

- Uploaded files preview as plain bytes instead of image/audio/video media.
- Output files do not download with a sensible name.
- `as_bytes()` or `as_str()` raises during conversion.

### Likely causes

- The field is missing a `mime_type` hint.
- The MIME type is not one of the supported media preview families.
- The payload is not valid base64 before calling `as_bytes()`.
- `as_str()` is used on binary content instead of UTF-8 text.

### Recovery steps

1. Add `mime_type` to the `Field(...)` metadata for file fields.
2. Use one of the supported preview families when a media preview is required.
3. Validate the base64 string with `FileContent.validate(...)` or by round-tripping through `as_bytes()`.
4. Use `as_bytes()` for binary content and reserve `as_str()` for text content.

## Custom output renderer is ignored or falls back

### Symptoms

- A model's `render_output_ui` does not seem to run.
- The UI falls back to JSON or the automatic model renderer.
- A custom renderer works for some outputs but not for nested output objects.

### Likely causes

- The method name is not exactly `render_output_ui`.
- The top-level output object is not a Pydantic model instance.
- The renderer raises an exception and Opyrator falls back to the automatic renderer.
- A nested object has its own renderer and is called directly by the parent renderer.
- The renderer expects the input object but its parameter is not named `input`.

### Recovery steps

1. Verify the method exists on the model instance, not just on the class definition.
2. If the renderer needs the original input, name that parameter `input`.
3. Keep the custom renderer small and deterministic; move expensive work into the callable itself.
4. Check the logs for the fallback message:
   - `Failed to execute custom render_output_ui function. Using auto-generation instead`
5. If you intentionally want fallback behavior, let the custom renderer raise and rely on the default renderer only for safe shapes.

## Custom input renderer does not preserve values

### Symptoms

- Widgets reset unexpectedly when the UI reruns.
- Custom fields do not carry previous input forward.
- The Execute button validates an empty object even though widgets were filled in.

### Likely causes

- The custom `render_input_ui` hook ignores the passed `input_data` snapshot.
- Widget keys are unstable or collide with generated keys.
- The hook returns a plain dict instead of an input model instance.

### Recovery steps

1. Use the passed input snapshot as the source for defaults.
2. Return a model instance of the input type.
3. Keep widget keys stable and unique, especially inside repeated reruns.
4. If custom behavior is not needed, remove the hook and let schema-derived widgets handle the model.

## Optional example dependencies are missing

### Symptoms

- Example app imports fail even though the core package imports succeed.
- Example-specific models fail because external libraries are unavailable.

### Likely causes

- The repo's demo requirements were not installed.
- Heavy example packages depend on large model downloads or system tools.

### Recovery steps

Use the example-specific dependency set before blaming the UI layer:

- Named entity recognition: `spacy`, the `en_core_web_sm` model, and `st-annotated-text`
- Image super-resolution: `ISR`
- Audio separation: `spleeter` and `ffmpeg`
- Language detection: `fasttext`

If the core UI still fails after optional example dependencies are excluded, treat it as a package/UI issue rather than a demo dependency issue.
