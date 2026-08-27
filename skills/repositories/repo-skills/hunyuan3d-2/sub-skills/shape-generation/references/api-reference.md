# Shape Generation API Reference

This reference distills the Hunyuan3D-2 shape-generation surfaces used by the repository examples and live package inspection.

## Public imports

```python
from hy3dgen.shapegen import Hunyuan3DDiTFlowMatchingPipeline
from hy3dgen.shapegen import FloaterRemover, DegenerateFaceRemover, FaceReducer, MeshSimplifier
from hy3dgen.rembg import BackgroundRemover
```

The shape pipeline returns a list whose first item is normally a `trimesh.Trimesh` when `output_type="trimesh"`.

## Verified signatures

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
```

```python
pipeline(
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
```

## Input forms

| Input | Shape | Notes |
| --- | --- | --- |
| Single image path | `image="input.png"` | Pipeline can prepare string inputs, but loading with PIL first makes preprocessing explicit. |
| PIL image | `image=Image.open(path).convert("RGBA")` | Use the alpha channel when possible; run `BackgroundRemover` on RGB inputs if the subject is not already isolated. |
| Multiview dict | `image={"front": img, "left": img, "back": img, "right": img}` | Use a multiview model/subfolder such as `tencent/Hunyuan3D-2mv` + `hunyuan3d-dit-v2-mv`. Missing views are acceptable in repo examples as long as at least one view exists. |
| Batch/list | supported by the pipeline internals | Keep batch size conservative because VAE export and texture workflows are VRAM-heavy. |

## Model and subfolder choices

| Use case | `model_path` | `subfolder` | Notes |
| --- | --- | --- | --- |
| Base single-view | `tencent/Hunyuan3D-2` | `hunyuan3d-dit-v2-0` | Default 1.1B image-to-shape model. |
| Base fast | `tencent/Hunyuan3D-2` | `hunyuan3d-dit-v2-0-fast` | Guidance-distilled faster variant. |
| Base turbo | `tencent/Hunyuan3D-2` | `hunyuan3d-dit-v2-0-turbo` | Step-distilled; pair with `enable_flashvdm()` for fast decoding. |
| Mini | `tencent/Hunyuan3D-2mini` | `hunyuan3d-dit-v2-mini` | Smaller 0.6B model. |
| Mini turbo | `tencent/Hunyuan3D-2mini` | `hunyuan3d-dit-v2-mini-turbo` | Small fast generation. |
| Multiview | `tencent/Hunyuan3D-2mv` | `hunyuan3d-dit-v2-mv` | Requires a multiview image dict. |
| Multiview turbo | `tencent/Hunyuan3D-2mv` | `hunyuan3d-dit-v2-mv-turbo` | Multiview turbo variant. |
| Hunyuan3D-2.1 shape | `tencent/Hunyuan3D-2.1` | `hunyuan3d-dit-v2-1` | Mentioned in the repository README; verify package compatibility before relying on 2.1-specific features. |

The repository docs and model zoo quote about 6 GB VRAM for shape generation. Treat that as a floor; higher `octree_resolution`, larger chunks, multiview, or concurrent service use can require more.

## Sampling and export parameters

| Parameter | Effect | Operating guidance |
| --- | --- | --- |
| `num_inference_steps` | Diffusion/flow sampling steps. | Base examples use 50; turbo examples use 5. Gradio switches mode defaults to roughly 30 normal, 10 fast, 5 turbo. |
| `guidance_scale` | Condition-following strength. | Live signature default is 5.0; Gradio exposes CFG values; too high can reduce quality. |
| `generator` | Torch RNG. | Prefer `torch.Generator(device).manual_seed(seed)` for CUDA consistency. Repo examples sometimes use `torch.manual_seed(seed)`. |
| `octree_resolution` | Surface extraction resolution. | Examples use 380/384; Gradio offers Low 196, Standard 256, High 384. Lower values reduce memory and detail. |
| `num_chunks` | Export chunk size. | Examples use 20,000 to 200,000; live default is 8,000. Reduce if export OOMs. |
| `mc_algo` | Surface extraction backend. | `mc` is used by the API server and is safe with FlashVDM. |
| `output_type` | Pipeline output conversion. | Use `"trimesh"` for direct `.export()`. Gradio sometimes requests `"mesh"` and converts with `export_to_trimesh`. |

## FlashVDM

```python
pipeline = Hunyuan3DDiTFlowMatchingPipeline.from_pretrained(
    "tencent/Hunyuan3D-2",
    subfolder="hunyuan3d-dit-v2-0-turbo",
    use_safetensors=True,
)
pipeline.enable_flashvdm(mc_algo="mc")
```

`enable_flashvdm()` may replace the VAE with a turbo VAE subfolder based on the model name:

- `Hunyuan3D-2` and `Hunyuan3D-2mv` map to `tencent/Hunyuan3D-2/hunyuan3d-vae-v2-0-turbo`.
- `Hunyuan3D-2mini` maps to `tencent/Hunyuan3D-2mini/hunyuan3d-vae-v2-mini-turbo`.

Use turbo DiT subfolders with FlashVDM. If `mc_algo` fails on a non-CUDA backend, the Gradio code falls back to `mc` for `cpu`/`mps`, but real generation for this skill is verified only on CUDA.

## Postprocessors

```python
from hy3dgen.shapegen import FloaterRemover, DegenerateFaceRemover, FaceReducer

mesh = FloaterRemover()(mesh)
mesh = DegenerateFaceRemover()(mesh)
mesh = FaceReducer()(mesh, max_facenum=40000)
```

- `FloaterRemover` removes small disconnected components through pymeshlab.
- `DegenerateFaceRemover` round-trips through pymeshlab to remove invalid faces.
- `FaceReducer(max_facenum=...)` decimates via `meshing_decimation_quadric_edge_collapse`.
- pymeshlab may require OpenGL runtime libraries even for headless processing.

## Model loading and cache behavior

`smart_load_model()` first checks `${HY3DGEN_MODELS:-~/.cache/hy3dgen}/<model_path>/<subfolder>`. If the subfolder is absent it calls `huggingface_hub.snapshot_download(repo_id=model_path, allow_patterns=[f"{subfolder}/*"])`. Therefore:

1. Pre-populate the cache for offline or no-network runs.
2. Use exact subfolder names; a typo causes a download or file-not-found failure.
3. Do not claim a run is offline unless every required subfolder is already cached locally.
