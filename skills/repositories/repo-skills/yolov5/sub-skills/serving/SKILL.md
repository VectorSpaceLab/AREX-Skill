---
name: serving
description: "Use this YOLOv5 sub-skill for the Flask REST API example, request
  validation, API-key handling, client payloads, and safe service smoke checks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: AGPL 3.0
---

# YOLOv5 Flask Serving

Use this route for the repository's Flask REST API example: `utils/flask_rest_api/restapi.py`, its request payloads, API-key behavior, upload validation, and safe smoke testing.

## Choose the workflow

- **Plan a request or server**: read `references/workflows.md` for route shape, image upload behavior, client request structure, and server startup considerations.
- **Inspect the API contract**: read `references/api-reference.md` for the route, model name, upload limit, file-type checks, and JSON response shape.
- **Check the service safely**: run `scripts/rest_api_smoke.py` to exercise the Flask test client with a dummy model instead of starting a server or downloading weights.

## Common decisions

- The route expects an image upload under the `image` form field.
- Set `API_KEY` only when you need authenticated requests; send the matching `X-API-Key` header.
- The server allows only a small set of image extensions and a 16 MB upload cap.
- The bundled example server loads YOLOv5 models through PyTorch Hub when actually started; that can download weights.
- The smoke helper avoids network, weight downloads, and a live listener.

## Handoffs

- Route detection behavior questions to `../detection/SKILL.md`.
- Route export/deployment-format questions to `../export/SKILL.md`.
- Read root `references/troubleshooting.md` for upload, auth, and service-side failure surfaces.
