# Shape Generation Workflows

These workflows are self-contained operating recipes for future agents. They do not require access to the original repository examples; use the bundled helper or the code snippets below.

## Single image to GLB

```python
import torch
from PIL import Image
from hy3dgen.rembg import BackgroundRemover
from hy3dgen.shapegen import Hunyuan3DDiTFlowMatchingPipeline

image = Image.open("input.png").convert("RGBA")
# If the image is RGB or has a noisy background, remove background first.
if image.mode == "RGB":
    image = BackgroundRemover()(image)

pipeline = Hunyuan3DDiTFlowMatchingPipeline.from_pretrained(
    "tencent/Hunyuan3D-2",
    subfolder="hunyuan3d-dit-v2-0",
    variant="fp16",
    device="cuda",
)
mesh = pipeline(
    image=image,
    num_inference_steps=50,
    guidance_scale=5.0,
    octree_resolution=384,
    num_chunks=20000,
    generator=torch.Generator("cuda").manual_seed(12345),
    output_type="trimesh",
)[0]
mesh.export("mesh.glb")
```

Use the bundled CLI equivalent:

```bash
python scripts/generate_shape.py --preset base --image input.png --output mesh.glb --steps 50 --octree-resolution 384
```

Dry-run without importing models:

```bash
python scripts/generate_shape.py --preset base --image input.png --output mesh.glb --dry-run
```

## Multiview image to GLB

Use the multiview repo/model and pass a dictionary of view names. The repository examples use `front`, `left`, and `back`; `right` is also accepted by the Gradio workflow.

```python
import torch
from PIL import Image
from hy3dgen.shapegen import Hunyuan3DDiTFlowMatchingPipeline

images = {
    "front": Image.open("front.png").convert("RGBA"),
    "left": Image.open("left.png").convert("RGBA"),
    "back": Image.open("back.png").convert("RGBA"),
}

pipeline = Hunyuan3DDiTFlowMatchingPipeline.from_pretrained(
    "tencent/Hunyuan3D-2mv",
    subfolder="hunyuan3d-dit-v2-mv",
    variant="fp16",
    device="cuda",
)
mesh = pipeline(
    image=images,
    num_inference_steps=50,
    octree_resolution=384,
    num_chunks=20000,
    generator=torch.Generator("cuda").manual_seed(12345),
    output_type="trimesh",
)[0]
mesh.export("mesh_mv.glb")
```

CLI equivalent:

```bash
python scripts/generate_shape.py \
  --preset mv \
  --view front=front.png --view left=left.png --view back=back.png \
  --output mesh_mv.glb
```

## Turbo / FlashVDM generation

Turbo examples use 5 steps and call `enable_flashvdm()`. Start with `mc_algo="mc"` if a custom marching-cubes backend fails.

```python
pipeline = Hunyuan3DDiTFlowMatchingPipeline.from_pretrained(
    "tencent/Hunyuan3D-2",
    subfolder="hunyuan3d-dit-v2-0-turbo",
    use_safetensors=True,
    device="cuda",
)
pipeline.enable_flashvdm(mc_algo="mc")
mesh = pipeline(image=image, num_inference_steps=5, octree_resolution=384, num_chunks=200000)[0]
```

CLI equivalent:

```bash
python scripts/generate_shape.py --preset base-turbo --enable-flashvdm --mc-algo mc --image input.png --steps 5 --output turbo.glb
```

## Mini model workflow

Use the mini preset when VRAM or latency matters more than maximum detail:

```bash
python scripts/generate_shape.py --preset mini-turbo --enable-flashvdm --image input.png --steps 5 --output mini.glb
```

The mini model still needs CUDA and model weights. Do not present it as a CPU fallback.

## Mesh cleanup before handoff

Before texturing or export, remove floaters and reduce face count when the downstream task benefits from lower mesh complexity:

```python
from hy3dgen.shapegen import FloaterRemover, DegenerateFaceRemover, FaceReducer

mesh = FloaterRemover()(mesh)
mesh = DegenerateFaceRemover()(mesh)
mesh = FaceReducer()(mesh, max_facenum=40000)
mesh.export("clean.glb")
```

If pymeshlab warns about missing OpenGL libraries, resolve the environment issue instead of skipping cleanup silently.

## VAE encode/decode workflow

The repository includes a minimal VAE demo that loads a `hunyuan3d-vae-*-withencoder` subfolder, encodes an input mesh to latents, decodes with `latents2mesh`, then converts to `trimesh`. This is useful for VAE experiments, not for ordinary image-to-shape generation.

Operational cautions:

- It requires VAE-withencoder weights in addition to the ordinary DiT/paint checkpoints.
- It still requires CUDA for meaningful verification in this skill scope.
- Ensure the input mesh is valid and normalized before interpreting reconstruction quality.

## Choosing parameters quickly

| Goal | Suggested settings |
| --- | --- |
| Quick smoke with cached turbo weights | `--preset base-turbo --enable-flashvdm --steps 5 --octree-resolution 256` |
| Higher detail shape | Base model, 50 steps, `octree_resolution=384`, larger `num_chunks` if memory allows. |
| Lower memory export | Reduce `octree_resolution` first, then reduce `num_chunks`. |
| Determinism | Use a fixed `torch.Generator(device).manual_seed(seed)` and avoid changing model variant/subfolder. |
| Multiview consistency | Use `Hunyuan3D-2mv` model and provide at least `front`; add `left`, `back`, `right` when available. |
