# Scene-generation workflows

## 1. Text prompt to a Gaussian scene

Use a CUDA device and keep the first run conservative:

```python
import torch
from worldgen import WorldGen

worldgen = WorldGen(
    mode="t2s",
    device=torch.device("cuda"),
    resolution=1024,
    low_vram=True,
)
scene = worldgen.generate_world("A beautiful landscape with a river and mountains")
scene.save("landscape.ply")
```

The first call may download DA-2, FLUX.1-dev, and the WorldGen text-to-scene
LoRA. Accept the required model licenses and verify cache space before starting.
The return value is a `SplatFile` unless `return_mesh=True` is passed.

## 2. Image to a scene

Load an RGB image and construct the image-to-scene mode explicitly:

```python
from PIL import Image
import torch
from worldgen import WorldGen

image = Image.open("input.jpg").convert("RGB")
worldgen = WorldGen(
    mode="i2s",
    device=torch.device("cuda"),
    resolution=1024,
    low_vram=True,
)
scene = worldgen.generate_world(
    "A street scene at dusk",
    image=image,
)
scene.save("street.ply")
```

`generate_pano()` resizes the longest input edge to at most 1024 pixels before
mapping the image into panorama space. `mode="i2s"` requires a non-`None`
image; `mode="t2s"` rejects an image.

## 3. Existing equirectangular panorama

A panorama bypasses the FLUX panorama-generation stage:

```python
from PIL import Image
import torch
from worldgen import WorldGen

pano = Image.open("panorama.jpg").convert("RGB")
if pano.width != 2 * pano.height:
    raise ValueError("WorldGen panorama inputs must be 2:1")

worldgen = WorldGen(mode="t2s", device=torch.device("cuda"), low_vram=True)
splat = worldgen._generate_world(pano, return_mesh=False)
splat.save("panorama.ply")
```

The bundled viewer helper normalizes a panorama to 2048x1024 before passing it to
this route. Use the same 2:1 invariant for custom code.

## 4. Mesh output

Mesh mode converts the panorama RGB-D-ray field into an Open3D triangle mesh:

```python
import open3d as o3d
import torch
from worldgen import WorldGen

worldgen = WorldGen(mode="t2s", device=torch.device("cuda"), low_vram=True)
mesh = worldgen.generate_world("A cozy bedroom", return_mesh=True)
o3d.io.write_triangle_mesh("bedroom.glb", mesh)
```

Mesh output is mutually exclusive with background inpainting in the bundled
launcher. If a mesh viewer culls faces, use a double-sided Viser build or
inspect the mesh directly with Open3D.

## 5. Interactive browser exploration

The bundled `scripts/worldgen_demo.py` provides a self-contained viewer:

```bash
python scripts/worldgen_demo.py \
  --prompt "A well-designed cozy bedroom" \
  --save_scene \
  --output_dir output/bedroom
```

Use `--image path/to/input.jpg` for image-to-scene, `--pano_image` for an
existing panorama, and `--return_mesh` for mesh output. After generation, open
`http://localhost:8080`. In the Camera Path panel, click Generate Camera Path;
then use Save Novel Views to write PNG frames and `rgb.mp4` under the output
folder.

## 6. Experimental options

- `--use_sharp` replaces the default RGB-D-to-splat conversion with a six-face
  cubemap Sharp predictor aligned to DA-2 depth. Install and validate the
  external Sharp package and checkpoint separately.
- `--inpaint_bg` segments the foreground, removes the boundary splat, inpaints
  the panorama background with LaMa, predicts background depth, and merges the
  resulting splats. It is experimental and does not support mesh mode.
- `--low_vram` selects the Nunchaku/offload branch for the panorama model. Use
  it when the GPU is below 24 GB or when the standard pipeline OOMs.

## 7. Output checks

Before launching a viewer, validate the returned object and output path:

```python
from worldgen.utils.splat_utils import SplatFile

assert isinstance(scene, SplatFile)
assert scene.centers.shape[1] == 3
assert scene.rgbs.shape[1] == 3
scene.save("scene.ply")
```

For mesh output, check `len(mesh.vertices)` and `len(mesh.triangles)` before
writing. The demo's `--save_scene` path writes `splat.ply` or `mesh.glb`, while
novel-view export writes `images/*.png` and `rgb.mp4`.
