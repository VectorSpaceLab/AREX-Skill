# Bundled demo CLI

Use the self-contained [`../scripts/worldgen_demo.py`](../scripts/worldgen_demo.py)
launcher instead of reopening the original repository's `demo.py`. It exposes
the same user-facing flags while importing the installed `worldgen` package.
Run `python ../scripts/worldgen_demo.py --help` before a generation run.

## Input and mode flags

| Flag | Meaning | Notes |
| --- | --- | --- |
| `-p`, `--prompt` | Text prompt | Used for text-to-scene, and optional context for image-to-scene |
| `-i`, `--image` | Input image path | Selects image-to-scene mode; the helper converts the image to RGB |
| `--pano_image` | Equirectangular panorama path | Bypasses panorama diffusion and sends a 2:1 panorama to the depth/scene stage |
| `-r`, `--resolution` | Panorama width | Default `1600`; generated height is `resolution // 2` |

The launcher chooses `t2s` when `--image` is absent and `i2s` when an image is
provided. A panorama path takes precedence in the scene-generation step.

## Output and optional-feature flags

| Flag | Meaning | Operational consequence |
| --- | --- | --- |
| `--return_mesh` | Return an Open3D triangle mesh | Cannot be combined with `--inpaint_bg` |
| `--save_scene` | Write the generated scene | Splat mode writes `splat.ply`; mesh mode writes `mesh.glb` |
| `-o`, `--output_dir` | Output directory | Default `output`; novel views are written below `images/` |
| `--low_vram` | Use the low-VRAM model path | The launcher also enables it automatically below 24 GB GPU memory |
| `--use_sharp` | Experimental Sharp Gaussian path | Requires the optional `sharp` package and Sharp weights |
| `--inpaint_bg` | Experimental background inpainting | Requires the iopaint/LaMa and segmentation model stack |

## Common commands

Text-to-scene with an interactive viewer:

```bash
python scripts/worldgen_demo.py \
  --prompt "A beautiful landscape with a river and mountains"
```

Image-to-scene with an optional prompt:

```bash
python scripts/worldgen_demo.py \
  --image path/to/input.jpg \
  --prompt "A street scene at dusk"
```

Mesh output with scene persistence:

```bash
python scripts/worldgen_demo.py \
  --prompt "A cozy bedroom" \
  --return_mesh \
  --save_scene \
  --output_dir output/bedroom
```

Panorama-to-scene input:

```bash
python scripts/worldgen_demo.py \
  --pano_image path/to/panorama.jpg \
  --save_scene
```

After generation, the viewer listens at `http://localhost:8080`. Use the
Camera Path controls to create interpolated frustums, then use Save Novel Views
to write numbered PNGs under `<output_dir>/images/` and an `rgb.mp4` video.
Press Ctrl-C in the launcher process to stop the server.

## Preflight

Run the environment check before a model download or a long GPU run:

```bash
python scripts/check_worldgen_env.py --demo-help
```

The check reports the installed WorldGen version, public constructor and method
signatures, CUDA availability, the first GPU, and a tiny CUDA allocation. It
does not download FLUX, DA-2, Sharp, or LaMa weights.
