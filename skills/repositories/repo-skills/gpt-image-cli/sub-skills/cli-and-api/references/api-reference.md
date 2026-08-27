# API reference

This reference maps the `gpt-image` CLI behavior to the OpenAI Python SDK. Treat SDK snippets as templates: they perform real API calls when run with credentials and network access.

## SDK client

```python
from openai import OpenAI

client = OpenAI()  # reads OPENAI_API_KEY from the process environment
```

The CLI adds dotenv loading before it constructs the client: process environment wins, then `./.env`, then `~/.env`, without overriding an already-set environment variable.

## Text-to-image mapping

CLI trigger: no `-i/--image` flags.

```python
result = client.images.generate(
    model="gpt-image-2",
    prompt="a photorealistic convenience store at 10pm",
    size="1024x1024",
    quality="high",
    n=1,
    background=None,
    moderation="low",
    output_format=None,
    output_compression=None,
    user=None,
)
```

The CLI omits parameters whose values are `None`; the SDK therefore receives missing fields rather than explicit `null` values.

| CLI argument | SDK parameter | Default/special handling |
|---|---|---|
| `--model` | `model` | Default `gpt-image-2`. |
| `--prompt` | `prompt` | Required. |
| `--size` | `size` | Resolved through the shortcut table before the SDK call. |
| `--quality` | `quality` | Default `high`; cost/fidelity knob. |
| `--n` | `n` | Default `1`. |
| `--background` | `background` | Omitted when not set. |
| `--moderation` | `moderation` | Default `low`; generation route only. |
| `--format` | `output_format` | Omitted when not set; effective default is PNG behavior. |
| `--compression` | `output_compression` | Omitted when not set; intended for JPEG/WebP. |
| `--user` | `user` | Omitted when not set. |

## Reference edit and inpaint mapping

CLI trigger: one or more `-i/--image` flags. Add `-m/--mask` for mask inpainting.

```python
from pathlib import Path

image_paths = [Path("person.png"), Path("jacket.png")]
mask_path = None

image_handles = [path.open("rb") for path in image_paths]
mask_handle = mask_path.open("rb") if mask_path else None
try:
    result = client.images.edit(
        model="gpt-image-2",
        image=image_handles,
        mask=mask_handle,
        prompt="Image 1 is the person; Image 2 is the jacket. Put the jacket on the person and preserve identity.",
        size="1024x1536",
        quality="medium",
        n=1,
        background=None,
        output_format=None,
        output_compression=None,
        user=None,
        # input_fidelity is intentionally omitted for gpt-image-2.
    )
finally:
    for handle in image_handles:
        handle.close()
    if mask_handle:
        mask_handle.close()
```

| CLI argument | SDK parameter | Default/special handling |
|---|---|---|
| `--image` / `-i` | `image` | Repeatable; each path is opened as binary. Missing files exit before an API call. |
| `--mask` / `-m` | `mask` | Optional binary file; missing file exits before an API call. `--mask` requires `--image`. |
| `--prompt` | `prompt` | Required edit instruction. Identify inputs by index for multi-reference edits. |
| `--model` | `model` | Default `gpt-image-2`. |
| `--size` | `size` | Resolved shortcut/literal. |
| `--quality` | `quality` | Default `high`. |
| `--n` | `n` | Default `1`. |
| `--background` | `background` | Exposed by the CLI and omitted when unset. |
| `--input-fidelity` | `input_fidelity` | If set with `gpt-image-2`, the CLI prints a note and drops it because the model rejects the parameter. |
| `--format` | `output_format` | Omitted when unset. |
| `--compression` | `output_compression` | Omitted when unset. |
| `--user` | `user` | Omitted when unset. |

The edit route does **not** pass `moderation`.

## Verified constants and helper behavior

The package's CLI module exposes these operating facts:

```python
DEFAULT_MODEL = "gpt-image-2"
DEFAULT_SIZE = "1024x1024"
DEFAULT_MODERATION = "low"
SIZE_SHORTCUTS = {
    "1k": "1024x1024",
    "2k": "2048x2048",
    "4k": "3840x2160",
    "portrait": "1024x1536",
    "landscape": "1536x1024",
    "square": "1024x1024",
    "wide": "2048x1152",
    "tall": "2160x3840",
}
```

Operational functions used by the CLI:

- `resolve_size(value)`: lowercases a shortcut and returns the literal pixel string, or returns the input unchanged.
- `model_rejects_input_fidelity(model)`: returns true for model names starting with `gpt-image-2`; the CLI then omits `input_fidelity`.
- `default_output_path(prompt, extension)`: chooses `./fig/` when present, otherwise the current directory, and creates a timestamped prompt slug.
- `write_outputs(data, out_path, n)`: decodes each result item from `b64_json`, or downloads from `url` if no base64 field is present, then writes bytes to disk.

## Output decoding pattern

```python
import base64
from pathlib import Path

out_path = Path("output.png")
item = result.data[0]
if getattr(item, "b64_json", None):
    out_path.write_bytes(base64.b64decode(item.b64_json))
else:
    raise RuntimeError("No base64 image returned; handle URL download if your API response uses URLs")
```

The CLI handles both `b64_json` and `url` result items. When multiple images are returned, it appends `_0`, `_1`, ... before the file suffix.

## Model/parameter cautions

- `gpt-image-2` is the recommended default in the bundled evidence and supports both generation and editing workflows.
- Use `quality="low"` for cheap drafts or large sweeps; `medium` for normal exploration; `high` for final assets, dense labels, diagrams, UI, and text-heavy images.
- For `gpt-image-2`, `input_fidelity` is disabled in the source evidence; do not depend on it for the default model.
- Literal custom sizes must meet live API constraints. Shortcuts are only client-side substitutions; the API is still the final validator.
- Real SDK calls require credentials, network, and may bill the user. Prefer the bundled helper's `build-command` mode for dry runs.
