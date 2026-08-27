# Service and Integration Troubleshooting

## Server does not start

- Run `python scripts/launch_api_server.py --help` or `python scripts/launch_gradio_app.py --help` first to confirm parser availability.
- Use `--dry-run` to inspect model paths/subfolders without importing Hunyuan3D or starting Uvicorn/Gradio.
- If startup begins loading models, check CUDA availability and model cache/network access.
- For texture support, install and verify `custom_rasterizer` and `mesh_processor` before launching with `--enable-tex`.
- Pass an explicit `--port` and use the same port in clients and Blender.

## Client cannot connect

| Symptom | Fix |
| --- | --- |
| Connection refused | Server not running or wrong port. Check `--host`, `--port`, firewall, and local URL. |
| Browser/client hangs | Model loading or generation still running. Use smaller/turbo settings or asynchronous `/send`. |
| CORS problem in browser | The compact API launcher adds permissive CORS. If a proxy is in front, check proxy CORS too. |
| Remote clients cannot connect | Binding to `127.0.0.1` is local-only; binding to `0.0.0.0` exposes all interfaces and should be secured. |

## `/generate` returns JSON error instead of GLB

The compact server wraps failures as HTTP 404 JSON with `error_code: 1`. Inspect server logs for the real exception. Common causes:

- Missing input image.
- Text request sent to the compact launcher; text-to-3D is intentionally not enabled there.
- CUDA OOM during shape/texture.
- Texture requested without `--enable-tex` or without texture extensions.
- Invalid base64 image/mesh payload.

## `/send` and `/status` problems

- `/send` returns a `uid` immediately but does not include the output model.
- `/status/{uid}` checks for `<cache-dir>/<uid>.glb`; if generation failed in the background thread it may stay `processing` forever unless logs are inspected.
- Status returns base64 model content only after completion. Decode it to a GLB file.

## Payload mistakes

- Base64 encode the raw bytes of the image or GLB. Do not send a data URL prefix unless the server is changed to strip it.
- Use `mesh` only for an existing GLB to texture; otherwise omit `mesh` and send an `image` for shape generation.
- Use `texture=true` only when the server loaded a paint pipeline with `--enable-tex`.
- Keep `octree_resolution`, `num_inference_steps`, and `guidance_scale` within values the server/model can handle.

## Compact Gradio app issues

- The bundled compact app supports single-image generation. Use the shape sub-skill's multiview workflows for multiview tasks.
- `--low-vram-mode` can help texture submodels but does not eliminate renderer CUDA needs.
- If the output viewer does not display a GLB, confirm the generated output path exists under `--cache-path` and open it in a standalone GLB viewer.

## Blender-specific failures

- `import bpy` fails outside Blender. Test Blender add-on workflows inside Blender, not with ordinary Python.
- Relative paths beginning with `//` are resolved relative to the `.blend` file; confirm the file exists after resolution.
- Selected mesh texturing requires an active selected object of type `MESH`; otherwise send ordinary image-to-3D payloads.
- If a textured selected mesh fails, first verify the same payload with `scripts/request_api.py` outside Blender to separate server issues from add-on UI issues.
