---
name: services-and-integrations
description: "Operate Hunyuan3D-2 FastAPI, Gradio, Blender add-on, and client
  integration workflows."
metadata:
  disco-role: operating
disable-model-invocation: true
license: NOASSERTION
---

# Hunyuan3D-2 Services and Integrations

Use this sub-skill when the task is about serving Hunyuan3D-2 through its FastAPI worker, launching the Gradio app, sending client requests, integrating with Blender, or understanding REST payloads and service flags.

## Route here for

- `api_server.py` launch flags, `/generate`, `/send`, and `/status/{uid}` behavior.
- Building base64 JSON payloads for image-to-3D, text-to-3D, existing-mesh texturing, and textured output.
- `gradio_app.py` model/subfolder flags, low-VRAM mode, FlashVDM mode, texture toggle, and cache/export behavior.
- Blender add-on installation/use at the level of API URL, image path, selected mesh, texture flag, and job status.
- Debugging local server connectivity, ports, CORS, binary GLB responses, status polling, and service-side CUDA failures.

## Do not route here for

- Low-level Hunyuan3D-DiT generation parameters except request payload routing: use `../shape-generation/`.
- Hunyuan3D-Paint internals, custom rasterizer, mesh cleanup, and texture quality: use `../texture-and-mesh/`.
- Installation, CUDA extension build order, and model cache setup: use `../environment-and-model-setup/`.

## Essential references

- [Gradio and API](references/gradio-and-api.md) for service launch commands, flags, endpoint schemas, and client workflows.
- [Blender add-on](references/blender-addon.md) for Blender properties, payload behavior, and limitations.
- [Troubleshooting](references/troubleshooting.md) for service startup, HTTP, payload, queue, and CUDA/runtime errors.

## Bundled helpers

- [scripts/request_api.py](scripts/request_api.py) builds or sends Hunyuan3D-2 API requests. It supports `--dry-run` for safe payload inspection.
- [scripts/launch_api_server.py](scripts/launch_api_server.py) is a compact self-contained FastAPI launcher adapted from the repository server semantics.
- [scripts/launch_gradio_app.py](scripts/launch_gradio_app.py) is a compact self-contained single-image Gradio launcher for installed Hunyuan3D environments.

Example dry-runs:

```bash
python scripts/request_api.py --image input.png --output mesh.glb --dry-run
python scripts/request_api.py --mesh mesh.glb --image ref.png --texture --dry-run
python scripts/request_api.py --mode status --uid 00000000-0000-0000-0000-000000000000 --dry-run
python scripts/launch_api_server.py --dry-run
python scripts/launch_gradio_app.py --dry-run
```

Omit `--dry-run` only when model loading, CUDA use, and possible checkpoint downloads are intended.
