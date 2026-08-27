---
name: texture-and-mesh
description: "Operate Hunyuan3D-2 paint, texture synthesis, mesh cleanup, custom
  rasterizer, and textured export workflows."
metadata:
  disco-role: operating
disable-model-invocation: true
license: NOASSERTION
---

# Hunyuan3D-2 Texture and Mesh

Use this sub-skill when the task is about Hunyuan3D-Paint texture synthesis, texturing generated or existing meshes, multiview texture prompts, mesh cleanup before texture, GLB/OBJ export, or CUDA rasterizer/renderer failures.

## Route here for

- Loading `hy3dgen.texgen.Hunyuan3DPaintPipeline` and applying it to a `trimesh` mesh plus one or more conditioning images.
- Choosing `hunyuan3d-paint-v2-0` versus `hunyuan3d-paint-v2-0-turbo`.
- Texturing an existing handcrafted mesh or a mesh produced by the shape pipeline.
- Using `FloaterRemover`, `DegenerateFaceRemover`, `FaceReducer`, UV wrapping, and textured mesh export before service/Blender handoff.
- Diagnosing `custom_rasterizer`, `mesh_processor`, `pymeshlab`, OpenGL, UV, or CUDA memory failures during texturing.

## Do not route here for

- Pure image-to-white-mesh generation: use `../shape-generation/`.
- API server, Gradio, Blender request/response usage: use `../services-and-integrations/`.
- Installation and backend setup planning: use `../environment-and-model-setup/`.

## Essential references

- [API reference](references/api-reference.md) for paint pipeline signatures, model subfolders, input mesh/image contracts, and mesh cleanup APIs.
- [Workflows](references/workflows.md) for existing-mesh texture, generate-then-texture, multiview texture, cleanup/export, and Gradio-style export handoff.
- [Troubleshooting](references/troubleshooting.md) for renderer/extension, UV, pymeshlab/OpenGL, cache, and VRAM failures.

## Bundled helper

- [scripts/texture_mesh.py](scripts/texture_mesh.py) provides a safe CLI wrapper with `--dry-run` and lazy heavy imports.

Example dry-runs:

```bash
python scripts/texture_mesh.py --mesh mesh.glb --image reference.png --output textured.glb --dry-run
python scripts/texture_mesh.py --shape-image input.png --image input.png --output textured.glb --dry-run
python scripts/texture_mesh.py --mesh mesh.glb --image front.png --image left.png --image back.png --dry-run
```

Actual texture generation requires CUDA, Hunyuan3D paint weights, and compiled texture extensions. A successful script dry-run is a guidance check, not proof that texture inference ran.
