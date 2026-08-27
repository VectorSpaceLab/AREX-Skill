# Component Reference

This reference is the compact field-to-widget and component-to-renderer map for the UI sub-skill.

## Public entry points

| Item | Kind | Purpose |
| --- | --- | --- |
| `launch_ui(opyrator_path: str, port: int = 8501) -> None` | function | Starts a Streamlit server for an Opyrator path or import string. |
| `render_streamlit_ui(opyrator: Opyrator) -> None` | function | Renders the auto-generated Streamlit app inside a running Streamlit session. |
| `InputUI(session_state, input_class)` | class | Builds schema-driven input widgets and stores values in session state. |
| `OutputUI(output_data, input_data)` | class | Renders output objects, lists, and custom output hooks. |
| `FileContent` | component type | Base64-backed file payload for inputs and outputs. |
| `ScoredLabel` | component type | Single label/score pair for reusable classification output. |
| `ClassificationOutput` | component type | Reusable list output with Plotly bar chart rendering. |

## Input widget classification

`InputUI._render_property(...)` checks predicates in this order:

1. `is_single_enum_property`
2. `is_multi_enum_property`
3. `is_single_file_property`
4. `is_multi_file_property`
5. `is_single_datetime_property`
6. `is_single_boolean_property`
7. `is_single_dict_property`
8. `is_single_number_property`
9. `is_single_string_property`
10. `is_single_object`
11. `is_object_list_property`
12. `is_property_list`
13. `is_single_reference`
14. otherwise unsupported

### Predicate map

| Predicate | Schema shape | Widget / behavior |
| --- | --- | --- |
| `is_single_string_property` | `type: string` | `text_input` or `text_area` depending on `format`, `maxLength`, and `writeOnly`. |
| `is_single_datetime_property` | `type: string`, `format: date-time|date|time` | `date_input`, `time_input`, or split date/time inputs. |
| `is_single_boolean_property` | `type: boolean` | `checkbox`. |
| `is_single_number_property` | `type: integer|number` | `number_input` or `slider` when both bounds are present. |
| `is_single_file_property` | `type: string`, `format: byte` | `file_uploader` for one file. Returns raw bytes before Pydantic validation. |
| `is_multi_file_property` | `type: array`, items with `format: byte` | `file_uploader(..., accept_multiple_files=True)`. Returns a list of raw bytes. |
| `is_single_enum_property` | `$ref` or `allOf[0].$ref` resolving to enum | `selectbox`. |
| `is_multi_enum_property` | `type: array`, `uniqueItems: true`, item ref resolves to enum | `multiselect`. |
| `is_single_dict_property` | `type: object` with `additionalProperties` | Simple key/value editor. Numeric additional properties get number inputs. |
| `is_property_list` | `type: array` of primitive string/number/integer | Add/clear list editor. |
| `is_single_object` | `$ref` or `allOf[0].$ref` resolving to object with properties | Recursive nested object editor with subheaders. |
| `is_object_list_property` | `type: array` of object refs | Nested object editor plus add/clear list editor. |
| `is_single_reference` | bare `$ref` without explicit `type` | Recurses into the referenced schema. |

### Important widget rules

- Required fields are shown in the main page; optional fields are shown in the sidebar.
- Missing titles fall back to `name_to_title(field_name)`.
- `description` becomes widget help text for simple widgets and markdown for compound widgets.
- `default` usually seeds the widget value; `example` seeds single-line string widgets when no default is present.
- For string fields, `writeOnly: true` triggers password mode.
- For date-time fields, the UI renders a combined two-column date/time picker.
- Unsupported schema shapes raise an exception after showing a warning.

## FileContent and media fields

`FileContent` is a `str` subclass whose schema is advertised as `format: byte`.

### Validation and conversion

| Operation | Result |
| --- | --- |
| `FileContent.validate(bytes)` | Base64-encodes the bytes and returns a `FileContent` string. |
| `FileContent.validate(str)` | Wraps the string as `FileContent` without decoding it. |
| `FileContent.validate(bytearray|memoryview)` | Base64-encodes and returns `FileContent`. |
| `FileContent.as_bytes()` | Base64-decodes and returns raw bytes. |
| `FileContent.as_str()` | Decodes the bytes as UTF-8 text. |

### UI media behavior

| MIME type family | Input preview | Output preview |
| --- | --- | --- |
| `image/png`, `image/jpeg` | image preview | image preview |
| `audio/mpeg`, `audio/ogg`, `audio/wav` | audio player | audio player |
| `video/mp4` | video player | video player |
| other or missing MIME metadata | file picker only | base64 download link |

### Practical rule

Use `mime_type` on the `Field(...)` definition whenever a value should display as a media object instead of only as a download link.

## Output renderers

`OutputUI` walks the returned model or list and chooses the richest renderer available.

| Output shape | Renderer behavior |
| --- | --- |
| top-level `BaseModel` with `render_output_ui` | Call the custom renderer. If the renderer raises, log the exception and fall back to auto-generated rendering. |
| top-level list | Render each item; if the items are plain models, try a table via `pandas.DataFrame`; otherwise fall back to JSON. |
| nested `BaseModel` field | Recurse into that model and render its fields. |
| output field with its own `render_output_ui` | Call the nested renderer directly. |
| file field | Use media renderer or download link depending on `mime_type`. |
| primitive string/number/date/boolean | Show a titled text block. |
| enum | Show the enum value as text. |
| dict or other complex object | Show `streamlit.json(...)` or `jsonable_encoder(...)` output. |

## Reusable component types

### `ScoredLabel`

Fields:

- `label: str`
- `score: float`

Use it as the item type inside classification outputs or any ranked-label display.

### `ClassificationOutput`

- Root type: `List[ScoredLabel]`.
- Iteration and indexing proxy to the root list.
- `render_output_ui(streamlit)` sorts by score and renders a horizontal Plotly bar chart.
- When there are more than ten labels, it adds a slider to choose how many top labels to display.
- The renderer depends on Plotly, which is part of Opyrator's runtime dependency set.

## Predicates and edge cases

Supported schema utilities are intentionally narrow and explicit:

- `is_single_reference` only accepts bare `$ref` properties with no declared `type`.
- `is_property_list` only accepts arrays of primitive string, number, or integer items.
- `is_single_dict_property` only accepts objects with `additionalProperties`.
- `is_multi_enum_property` only accepts arrays marked `uniqueItems: true`.
- `is_single_file_property` and `is_multi_file_property` only recognize `format: byte`.
- `is_single_object` and `is_object_list_property` depend on `$ref` resolution.

Unsupported shapes to route to a custom renderer or a different sub-skill:

- unions such as `anyOf`, `oneOf`, or mixed-type lists
- arrays of booleans or other non-primitive non-file items
- objects without `additionalProperties` and without explicit properties
- binary formats that are not encoded as `byte`
- deeply custom nested editors that need richer semantics than the built-in widget set
