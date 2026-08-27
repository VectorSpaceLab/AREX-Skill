# API workflows

## Safe local smoke without starting a service

```bash
python scripts/api_smoke.py --local-testclient
```

This imports `samgeo.api`, calls `/health` and `/models` through FastAPI's test
client, and does not load model weights.

## Start the server

```bash
samgeo-api --host 0.0.0.0 --port 8000
```

Development reload:

```bash
samgeo-api --reload
```

Preload one model when model downloads/GPU memory are ready:

```bash
samgeo-api --preload sam2:sam2-hiera-large
```

Interactive OpenAPI docs are served at `/docs` when the server is running.

## Curl examples

Health and model registry:

```bash
curl http://localhost:8000/health
curl http://localhost:8000/models
```

Automatic segmentation:

```bash
curl -X POST http://localhost:8000/segment/automatic \
  -F "file=@image.tif" \
  -F "model_version=sam2" \
  -F "model_id=sam2-hiera-large" \
  -F "output_format=geojson"
```

Prompt segmentation:

```bash
curl -X POST http://localhost:8000/segment/predict \
  -F "file=@image.tif" \
  -F 'point_coords=[[100, 200]]' \
  -F 'point_labels=[1]' \
  -F "output_format=geojson"
```

Box prompts:

```bash
curl -X POST http://localhost:8000/segment/predict \
  -F "file=@image.tif" \
  -F 'boxes=[[10, 20, 300, 400]]' \
  -F "output_format=json"
```

SAM3 text prompt:

```bash
curl -X POST http://localhost:8000/segment/text \
  -F "file=@image.tif" \
  -F "prompt=building" \
  -F "model_id=facebook/sam3" \
  -F "backend=meta" \
  -F "output_format=detections"
```

Clear loaded models after large work:

```bash
curl -X DELETE http://localhost:8000/models
```

## Python client pattern

```python
import requests

with open("image.tif", "rb") as f:
    response = requests.post(
        "http://localhost:8000/segment/text",
        files={"file": ("image.tif", f, "image/tiff")},
        data={"prompt": "building", "output_format": "geojson"},
        timeout=300,
    )
response.raise_for_status()
geojson = response.json()
print(len(geojson.get("features", [])))
```

## Production caution

The built-in service is a package API surface, not a complete production
platform. Add your own authentication, request limits, logging, storage policy,
TLS, monitoring, and worker lifecycle management if exposing it beyond a trusted
local/network environment.
