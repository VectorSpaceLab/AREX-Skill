# Prompt Workflow API Reference

This reference is self-contained runtime guidance for Outlines prompt composition. It intentionally avoids provider calls and source-checkout dependencies.

## Template

Import from the public namespace:

```python
from outlines import Template
```

Construction:

```python
template = Template.from_string("Hello {{ name }}!", filters={})
rendered = template(name="Ada")
```

File-backed templates are supported, but should be used only for bundled template files whose includes and inheritance stay inside the same directory tree:

```python
from pathlib import Path
from outlines import Template

template_path = Path("prompts/main.jinja").resolve()
template = Template.from_file(template_path, filters={})
prompt = template(question="What changed?", examples=[])
```

Operational facts:

- `Template.from_string(content, filters={})` builds from an inline Jinja string.
- `Template.from_file(path, filters={})` loads from a file and roots the Jinja loader at that file's directory.
- The Jinja environment uses `StrictUndefined`, so a missing variable raises a Jinja `UndefinedError` instead of rendering an empty string.
- Rendering dedents common indentation and normalizes many whitespace runs; render tests should compare the exact final prompt when whitespace matters.
- Custom filters can be supplied with `filters={"filter_name": callable}`. They may override built-ins, so keep names explicit and test them.

Built-in filters available in Outlines templates:

| Filter | Use |
|---|---|
| `name` | Render a callable's name. |
| `description` | Render the first line of a callable's docstring. |
| `source` | Render a callable's source text. Do not use this on untrusted objects. |
| `signature` | Render the callable signature text. |
| `args` | Render arguments with annotations/defaults. |
| `schema` | Pretty-render a dict or Pydantic model schema for prompt instructions. |

Safe custom filter pattern:

```python
from outlines import Template

def bullet(items):
    return "\n".join(f"- {item}" for item in items)

template = Template.from_string(
    "Items:\n{{ items | bullet }}",
    filters={"bullet": bullet},
)
print(template(items=["alpha", "beta"]))
```

Avoid dynamic filter loading from user-provided dotted paths in runtime skills; importing arbitrary callables can become code execution.

## Application

Import from the public namespace or module:

```python
from outlines import Application, Template
```

`Application(template_or_callable, output_type=None)` stores a prompt builder and an optional output type. When called, it renders the prompt, creates or reuses a generator for the supplied model, and returns the generator result.

```python
from typing import Literal
from outlines import Application, Template

template = Template.from_string("Classify this ticket: {{ ticket }}")
application = Application(template, Literal["bug", "question", "request"])

# Later, after a model has been selected by the appropriate provider/local-model route:
# label = application(model, {"ticket": "The install command fails."}, max_new_tokens=8)
```

Operational facts:

- Call shape is `application(model, template_vars: dict, **inference_kwargs)`.
- `model` is required; `Application` raises `ValueError` if it is `None`.
- Template variables must be passed as a mapping, not as keyword arguments.
- If the same model object is reused, the `Application` reuses its generator; if the model changes, it creates a new generator.
- Missing Jinja variables surface before the model call.
- For schema-backed outputs, use the sibling `../../structured-generation/` route to choose `output_type` and validation strategy.

Callable template alternative:

```python
from outlines import Application

def prompt_for(topic: str, audience: str) -> str:
    return f"Explain {topic} for {audience}."

application = Application(prompt_for, output_type=None)
# response = application(model, {"topic": "constrained decoding", "audience": "engineers"})
```

## Chat

Correct import path:

```python
from outlines.inputs import Chat, Image, Audio, Video
```

A `Chat` contains a mutable list of message dictionaries. Each message should have:

- `role`: `"system"`, `"user"`, or `"assistant"`.
- `content`: a string, a list containing text and assets such as `Image(...)`, or, for models that document it, explicit typed content dictionaries.

```python
from outlines.inputs import Chat

chat = Chat()
chat.add_system_message("Answer tersely and cite fields you used.")
chat.add_user_message("Extract the event title and location from this note.")
chat.add_assistant_message("Ready.")
chat.append({"role": "user", "content": "Dinner Friday at 7, Central Hall."})
last = chat.pop()
chat.append(last)
```

Available mutators:

- `append(message)` adds one message dict.
- `extend(messages)` appends multiple message dicts.
- `pop()` removes and returns the last message.
- `add_system_message(content)`, `add_user_message(content)`, and `add_assistant_message(content)` add role-specific messages.

`Chat` itself is permissive; provider/model adapters may reject unsupported roles, content types, or multimodal shapes. Validate shape before passing to a model.

## Image, Audio, and Video

`Image` wraps a PIL image and immediately serializes it:

```python
from io import BytesIO
from PIL import Image as PILImage
from outlines.inputs import Image

pil_image = PILImage.new("RGB", (16, 16), color="white")
pil_image.format = "PNG"  # required when the image did not come from a file
asset = Image(pil_image)
assert asset.image_format == "image/png"
assert isinstance(asset.image_str, str)
```

Operational facts:

- A PIL image without a truthy `.format` raises `TypeError`.
- `Image` base64-encodes the image bytes and records `image_format` such as `image/png` or `image/jpeg`.
- Multimodal model input is usually a list such as `["Describe this", Image(pil_image)]` or a `Chat` message whose `content` is that list.
- `Audio(audio)` and `Video(video)` are wrappers around arbitrary objects; whether they work depends on the selected model/provider. Route to `../../remote-providers/` or `../../local-models/` before relying on them.

## Caching

Imports:

```python
import outlines
from outlines.caching import cache, cache_disabled
```

Useful controls:

| Control | Scope |
|---|---|
| `OUTLINES_CACHE_DIR` | Environment variable that chooses the disk cache directory. |
| `outlines.get_cache()` | Returns the disk cache object. |
| `cache(expire=None, typed=False, ignore=())` | Decorator for memoizing a function. |
| `cache_disabled()` | Context manager that temporarily bypasses cache reads/writes. |
| `outlines.disable_cache()` | Disables cache for the current session until process state changes. |
| `outlines.clear_cache()` | Clears the cache contents. |

Cache a deterministic prompt preprocessor, not an unsafe side effect:

```python
from outlines.caching import cache, cache_disabled

@cache(expire=3600)
def normalize_examples(examples_tuple):
    return "\n".join(f"- {item}" for item in examples_tuple)

examples = normalize_examples(("first", "second"))

with cache_disabled():
    # Use for deliberately stochastic sampling, debugging stale values, or one-off probes.
    fresh_examples = normalize_examples(("first", "second"))
```

Stale-cache recovery sequence:

1. Set `OUTLINES_CACHE_DIR` to a task-specific directory when reproducibility matters.
2. Use `cache_disabled()` around sampling paths where repeated calls should vary.
3. Use `outlines.clear_cache()` when a cached function signature or output shape changed and old values are causing failures.

## Safety Boundary

Prompt workflows may generate text that resembles code. Treat it as text unless a separate, explicit sandboxed execution workflow has been approved. This sub-skill never recommends `eval`, `exec`, shelling out, importing generated modules, or running generated notebooks/scripts.
