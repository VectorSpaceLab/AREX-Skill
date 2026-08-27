# Serving API Reference

## Route and constants

The Flask example exports these public names:

- `DETECTION_URL = "/v1/object-detection/<model>"`
- `ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "gif", "bmp", "tiff", "webp"}`
- `MAX_IMAGE_SIZE = 16 * 1024 * 1024`
- `app = Flask(__name__)`
- `models = {}`

## CLI parser

`utils/flask_rest_api/restapi.py` exposes:

```python
restapi.py --port PORT --model MODEL [MODEL ...]
```

- `--port` defaults to `5000`.
- `--model` defaults to `yolov5s` and may accept multiple model names.

## Request behavior

The Flask route receives a `POST` multipart request with the `image` field.

Validation order:

1. If `API_KEY` is set, compare it against the `X-API-Key` header.
2. Reject missing `image` form data.
3. Reject unsupported file extensions.
4. Reject uploads larger than `MAX_IMAGE_SIZE`.
5. Verify the uploaded image with Pillow.
6. Reject unknown model names.
7. Run the model and return `results.pandas().xyxy[0].to_json(orient="records")`.

## Status codes observed in tests

- `400` for missing/invalid image uploads.
- `401` for API-key mismatch.
- `404` for unknown model names.
- `413` for oversized uploads.
- `200` for successful image uploads.

## Practical notes

- The example server loads models through PyTorch Hub when actually executed.
- The dummy-model smoke helper should be used for request-validation checks that do not need a real checkpoint.
- Use the detection sub-skill for any question about the model's prediction behavior; this sub-skill owns the HTTP layer only.
