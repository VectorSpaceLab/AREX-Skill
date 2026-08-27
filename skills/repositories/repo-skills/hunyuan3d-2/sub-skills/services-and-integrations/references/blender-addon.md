# Blender Add-on Reference

Hunyuan3D-2 includes a Blender 3.x add-on pattern that talks to the FastAPI server. The add-on is not bundled as runtime code here because it requires Blender's `bpy` runtime, but its operating contract is distilled below.

## Add-on metadata

- Name: `Hunyuan3D-2 Generator`
- Blender: `(3, 0, 0)` or newer according to `bl_info`
- Location: `View3D > Sidebar > Hunyuan3D-2 3D Generator`
- Category: `3D View`

## User properties

| Property | Default | Meaning |
| --- | --- | --- |
| `prompt` | empty | Text prompt for text-to-3D or text-conditioned selected mesh texturing. Server text support may require customization because `api_server.py` comments out `pipeline_t2i`. |
| `api_url` | `http://localhost:8080` | Base URL of the Hunyuan3D API server. Must match server host/port. |
| `image_path` | empty | Optional image file to upload. Relative Blender paths beginning with `//` are resolved relative to the `.blend` file. |
| `octree_resolution` | 256 | Generation octree resolution, min 128, max 512. |
| `num_inference_steps` | 20 | Generation steps, min 20, max 50 in UI. |
| `guidance_scale` | 5.5 | Guidance scale, min 1.0, max 10.0. |
| `texture` | false | Whether to request texture generation. |

## Payload behavior

The operator posts to `<api_url>/generate`.

### Image to 3D

When an image path exists and no selected mesh is being textured:

```json
{
  "image": "<base64 image>",
  "octree_resolution": 256,
  "num_inference_steps": 20,
  "guidance_scale": 5.5,
  "texture": false
}
```

### Text to 3D

When no image is selected:

```json
{
  "text": "prompt text",
  "octree_resolution": 256,
  "num_inference_steps": 20,
  "guidance_scale": 5.5,
  "texture": false
}
```

This depends on server-side text-to-image being available. In the repository `api_server.py`, `pipeline_t2i` is commented out, so text requests may fail unless the server is modified or launched with a text pipeline in a separate implementation.

### Texture selected mesh

If a Blender mesh object is selected and `texture=true`, the add-on exports the selected mesh to a temporary GLB, base64-encodes it, and sends it as `mesh`. It uses the selected image when available; otherwise it sends the text prompt.

```json
{
  "mesh": "<base64 glb>",
  "image": "<base64 image>",
  "octree_resolution": 256,
  "num_inference_steps": 20,
  "guidance_scale": 5.5,
  "texture": true
}
```

## Response behavior

The add-on expects a binary model file from `/generate`. It writes the response to a temporary `.glb`, imports it into the Blender scene, and reports HTTP errors through Blender's UI.

## Operating checklist

1. Start the API server first, preferably bound to `127.0.0.1` unless remote access is needed.
2. Start with image-to-3D before testing selected-mesh texturing.
3. Launch the server with `--enable_tex` before using the add-on's texture option.
4. Match the add-on `api_url` to the server port (`8080` in docs, `8081` default in `api_server.py`).
5. Keep mesh face counts reasonable before selected-mesh texture; the server cleanup cap defaults to 40000.

## Limitations

- Static Python execution outside Blender will fail on `import bpy`; this is expected.
- The add-on uses synchronous `/generate`, so the UI can wait for a long-running request.
- It does not manage model downloads or CUDA errors; those appear as server-side failures.
- Text-to-3D requires a server implementation with text-to-image enabled.
