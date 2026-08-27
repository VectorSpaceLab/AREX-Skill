# Gradio and API Service Reference

This reference is self-contained. Use the bundled launchers and client helper from this sub-skill; they are compact adaptations of the repository service behavior and do not require the original checkout.

## Compact FastAPI server

Dry-run the launch plan without imports/model loading:

```bash
python scripts/launch_api_server.py --dry-run
```

Launch a local image-to-shape server when CUDA/model-cache use is intended:

```bash
python scripts/launch_api_server.py \
  --host 127.0.0.1 \
  --port 8080 \
  --model-path tencent/Hunyuan3D-2mini \
  --subfolder hunyuan3d-dit-v2-mini-turbo \
  --device cuda \
  --enable-flashvdm
```

Launch with texture support:

```bash
python scripts/launch_api_server.py \
  --host 127.0.0.1 \
  --port 8080 \
  --model-path tencent/Hunyuan3D-2mini \
  --subfolder hunyuan3d-dit-v2-mini-turbo \
  --tex-model-path tencent/Hunyuan3D-2 \
  --tex-subfolder hunyuan3d-paint-v2-0-turbo \
  --device cuda \
  --enable-flashvdm \
  --enable-tex
```

Important compact launcher flags:

| Flag | Default | Meaning |
| --- | --- | --- |
| `--host` | `127.0.0.1` | Bind address. Use `0.0.0.0` only when intentionally exposing the service. |
| `--port` | `8080` | HTTP port. Match clients/Blender `api_url`. |
| `--model-path` | `tencent/Hunyuan3D-2mini` | Shape model repo or local path. |
| `--subfolder` | `hunyuan3d-dit-v2-mini-turbo` | Shape model subfolder. |
| `--tex-model-path` | `tencent/Hunyuan3D-2` | Texture model repo or local path. |
| `--tex-subfolder` | `hunyuan3d-paint-v2-0-turbo` | Paint model subfolder. |
| `--device` | `cuda` | Generation device. CUDA is the verified backend class. |
| `--enable-tex` | false | Load Hunyuan3D-Paint and honor `texture=true` requests. |
| `--enable-flashvdm` | false | Call `enable_flashvdm()` on the shape pipeline. |
| `--mc-algo` | `mc` | Marching-cubes backend passed to FlashVDM/generation. |
| `--cache-dir` | `hunyuan3d_api_cache` | Directory for generated service outputs. |
| `--dry-run` | false | Print plan without importing models or starting Uvicorn. |

## Endpoints

### `POST /generate`

Runs generation synchronously and returns a file response on success. On failure it returns JSON with `error_code: 1` and HTTP 404.

Common payload keys:

| Key | Type | Meaning |
| --- | --- | --- |
| `image` | base64 string | Input/conditioning image. Required by the compact launcher. |
| `text` | string | The original repository service had an incomplete default text path; the bundled compact launcher intentionally reports that text-to-3D is not enabled. Use Gradio or a custom text-to-image pipeline if needed. |
| `mesh` | base64 GLB string | Existing mesh to texture instead of generating a new shape. |
| `texture` | bool | If true, run cleanup and paint pipeline. Requires launching with `--enable-tex`. |
| `seed` | int | Seed used for generated shape. Default 1234. |
| `octree_resolution` | int | Default compact-server payload value is 128 unless the client sets another value. Higher values increase detail/memory. |
| `num_inference_steps` | int | Default compact-server payload value is 5. |
| `guidance_scale` | float | Default 5.0. |
| `face_count` | int | Texture cleanup face cap; default 40000. |
| `type` | string | Output extension, default `glb`. |

Build a safe payload without contacting the server:

```bash
python scripts/request_api.py --server http://localhost:8080 --image input.png --output mesh.glb --dry-run
```

Actual request:

```bash
python scripts/request_api.py --server http://localhost:8080 --image input.png --output mesh.glb
```

Texture existing mesh:

```bash
python scripts/request_api.py --server http://localhost:8080 --mesh mesh.glb --image ref.png --texture --output textured.glb
```

### `POST /send`

Starts generation in a background thread and returns JSON:

```json
{"uid": "..."}
```

Use it when the client wants asynchronous polling.

### `GET /status/{uid}`

Returns:

```json
{"status": "processing"}
```

or:

```json
{"status": "completed", "model_base64": "..."}
```

The bundled client can poll status and decode the completed base64 model:

```bash
python scripts/request_api.py --server http://localhost:8080 --mode status --uid <uid> --output result.glb
```

## Compact Gradio app

Dry-run the launch plan:

```bash
python scripts/launch_gradio_app.py --dry-run
```

Launch a local single-image UI:

```bash
python scripts/launch_gradio_app.py \
  --model-path tencent/Hunyuan3D-2mini \
  --subfolder hunyuan3d-dit-v2-mini-turbo \
  --enable-flashvdm \
  --host 127.0.0.1 \
  --port 8080
```

Launch with texture support:

```bash
python scripts/launch_gradio_app.py \
  --model-path tencent/Hunyuan3D-2mini \
  --subfolder hunyuan3d-dit-v2-mini-turbo \
  --texgen-model-path tencent/Hunyuan3D-2 \
  --texgen-subfolder hunyuan3d-paint-v2-0-turbo \
  --enable-flashvdm \
  --enable-tex \
  --low-vram-mode \
  --host 127.0.0.1 \
  --port 8080
```

Important compact Gradio flags:

| Flag | Default | Meaning |
| --- | --- | --- |
| `--model-path` | `tencent/Hunyuan3D-2mini` | Shape model repo/path. |
| `--subfolder` | `hunyuan3d-dit-v2-mini-turbo` | Shape model subfolder. |
| `--texgen-model-path` | `tencent/Hunyuan3D-2` | Paint model repo/path. |
| `--texgen-subfolder` | `hunyuan3d-paint-v2-0-turbo` | Paint model subfolder. |
| `--host` / `--port` | `127.0.0.1` / `8080` | Service bind address. |
| `--device` | `cuda` | Generation device. |
| `--cache-path` | `hunyuan3d_gradio_cache` | Output/cache directory. |
| `--enable-tex` | false | Load paint pipeline and expose texture checkbox. |
| `--enable-flashvdm` | false | Enable FlashVDM decoder. |
| `--mc-algo` | `mc` | FlashVDM marching-cubes algorithm. |
| `--low-vram-mode` | false | Enable model CPU offload for paint submodels when texture is enabled. |
| `--share` | false | Pass `share=True` to Gradio launch. |

The bundled compact app supports single-image generation. Use the shape sub-skill's Python/CLI workflows for multiview generation.

## Safety and verification notes

- `scripts/launch_api_server.py --help`, `scripts/launch_api_server.py --dry-run`, `scripts/launch_gradio_app.py --help`, and `scripts/launch_gradio_app.py --dry-run` are safe parser/plan checks.
- Launching either service without `--dry-run` loads models and may download checkpoints. Do it only when model cache/network/GPU use is intended.
- Binding to `0.0.0.0` exposes the service on all interfaces. Prefer `127.0.0.1` for local private use.
