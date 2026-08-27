---
name: api-server
description: "Guides segment-geospatial's FastAPI service, samgeo-api CLI,
  segmentation endpoints, model/cache behavior, output formats, and safe API
  smoke checks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# SamGeo REST API server

Use this sub-skill when the task is about serving SamGeo segmentation over HTTP,
using the `samgeo-api` command, sending curl/Python client requests, validating
endpoint parameters, or debugging API model/image caches.

## Read this when

- The user asks for `samgeo-api`, `uvicorn samgeo.api:app`, FastAPI docs, or
  Swagger UI.
- The task calls `GET /health`, `GET /models`, `DELETE /models`,
  `POST /segment/automatic`, `POST /segment/predict`, or `POST /segment/text`.
- The user needs `output_format=geojson|geotiff|png|json|detections`.
- A request fails with invalid model ids, missing prompt parameters, bad output
  format, cache problems, or GPU memory retention.

## Route elsewhere

- Direct Python class usage: [core-segmentation](../core-segmentation/SKILL.md)
  or [samgeo3-workflows](../samgeo3-workflows/SKILL.md).
- CRS/raster/vector prep before an API upload: [geospatial-utilities](../geospatial-utilities/SKILL.md).
- Optional model wrapper details: [specialized-models](../specialized-models/SKILL.md).

## API operating sequence

1. Install `segment-geospatial[api]` plus the model extra needed by requests.
   For SAM3 text endpoints, include `[samgeo3]` and verify CUDA/model access.
2. Run the safe smoke script before starting a service:
   `python scripts/api_smoke.py --local-testclient`.
3. Start the service only when a listener is wanted:
   `samgeo-api --host 0.0.0.0 --port 8000`.
4. Use `GET /models` to inspect available and loaded models.
5. Use `DELETE /models` to clear model cache and free GPU memory after large
   jobs.

## References and scripts

- [api-reference.md](references/api-reference.md) lists endpoints, parameters,
  model ids, output formats, and cache behavior.
- [workflows.md](references/workflows.md) gives server start, curl, and Python
  client examples.
- [troubleshooting.md](references/troubleshooting.md) covers common API errors
  and cache/GPU recovery.
- [scripts/api_smoke.py](scripts/api_smoke.py) probes either the local FastAPI
  TestClient or a running server without loading model weights.

## Native validation candidates

`tests/test_api.py` is a strong native candidate because it uses mocks for model
loads while validating endpoint errors, model registry exposure, output format
checks, SAM3 point prompt dispatch, and cache-key behavior.
