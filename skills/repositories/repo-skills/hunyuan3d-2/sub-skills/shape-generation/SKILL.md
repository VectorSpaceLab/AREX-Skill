---
name: shape-generation
description: "Operate Hunyuan3D-2 image-to-shape, multiview, turbo, FlashVDM,
  and mesh export workflows."
metadata:
  disco-role: operating
disable-model-invocation: true
license: NOASSERTION
---

# Hunyuan3D-2 Shape Generation

Use this sub-skill when the task is about Hunyuan3D-DiT geometry generation: single-image to mesh, multiview to mesh, mini/fast/turbo model variants, FlashVDM, seeds, octree settings, output formats, or VAE/latent shape workflows.

## Route here for

- Loading `hy3dgen.shapegen.Hunyuan3DDiTFlowMatchingPipeline` and generating a `trimesh` mesh.
- Choosing among `tencent/Hunyuan3D-2`, `tencent/Hunyuan3D-2mini`, `tencent/Hunyuan3D-2mv`, and Hunyuan3D-2.1-compatible subfolders.
- Multiview image dictionaries with `front`, `back`, `left`, and `right` keys.
- Turbo or FlashVDM decoding and `mc_algo`, `octree_resolution`, `num_chunks`, `guidance_scale`, seed, and export troubleshooting.
- Shape postprocessors such as floater removal, degenerate-face cleanup, and face reduction when used before export or texturing.

## Do not route here for

- Texture synthesis and custom rasterizer details: use `../texture-and-mesh/`.
- FastAPI, Gradio, Blender, or client payload work: use `../services-and-integrations/`.
- Installation, CUDA extension build order, and model cache planning: use `../environment-and-model-setup/`.

## Essential references

- [API reference](references/api-reference.md) for constructor/call signatures, parameter meanings, model presets, and postprocessors.
- [Workflows](references/workflows.md) for single-image, multiview, turbo/FlashVDM, VAE, and export recipes.
- [Troubleshooting](references/troubleshooting.md) for CUDA/model-cache/background-removal/export failures.

## Bundled helper

- [scripts/generate_shape.py](scripts/generate_shape.py) provides a safe CLI wrapper with `--dry-run` and lazy heavy imports. Use it to prepare or run shape generation without depending on the original repository examples.

Example dry-run:

```bash
python scripts/generate_shape.py --preset base --image input.png --output mesh.glb --dry-run
python scripts/generate_shape.py --preset mv --view front=front.png --view left=left.png --output mesh.glb --dry-run
```

Actual generation requires a CUDA-capable Hunyuan3D environment and model weights. CPU-only imports or dry-runs are not proof that shape generation works.
