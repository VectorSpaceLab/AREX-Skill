# API, Streamlit, and Docker Workflows

## FastAPI App

The app object is `pix2tex.api.app:app` and has title `pix2tex API`. Verified
routes:

- `GET /`: health response with HTTP OK phrase and status code.
- `POST /predict/`: multipart upload field `file`, opens image with PIL, calls
  the shared `LatexOCR` model with resize enabled.
- `POST /bytes/`: multipart upload field `file` as bytes, opens image from
  bytes, calls the model with `resize=False`.

Start the API only when model loading/downloading is acceptable:

```bash
pip install "pix2tex[api]"
uvicorn pix2tex.api.app:app --host 0.0.0.0 --port 8502
```

Minimal client example:

```python
import requests

with open("equation.png", "rb") as f:
    response = requests.post("http://127.0.0.1:8502/predict/", files={"file": f})
response.raise_for_status()
print(response.json())
```

## Streamlit Frontend

`pix2tex.api.streamlit` lets users upload or paste an image and then calls the
local API at `http://127.0.0.1:8502/predict/`. The package helper
`python -m pix2tex.api.run` starts both uvicorn and Streamlit in child
processes. Treat it as a long-running UI action.

## Docker API Recipe

The Dockerfile installs base package plus `[api]`, downloads checkpoints during
image build, and starts uvicorn on port 8502. Typical usage:

```bash
docker pull lukasblecher/pix2tex:api
docker run --rm -p 8502:8502 lukasblecher/pix2tex:api
```

To run the Streamlit demo from the image, override the entrypoint and expose
port 8501. This is a service operation; confirm Docker daemon/network use first.
