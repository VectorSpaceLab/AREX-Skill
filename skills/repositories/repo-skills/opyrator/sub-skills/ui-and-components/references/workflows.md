# UI and Component Workflows

This reference gives task recipes for Opyrator's Streamlit UI layer and component models. It assumes the callable is already Opyrator-compatible; if the callable contract itself is unclear, route to [api-services](../../api-services/SKILL.md) for the shared Pydantic callable contract or [wrapping-and-cli](../../wrapping-and-cli/SKILL.md) for import-string and CLI routing.

## Launch or embed the Streamlit UI

### Launch from the CLI

Use this when the user wants a local browser UI for an importable callable:

```bash
opyrator launch-ui my_module:my_function --port 8051
```

Expected behavior:

- Opyrator creates a temporary Streamlit runner around `Opyrator("my_module:my_function")`.
- Streamlit is launched headlessly on the selected port.
- The command stays in the foreground until the Streamlit server exits.
- The function's docstring becomes page description text when available.

Validation signals:

- The terminal should show Streamlit's local URL and no import traceback.
- If the callable cannot be imported or does not satisfy the one-`input` Pydantic contract, stop UI work and route to [wrapping-and-cli](../../wrapping-and-cli/SKILL.md) or [api-services](../../api-services/SKILL.md).
- If import fails in `streamlit` or `protobuf`, use [troubleshooting](troubleshooting.md#streamlit-or-protobuf-import-fails) and the [root troubleshooting guide](../../../references/troubleshooting.md).

### Launch from Python

Use the function API when another Python entry point should start the same long-running UI server:

```python
from opyrator.ui.streamlit_ui import launch_ui

launch_ui("my_module:my_function", port=8051)
```

`launch_ui(opyrator_path: str, port: int = 8501) -> None` takes the same import string or supported Opyrator path accepted by the CLI. It writes a temporary Streamlit runner, starts `python -m streamlit run`, and deletes the temporary file after the subprocess returns.

### Embed in a Streamlit script

Use `render_streamlit_ui` only when the current process is already a Streamlit app:

```python
import streamlit as st
from opyrator import Opyrator
from opyrator.ui import render_streamlit_ui

st.set_page_config(page_title="Opyrator", page_icon=":arrow_forward:")
render_streamlit_ui(Opyrator("my_module:my_function"))
```

Expected behavior inside the Streamlit runtime:

1. A session state object stores `input_data`, `output_data`, `latest_operation_input`, and a `run_id` used to reset widget keys.
2. `InputUI(...).render_ui()` renders schema-derived widgets.
3. Pressing **Execute** parses the collected `input_data` as the callable's Pydantic input model and calls `opyrator(input=input_data_obj)`.
4. Validation errors are shown with `st.error(...)`.
5. Successful output is rendered by `OutputUI(...)`; a **Show JSON Output** button displays serialized output JSON.

Do not call `render_streamlit_ui` from a plain Python script and expect a UI; it expects Streamlit's runtime and session context. Use `launch_ui` or `streamlit run` for an interactive app.

## Design schema-driven inputs

Use Pydantic model fields to drive the UI. Start with the mapping in [component reference](component-reference.md#input-widget-classification), then apply these design rules:

- Required fields are rendered in the main page. Optional/defaulted fields are rendered in the sidebar.
- `Field(description="...")` becomes widget help or markdown near complex sections.
- Missing titles fall back to a title-cased version of the field name.
- `Field(default=...)` seeds supported widgets. For string fields without a default, `Field(example="...")` can seed the text widget.
- Short strings (`max_length < 140`), formatted strings, and write-only/password strings use a single-line text input; unbounded strings use a text area.
- Integer and number fields use `number_input` unless both min and max are available, in which case the UI uses a slider.
- Dict and list widgets are interactive add/clear editors; their support is intentionally limited to the schema shapes listed in [component reference](component-reference.md#input-widget-classification).

A showcase-style input model should include at least these field families when testing UI coverage:

```python
import datetime
from enum import Enum
from typing import Dict, List, Optional, Set
from pydantic import BaseModel, Field, SecretStr
from opyrator.components.types import FileContent

class Choice(str, Enum):
    FOO = "foo"
    BAR = "bar"

class Nested(BaseModel):
    text: str
    count: int

class Input(BaseModel):
    short_text: str = Field(..., max_length=60, description="Short text")
    password: SecretStr = Field(..., description="Secret")
    long_text: str = Field(..., description="Long text")
    integer_in_range: int = Field(20, ge=10, lt=30, multiple_of=2)
    date: Optional[datetime.date] = Field(datetime.date(2021, 4, 22))
    file_list: Optional[List[FileContent]] = None
    single_file: Optional[FileContent] = Field(None, mime_type="image/png")
    string_dict: Dict[str, str]
    single_selection: Choice
    multi_selection: Set[Choice]
    single_object: Nested
    object_list: List[Nested]
```

Safe validation from this sub-skill directory without launching a UI:

```bash
python scripts/schema_smoke.py --json
```

Success means schema utility predicates classify the supported field shapes and `FileContent` round-trips bytes to base64 and back.

## Handle FileContent inputs and outputs

Use `FileContent` for file-like values that must travel through JSON/OpenAPI and the Streamlit UI.

### Input fields

```python
from pydantic import BaseModel, Field
from opyrator.components.types import FileContent

class ImageInput(BaseModel):
    image_file: FileContent = Field(..., mime_type="image/png")
```

What the UI does:

- The Pydantic schema for `FileContent` is a string with `format: byte`.
- `InputUI` maps that shape to `file_uploader`.
- Single uploads become bytes before Pydantic validation; `FileContent.validate(...)` base64-encodes bytes.
- Lists of `FileContent` are supported as multi-file uploads when the array item schema has `format: byte`.
- Compatible input media previews are shown for `image/png`, `image/jpeg`, `audio/mpeg`, `audio/ogg`, `audio/wav`, and `video/mp4` when `mime_type` is present.

### Output fields

```python
class ImageOutput(BaseModel):
    upscaled_image_file: FileContent = Field(
        ..., mime_type="image/png", description="Upscaled PNG image."
    )
```

What the UI does:

- For compatible image/audio/video MIME types, output rendering calls `value.as_bytes()` and uses Streamlit media renderers.
- For other file MIME types or absent MIME metadata, it renders a base64 download link.
- Use `as_bytes()` for binary files and `as_str()` only for known text content.

Failure signals:

- `as_bytes()` raises when a string is not valid base64.
- `as_str()` can raise a decode error for binary bytes.
- Missing or unsupported `mime_type` does not make a file invalid; it only changes preview vs download behavior.

## Add custom input or output renderers

### Custom input UI

Add `render_input_ui` to the input model class when schema-derived widgets are not enough:

```python
from pydantic import BaseModel

class Input(BaseModel):
    text: str

    @classmethod
    def render_input_ui(cls, streamlit, input_data):
        previous = input_data.get("text", "") if isinstance(input_data, dict) else ""
        text = streamlit.text_area("Text", value=previous, key="custom-text")
        return cls(text=text)
```

Contract and cautions:

- `InputUI` checks `hasattr(input_class, "render_input_ui")`.
- The hook is called as `input_class.render_input_ui(streamlit, current_input_data)`.
- It must return an instance of the input Pydantic model; Opyrator stores `.dict()` from the return value.
- Unlike output renderers, the custom input hook is not wrapped in a local fallback. Let Pydantic validation raise useful errors or handle exceptions inside the hook.
- Use stable, unique Streamlit widget keys to avoid collisions with generated widget keys.

### Custom output UI

Add `render_output_ui` to the output model when default BaseModel/list rendering is not enough:

```python
from typing import List
from pydantic import BaseModel

class Entity(BaseModel):
    text: str
    start_char: int
    end_char: int
    label: str

class EntitiesOutput(BaseModel):
    __root__: List[Entity]

    def render_output_ui(self, streamlit, input):
        streamlit.subheader("Entities")
        streamlit.write({"source_text": input.text, "entities": [x.dict() for x in self.__root__]})
```

Contract and fallback behavior:

- `OutputUI` checks `hasattr(output_data, "render_output_ui")` on the top-level output object.
- If the renderer signature has a parameter named `input`, Opyrator calls `render_output_ui(streamlit, input=latest_operation_input)`; otherwise it calls `render_output_ui(streamlit)`.
- If the top-level custom output renderer raises, Opyrator logs the exception and falls back to default output rendering.
- Nested output objects with their own `render_output_ui` are rendered directly; if they raise, the outer `render_ui()` catch shows the exception and JSON fallback.

Use this hook for specialized visualizations such as annotated text spans or charts. Keep expensive model loading outside the renderer; the renderer should format already-computed output.

## Use reusable component outputs

`ScoredLabel` and `ClassificationOutput` provide a ready-made classification display:

```python
from opyrator.components.outputs import ClassificationOutput, ScoredLabel

result = ClassificationOutput(
    __root__=[
        ScoredLabel(label="cat", score=0.82),
        ScoredLabel(label="dog", score=0.18),
    ]
)
```

`ClassificationOutput.render_output_ui(streamlit)` sorts labels by score and renders a horizontal Plotly bar chart. If there are more than ten predictions, it asks the user how many labels to show. This is an output component only; callable wrapping and service response semantics still follow the shared Pydantic contracts routed through [api-services](../../api-services/SKILL.md).
