# Hunyuan3D-2 Repo Provenance

## Source identity

- Repository: Tencent Hunyuan Hunyuan3D-2
- Origin URL: `https://github.com/Tencent-Hunyuan/Hunyuan3D-2.git`
- Branch during distillation: `main`
- Commit: `f8db63096c8282cb27354314d896feba5ba6ff8a`
- Commit date: `2025-10-28T17:58:12+08:00`
- Exact tag: none observed
- Package distribution/import: `hy3dgen`
- Package version: `2.0.2`

## Runtime skill identity

- Skill id: `hunyuan3d-2`
- Operating role: repo-specific high-reuse skill for DisCo Researcher routing.
- Generated sub-skills: `shape-generation`, `texture-and-mesh`, `services-and-integrations`, `environment-and-model-setup`.

## Evidence used

Primary evidence paths from the source repository:

- `README.md`
- `setup.py`
- `requirements.txt`
- `docs/source/started/code.md`
- `docs/source/started/api.md`
- `docs/source/started/gradio.md`
- `docs/source/started/blender.md`
- `docs/source/modelzoo.md`
- `examples/shape_gen.py`
- `examples/shape_gen_mini.py`
- `examples/shape_gen_multiview.py`
- `examples/shape_gen_v2_1.py`
- `examples/fast_shape_gen_with_flashvdm.py`
- `examples/fast_shape_gen_multiview.py`
- `examples/faster_shape_gen_with_flashvdm_mini_turbo.py`
- `examples/textured_shape_gen.py`
- `examples/textured_shape_gen_mini.py`
- `examples/textured_shape_gen_multiview.py`
- `examples/fast_texture_gen_multiview.py`
- `minimal_demo.py`
- `minimal_vae_demo.py`
- `api_server.py`
- `gradio_app.py`
- `blender_addon.py`
- `hy3dgen/shapegen/`
- `hy3dgen/texgen/`
- `hy3dgen/rembg.py`
- `hy3dgen/text2image.py`

Excluded or downweighted evidence:

- `docs/source/installation/index.md` and `docs/source/started/index.md` contain stale Delta-Prox placeholder text in this checkout.
- Large marketing images, videos/GIFs, QR codes, caches, version-control metadata, generated build outputs, and creation-only review artifacts were not used as runtime skill content.
- Low-level texture UNet internals and C++ kernels were summarized only for operational consequences.

## Verified package/API facts

Live inspection verified:

```python
Hunyuan3DDiTFlowMatchingPipeline.from_pretrained(
    model_path,
    device="cuda",
    dtype=torch.float16,
    use_safetensors=True,
    variant="fp16",
    subfolder="hunyuan3d-dit-v2-0",
    **kwargs,
)

Hunyuan3DDiTFlowMatchingPipeline.__call__(
    image=None,
    num_inference_steps=50,
    timesteps=None,
    sigmas=None,
    eta=0.0,
    guidance_scale=5.0,
    generator=None,
    box_v=1.01,
    octree_resolution=384,
    mc_level=0.0,
    mc_algo=None,
    num_chunks=8000,
    output_type="trimesh",
    enable_pbar=True,
    **kwargs,
)

Hunyuan3DPaintPipeline.from_pretrained(
    model_path,
    subfolder="hunyuan3d-paint-v2-0-turbo",
)

Hunyuan3DPaintPipeline.__call__(mesh, image)
```

Backend smokes verified in the private creation environment:

- `pip check` passed.
- `hy3dgen.shapegen`, `hy3dgen.texgen`, `hy3dgen.rembg`, and `hy3dgen.text2image` imported.
- CUDA PyTorch allocation passed.
- `mesh_processor` and `custom_rasterizer` imported when `torch` was imported first.
- `MeshRender(device="cuda")` constructed.

Full Hunyuan3D model examples were classified as network/expensive and not run by default during skill creation.

## Staleness signals for future refresh

Refresh this skill if any of the following change:

- The source commit or `hy3dgen` version changes.
- Hunyuan3D model repo ids/subfolders or model zoo entries change.
- `Hunyuan3DDiTFlowMatchingPipeline` or `Hunyuan3DPaintPipeline` signatures change.
- `api_server.py`, `gradio_app.py`, or `blender_addon.py` endpoint/flag behavior changes.
- Texture extension build layout changes under `hy3dgen/texgen/`.
- The stale documentation pages are replaced with real Hunyuan3D installation docs.
