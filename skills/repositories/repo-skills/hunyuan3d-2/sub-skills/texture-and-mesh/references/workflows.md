# Texture and Mesh Workflows

## Texture an existing mesh

```bash
python scripts/texture_mesh.py --mesh mesh.glb --image reference.png --output textured.glb --paint-subfolder hunyuan3d-paint-v2-0-turbo
```

Equivalent Python:

```python
from PIL import Image
import trimesh
from hy3dgen.texgen import Hunyuan3DPaintPipeline

mesh = trimesh.load("mesh.glb")
image = Image.open("reference.png").convert("RGBA")
paint = Hunyuan3DPaintPipeline.from_pretrained("tencent/Hunyuan3D-2", subfolder="hunyuan3d-paint-v2-0-turbo")
mesh = paint(mesh, image=image)
mesh.export("textured.glb")
```

Use this for handcrafted meshes, meshes selected in Blender, or white meshes produced in an earlier run.

## Generate a mesh then texture it

```bash
python scripts/texture_mesh.py \
  --shape-image input.png \
  --image input.png \
  --shape-preset base-turbo \
  --enable-flashvdm \
  --shape-steps 5 \
  --output textured.glb
```

This mirrors the repository's two-stage `minimal_demo.py`: Hunyuan3D-DiT creates geometry, then Hunyuan3D-Paint creates texture. For deeper shape choices, use the shape sub-skill first and pass the resulting mesh to this workflow.

## Multiview texture conditioning

The fast multiview texture example loads an existing mesh and a list of view images:

```bash
python scripts/texture_mesh.py \
  --mesh mesh.glb \
  --image front.png --image left.png --image back.png \
  --output multiview_textured.glb
```

Order matters semantically: put the most representative/front view first, then lateral/back views. The paint pipeline will recentre and delight each prompt image internally.

## Clean a generated mesh before texture

When shape generation produces extra islands or very dense geometry, clean before painting:

```python
from hy3dgen.shapegen import FloaterRemover, DegenerateFaceRemover, FaceReducer

mesh = FloaterRemover()(mesh)
mesh = DegenerateFaceRemover()(mesh)
mesh = FaceReducer()(mesh, max_facenum=40000)
```

The API server applies the same cleanup sequence before texture when a request sets `texture=true`.

## Export choices

- Prefer `.glb` for web, Blender, and API responses because it carries mesh and texture in one file.
- Use `.obj` only when the downstream tool needs separate material/texture assets and you have verified the export path.
- For Gradio-style preview, the app writes both white and textured mesh files and builds model-viewer HTML around the exported GLB.

## Low-VRAM operating mode

The Gradio app calls `texgen_worker.enable_model_cpu_offload()` when `--low_vram_mode` is set. This can reduce pressure from Diffusers submodels, but it does not remove the CUDA requirement for renderer-backed texture workflows. If VRAM is limited:

1. Texture an already-cleaned mesh rather than generating and texturing in one process.
2. Reduce face count before paint.
3. Avoid concurrent Gradio/API jobs.
4. Use turbo paint subfolder.

## Dry-run planning

Use dry-runs to validate payloads in agent workflows without triggering downloads:

```bash
python scripts/texture_mesh.py --mesh mesh.glb --image ref.png --dry-run
```

A dry-run checks local input paths and prints the model/subfolder plan. It does not import Hunyuan3D, load CUDA extensions, or prove inference.
