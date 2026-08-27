# LitServe data formats

LitServe routes request and response payloads through `decode_request`, `predict`, and
`encode_response`. Keep each boundary explicit so HTTP parsing, model input, and model
output remain testable.

## Request parsing model

For each `LitAPI`, LitServe inspects the type annotation on `decode_request`'s
`request` parameter:

- If there is no annotation, LitServe treats it as a FastAPI `Request` and prepares JSON,
  form, or multipart data before calling `decode_request`.
- If the annotation is `fastapi.Request`/`litserve.Request`, JSON bodies become `dict`,
  URL-encoded or multipart bodies become `FormData`-like mappings.
- If the annotation is a Pydantic model such as `ImageInput`, FastAPI validates the JSON
  body against that model and passes the model instance to `decode_request`.

Recommended boundary:

```python
def decode_request(self, request):
    # HTTP shape -> plain model input
    return request["input"]

def predict(self, x):
    # Plain model input -> model output
    return self.model(x)

def encode_response(self, output):
    # Model output -> HTTP response shape
    return {"output": output}
```

## JSON requests

Client request:

```bash
curl -X POST http://127.0.0.1:8000/predict \
  -H 'Content-Type: application/json' \
  -d '{"input": 4.0}'
```

API code:

```python
class JsonAPI(ls.LitAPI):
    def decode_request(self, request):
        return float(request["input"])

    def predict(self, x):
        return x * x

    def encode_response(self, output):
        return {"output": output}
```

Response:

```json
{"output": 16.0}
```

Tips:

- Keep request keys stable; `client.py` generation assumes the default `/predict` example
  shape `{"input": 4.0}`.
- Raise `fastapi.HTTPException(status_code=400, detail="...")` in `decode_request` for
  user-facing validation errors.
- `model_metadata` supplied to `LitServer` must be JSON-serializable because `/info`
  returns it as JSON.

## Pydantic model requests

Use Pydantic models when you want FastAPI validation and OpenAPI documentation:

```python
from pydantic import BaseModel

class InputPayload(BaseModel):
    text: str
    limit: int = 32

class TypedAPI(ls.LitAPI):
    def decode_request(self, request: InputPayload):
        return request.text[: request.limit]

    def predict(self, text):
        return text.upper()

    def encode_response(self, output):
        return {"text": output}
```

FastAPI validation errors are returned before `predict` runs.

## URL-encoded form data

Client request:

```bash
curl -X POST http://127.0.0.1:8000/predict \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'input=4.0'
```

API code:

```python
from fastapi import Request

class FormAPI(ls.LitAPI):
    def decode_request(self, request: Request):
        return float(request["input"])

    def predict(self, x):
        return x * x

    def encode_response(self, output):
        return {"output": output}
```

Install `python-multipart` for form and multipart parsing in environments where FastAPI
requires it.

## Multipart file uploads

Client request:

```bash
curl -X POST http://127.0.0.1:8000/predict -F 'input=@sample.txt'
```

API code:

```python
from fastapi import Request

class FileAPI(ls.LitAPI):
    def decode_request(self, request: Request):
        upload = request["input"]
        data = upload.file.read()
        return {
            "filename": getattr(upload, "filename", None),
            "size": len(data),
            "text": data.decode("utf-8", errors="replace"),
        }

    def predict(self, payload):
        return {"size": payload["size"], "uppercase": payload["text"].upper()}

    def encode_response(self, output):
        return output
```

File upload rules:

- Decode the file in `decode_request`; avoid passing open file handles into `predict`.
- Use `max_payload_size=<bytes>` on `LitServer` to enforce a hard request-size limit.
- Over-limit requests return HTTP `413` with detail `Payload too large`.
- LitServe configures Starlette multipart spooling so large form files are not silently
  written to disk before multiprocessing serialization; still decode to plain values.

## Image JSON payloads

LitServe includes image schemas:

```python
from litserve.schema.image import ImageInput, ImageOutput
```

Request payload shape:

```json
{"image_data": "<base64-encoded image bytes>"}
```

API code:

```python
class ImageAPI(ls.LitAPI):
    def decode_request(self, request: ImageInput):
        return request.get_image().convert("RGB")

    def predict(self, image):
        return image

    def encode_response(self, image) -> ImageOutput:
        return ImageOutput(image=image)
```

`ImageInput` facts:

