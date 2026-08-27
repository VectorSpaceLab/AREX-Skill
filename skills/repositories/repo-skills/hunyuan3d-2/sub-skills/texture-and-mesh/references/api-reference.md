# Texture and Mesh API Reference

## Public imports

```python
from hy3dgen.texgen import Hunyuan3DPaintPipeline
from hy3dgen.shapegen import FloaterRemover, DegenerateFaceRemover, FaceReducer
import trimesh
```

Import `torch` before importing or directly using `custom_rasterizer` in standalone checks so PyTorch shared libraries such as `libc10.so` are already loaded.

## Verified paint signatures

```python
Hunyuan3DPaintPipeline.from_pretrained(
    model_path,
    subfolder="hunyuan3d-paint-v2-0-turbo",
)
```

```python
Hunyuan3DPaintPipeline.__call__(mesh, image)
```

`mesh` is typically a `trimesh.Trimesh` or a mesh object returned by Hunyuan3D-DiT. `image` may be a PIL image, an image path, or a list of images/paths. The implementation normalizes `image` to a list, recenters images, applies the delight model, UV-wraps the mesh, renders normal/position views, generates multiview texture images, bakes them to UV texture, inpaints missing areas, and returns a textured mesh.

## Paint subfolders

| Subfolder | Meaning | Notes |
| --- | --- | --- |
| `hunyuan3d-paint-v2-0` | Standard paint model. | More conservative default if turbo behavior is not desired. |
| `hunyuan3d-paint-v2-0-turbo` | Distilled/turbo paint model. | Repository's current `from_pretrained` default and fast multiview texture example. |

`from_pretrained()` also needs `hunyuan3d-delight-v2-0`. If local files are absent, the code attempts Hugging Face downloads for the delight and selected paint subfolders.

## Texture pipeline internals that matter operationally

- `Hunyuan3DTexGenConfig` fixes `device='cuda'`, candidate azimuths `[0, 90, 180, 270, 0, 180]`, elevations `[0, 0, 0, 0, 90, -90]`, render/texture size `2048`, bake exponent `4`, and merge method `fast`.
- `MeshRender` is constructed when `Hunyuan3DPaintPipeline` initializes, so renderer/extension failures can happen at model-load time.
- The pipeline calls `mesh_uv_wrap(mesh)` before rendering. Meshes with invalid topology, huge face counts, or unsupported scene layouts may fail here.
- `enable_model_cpu_offload()` exists for the internal Diffusers paint models and is used by Gradio low-VRAM mode, but the renderer and Hunyuan3D texture workflow are still CUDA-oriented.

## Existing mesh texturing

```python
from PIL import Image
import trimesh
from hy3dgen.texgen import Hunyuan3DPaintPipeline

mesh = trimesh.load("mesh.glb")
image = Image.open("reference.png").convert("RGBA")
paint = Hunyuan3DPaintPipeline.from_pretrained(
    "tencent/Hunyuan3D-2",
    subfolder="hunyuan3d-paint-v2-0-turbo",
)
textured = paint(mesh, image=image)
textured.export("textured.glb")
```

For multiview texture prompts, pass a list:

```python
images = [Image.open(p).convert("RGBA") for p in ["front.png", "left.png", "back.png"]]
textured = paint(mesh, image=images)
```

## Generate then texture

The repository's `minimal_demo.py` first creates a white mesh with `Hunyuan3DDiTFlowMatchingPipeline`, then paints it with `Hunyuan3DPaintPipeline`. Keep the two-stage boundary explicit: shape generation is owned by the shape sub-skill; this sub-skill owns the texture stage and the mesh cleanup that improves texture readiness.

## Mesh cleanup APIs

```python
from hy3dgen.shapegen import FloaterRemover, DegenerateFaceRemover, FaceReducer

mesh = FloaterRemover()(mesh)
mesh = DegenerateFaceRemover()(mesh)
mesh = FaceReducer()(mesh, max_facenum=40000)
```

Use cleanup before texture if the generated mesh has disconnected floaters, degenerate faces, or too many faces for renderer/export constraints. The API server uses the same sequence when request payload sets `texture=true` and uses `face_count` default `40000`.

## Compiled extensions

Texture workflows depend on:

- `hy3dgen/texgen/custom_rasterizer` packaged as `custom_rasterizer`.
- `hy3dgen/texgen/differentiable_renderer` packaged as `mesh_processor`.
- CUDA development headers/libraries compatible with the installed PyTorch CUDA variant.

Smoke checks that are meaningful without model downloads:

```python
import torch
import mesh_processor, custom_rasterizer
from hy3dgen.texgen.differentiable_renderer.mesh_render import MeshRender
MeshRender(device="cuda")
```

If this fails, fix the environment before running paint inference.
