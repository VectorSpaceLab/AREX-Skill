# Serving Workflows

## Start the API

The repository's Flask example defines a route of the form `/v1/object-detection/<model>`. The CLI exposes `--port` and `--model`.

Typical startup shape:

```bash
python utils/flask_rest_api/restapi.py --port 5000 --model yolov5s
```

Important notes:

- The server binds to localhost by default.
- Model loading uses PyTorch Hub and can download weights.
- You may pass multiple `--model` values to expose several models.
- Keep the environment prepared for Flask, torch, and YOLOv5 model loading before starting a real server.

## Client request shape

The bundled example client posts a multipart form file field named `image` to the detection route.

```python
files = {"image": ("zidane.jpg", image_bytes, "image/jpeg")}
response = requests.post("http://localhost:5000/v1/object-detection/yolov5s", files=files)
```

The route returns JSON records from the model's pandas output. A successful response is a list of detection dictionaries.

## Authentication

If `API_KEY` is set in the server environment, the client must send the same value in the `X-API-Key` header. Missing or mismatched keys are rejected with `401`.

## Upload validation

The server validates:

- presence of the `image` form field,
- allowed file extension,
- upload size (`16 MB` maximum),
- image integrity before inference,
- requested model name exists in the server's registry.

## Safe smoke testing

Use `scripts/rest_api_smoke.py` when you want to test request handling without a live server, model downloads, or network access. The helper uses Flask's test client and a dummy model object.
