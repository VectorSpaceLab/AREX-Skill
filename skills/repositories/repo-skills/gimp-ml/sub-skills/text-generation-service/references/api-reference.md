# FastAPI route reference

This reference describes the observed local service contract. It is a
request-shape guide, not a promise that a provider call or GIMP bridge is
available.

## Configuration and process lifecycle

The observed local configuration contract contains integer `gimpml.port`; its
observed default value is `61482`. Validate an operator-supplied configuration
with `python scripts/inspect_service.py --config JSON_FILE`. The inspector
retains and prints only `gimpml.port`; it discards unrelated object members and
never imports application code.

HTTP checks require either an installed application's documented launcher or
an operator-provided service already running on loopback. This skill supplies
neither a launcher nor a server process. Never start an original source file or
an ad hoc application import from these instructions. If the installed
launcher is absent or no operator-provided process is running, record live HTTP
verification as blocked.

The observed service keeps `self.model` and `self.model_name` in one process.
Loading a new model name replaces the object; loading the same model name
returns `Loaded.` without checking whether the requested pipeline matches the
cached object. Treat a pipeline change as a reload boundary, preferably with a
pipeline-specific model value or an operator-controlled process restart.

## Routes

| Method | Path | Request | Observed response/behavior |
|---|---|---|---|
| `GET` | `/status` | No JSON body | Object with `service`, `cuda_available`, `cuda_total`, `cuda_used`, `cuda_free`, `ram_total`, `ram_used`, `ram_free`, `cpu`, and `os`. |
| `POST` | `/download_load_model` | JSON with `pipeline`, `model` | `{"status":"Loaded."}` on constructor success; `{"status":"Error!"}` when constructor code raises. |
| `POST` | `/run_inference` | Pipeline-specific JSON | JSON with `image`, `image_shape`, and `text` after the model method and output conversion. |

The source does not add a custom error envelope. Missing keys, malformed JSON,
invalid shapes, model-method failures, and provider exceptions may surface as
framework errors or uncaught exceptions. Clients should validate before the
request and record only sanitized error categories.

## Load request

Use a JSON object with these exact names:

```json
{
  "pipeline": "text_to_image",
  "model": "standard"
}
```

The accepted pipeline selectors are `text_to_image`, `text_edit_image`,
`text_extend_image`, and `text_outpaint_image`. The source constructors map
them to the four corresponding pipeline tools. The text-to-image bridge uses
`standard` or `hd`; the edit/extend/outpaint bridge sends placeholder model
values, so a caller should use a stable pipeline-specific value and avoid
relying on the cache shortcut.

## Inference requests

The common fields are `pipeline`, `text`, and `source`. `image_shape` is also
the requested output shape for text-to-image and edit, but is the input shape
for the image fields. Shapes are JSON arrays or tuples serialized as arrays.

Text-to-image has no input image:

```json
{
  "pipeline": "text_to_image",
  "model": "standard",
  "text": "a small red boat on a quiet lake",
  "image_shape": [64, 64, 3],
  "source": "gimp3"
}
```

Text edit requires both image and mask fields:

```json
{
  "pipeline": "text_edit_image",
  "model": "dall-e-2-edit",
  "text": "replace the object with a blue vase",
  "image": "AAEC",
  "image_shape": [1, 1, 3],
  "mask": "AAEC",
  "mask_shape": [1, 1, 3],
  "source": "gimp3"
}
```

Text extend requires an image and an exact `ext_side` value:

```json
{
  "pipeline": "text_extend_image",
  "model": "dall-e-2-extend",
  "text": "continue the landscape",
  "image": "AAEC",
  "image_shape": [1, 1, 3],
  "ext_side": "Right",
  "source": "gimp3"
}
```

Valid source-side labels are `Right`, `Bottom`, `Left`, and `Top`. Text
outpaint has the same image/text shape but no side field:

```json
{
  "pipeline": "text_outpaint_image",
  "model": "dall-e-2-outpaint",
  "text": "extend the scene naturally",
  "image": "AAAA/w==",
  "image_shape": [1, 1, 4],
  "source": "gimp3"
}
```

The examples are protocol fixtures only. They must not be sent to the
provider and are too small to be useful model inputs.

## Output and status interpretation

A normal pipeline response has the shape:

```json
{
  "image": "<base64 raw bytes>",
  "image_shape": [height, width, channels],
  "text": "<the submitted prompt>"
}
```

The source chooses `get_gimp2_output()` only when `source` equals exactly
`gimp2`; every other value selects `get_gimp3_output()`. Both methods are raw
pixel transfers, not encoded image files. GIMP 2 decodes the bytes directly
into a newly created layer. The non-GIMP-2 method explicitly flattens the
array before encoding. For normal contiguous `uint8` arrays, both represent
the same pixel bytes, but callers must honor the returned shape.

The observed `/status` implementation sets `cuda_available` to false while
still reporting host memory information. Do not infer provider or local model
readiness from this route. `Loaded.` only means the local pipeline object was
constructed; it does not prove an API key, quota, model weights, or a remote
image URL.

## Runtime-safe inspection

List the built-in route contract without a checkout or network operation:

```text
python scripts/inspect_service.py --list-routes
```

Probe only an already-running loopback status endpoint:

```text
python scripts/inspect_service.py \
  --probe-status http://127.0.0.1:61482 --timeout 2
```

The probe performs exactly `GET /status`, does not follow redirects, accepts a
0.1–5 second timeout, requires an explicit loopback port, rejects URL
credentials and non-loopback hosts, and never prints the body. The two POST
routes are static protocol records only and are never invoked by the inspector.

Construction evidence labels include `gimpml/service.py` and
`gimpml/config.json`. These names record provenance only; runtime agents must
not open, import, execute, or require those source files.
