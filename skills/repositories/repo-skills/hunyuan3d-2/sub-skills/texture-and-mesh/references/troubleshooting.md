# Texture and Mesh Troubleshooting

## Renderer or extension import failures

Texture generation depends on compiled CUDA/C++ extensions. If `custom_rasterizer` fails with `libc10.so` missing, import `torch` first in the process:

```python
import torch
import custom_rasterizer
```

If the extension build fails on `cusparse.h`, install CUDA library development headers matching the PyTorch CUDA variant, then rebuild `hy3dgen/texgen/custom_rasterizer` without build isolation.

If `MeshRender(device="cuda")` fails, do not proceed to paint inference. Fix `custom_rasterizer`, `mesh_processor`, PyTorch CUDA, and CUDA runtime visibility first.

## `pymeshlab` and OpenGL warnings

Headless Linux environments can emit `libOpenGL.so.0: cannot open shared object file` during pymeshlab import or mesh cleanup. Install an OpenGL runtime library in the active environment and ensure its library directory is visible. Treat persistent pymeshlab errors as mesh-cleanup blockers, not cosmetic warnings, if cleanup is required before texture.

## Model download/cache issues

`Hunyuan3DPaintPipeline.from_pretrained("tencent/Hunyuan3D-2", subfolder="hunyuan3d-paint-v2-0-turbo")` needs both:

- `hunyuan3d-delight-v2-0`
- selected paint subfolder, usually `hunyuan3d-paint-v2-0-turbo`

The code checks `${HY3DGEN_MODELS:-~/.cache/hy3dgen}` for local files and otherwise downloads with `huggingface_hub.snapshot_download`. Pre-cache both subfolders for offline or no-network runs.

## Mesh/UV failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| UV wrapping fails | Invalid mesh, scene object, non-manifold geometry, or huge face count. | Load with `trimesh`, reduce/clean mesh, export to GLB, retry. |
| Texture is smeared or misaligned | Prompt image not aligned with mesh view or subject not centered. | Use RGBA/centered input; provide multiview images with front first. |
| Renderer OOM | High face count or 2048 render/texture size. | Reduce mesh face count before paint; avoid generate+paint in one process. |
| Output lacks texture in viewer | Export format/tool stripped materials. | Prefer GLB; inspect material/texture in Blender or a GLB viewer. |

## CUDA memory during full shape+texture

Repository docs quote 16 GB to 24.5 GB total VRAM for shape+texture depending on doc version/model path. The prepared host had A100 GPUs; lower-memory hosts should not assume parity.

Mitigations:

1. Generate the white mesh in a separate process and free memory before painting.
2. Use `--low_vram_mode` in Gradio or call `enable_model_cpu_offload()` for paint submodels when appropriate.
3. Reduce face count before painting.
4. Avoid running API server with high `--limit-model-concurrency`.

## Image conditioning issues

The paint pipeline recenters RGBA images and converts grayscale to RGB. It raises `ValueError("Image is fully transparent")` for empty alpha. If a reference image has a noisy background, remove background before texture or use an RGBA cutout.

## CPU is not a texture fallback

CPU imports, script dry-runs, or parser checks can validate instructions, but they do not prove texture generation. The paint configuration hardcodes CUDA-oriented rendering and the verified backend for this skill is CUDA.