- Field: `image_data: Optional[str] = None`.
- Validates that non-empty string fields are base64.
- `get_image(key=None)` defaults to `"image_data"` and returns a PIL image.
- If Pillow is not installed, `get_image` raises an import error telling you to install
  Pillow.
- If the key is missing, `get_image` raises `ValueError("Missing image data for key ...")`.

`ImageOutput` facts:

- Field: `image: Any`.
- Requires a PIL `Image.Image` object.
- Serializes the image as PNG bytes encoded to base64 under the `image` key.
- Raises a type error if the supplied object is not a PIL image.

Multiple image inputs can subclass `ImageInput` and call `get_image("image_0")`,
`get_image("image_1")`, etc.

## Streaming responses

For `LitAPI(stream=True)`, `predict` yields model outputs and `encode_response` yields
HTTP chunks:

```python
class StreamAPI(ls.LitAPI):
    def decode_request(self, request):
        return request["prompt"]

    def predict(self, prompt):
        for token in prompt.split():
            yield token

    def encode_response(self, output_stream):
        for token in output_stream:
            yield {"token": token}
```

Formatting behavior:

- A streamed `dict` is formatted as one JSON object followed by `\n`.
- A streamed Pydantic `BaseModel` is formatted as model JSON followed by `\n`.
- Other chunk types are returned as-is.
- Clients should read incrementally, for example with `curl -N`.

For OpenAI-compatible streaming schemas, route to `openai-specs`.

## Batched data shapes

When `max_batch_size > 1`:

1. `decode_request` runs once per request.
2. `batch(inputs)` combines a list of decoded inputs.
3. `predict(batch)` receives the batched object.
4. `unbatch(output)` splits the model output back into one item per request.
5. `encode_response` runs per output item.

Default `batch` behavior:

- Torch tensors are stacked with `torch.stack` when Torch tensors are supplied.
- NumPy arrays are stacked with `numpy.stack` when NumPy arrays are supplied.
- Other values are returned as a list.

Default `unbatch` behavior after server setup:

- Non-streaming output is converted with `list(output)`.
- Streaming output yields `list(output)` for each stream step.
- If `predict` returns a string, dict, or set in batched non-streaming mode, LitServe warns
  because these are usually not per-request lists.

Correct batched dictionary response:

```python
def predict(self, batch):
    return [{"label": label, "score": score} for label, score in model(batch)]
```

Avoid:

```python
def predict(self, batch):
    return {"label": labels, "score": scores}  # ambiguous dictionary of lists
```

## Response type annotations

LitServe inspects the return annotation of `encode_response` to register FastAPI endpoint
response handling. If there is no annotation, it uses a generic response path and FastAPI
serializes returned dictionaries normally.

Common choices:

```python
from fastapi import Response
from pydantic import BaseModel

class OutputPayload(BaseModel):
    output: float

class API(ls.LitAPI):
    def encode_response(self, output) -> OutputPayload:
        return OutputPayload(output=output)
```

For most JSON APIs, returning a dict without an annotation is sufficient.

## Built-in endpoint payloads

`GET /info` returns:

```json
{
  "model": {"name": "optional", "version": "optional"},
  "server": {
    "devices": ["cpu"],
    "workers_per_device": 1,
    "timeout": 30,
    "stream": {"/predict": false},
    "max_payload_size": null,
    "track_requests": false
  }
}
```

`GET /health` returns plain text:

- `200 ok` when workers are ready and API health checks pass.
- `503 not ready` otherwise.

`POST /shutdown`, when enabled, returns plain text confirming graceful shutdown started.

## Client content types

| Payload type | Client example | Server hook |
| --- | --- | --- |
| JSON | `curl -H 'Content-Type: application/json' -d '{"input": 4}'` | `decode_request(self, request)` receives dict or Pydantic model. |
| URL-encoded form | `curl -H 'Content-Type: application/x-www-form-urlencoded' -d 'input=4'` | `decode_request(self, request: Request)` receives form mapping. |
| Multipart file | `curl -F 'input=@file.txt'` | `decode_request(self, request: Request)` receives upload object under `input`. |
| Base64 image JSON | `curl --data-binary @payload.json` | `decode_request(self, request: ImageInput)` receives image model. |
| Streaming | `curl -N ...` | `predict` and `encode_response` yield chunks. |
