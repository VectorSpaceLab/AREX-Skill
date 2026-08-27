---
name: scene-generation
description: "Generate WorldGen 3D scenes from text, images, or equirectangular
  panoramas, choose splat or mesh output, and explore results in a local Viser
  viewer."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Scene generation

Use this route when the task asks for a WorldGen scene from a text prompt,
source image, or 360 panorama; wants a Gaussian splat or Open3D mesh; needs
low-VRAM or experimental Sharp/inpainting options; or wants to explore and
export novel views in a browser.

## Choose the input path

- **Text-to-scene**: construct `WorldGen(mode="t2s", ...)` and call
  `generate_world(prompt)`.
- **Image-to-scene**: construct `WorldGen(mode="i2s", ...)`, load an RGB PIL
  image, and call `generate_world(prompt, image=image)`.
- **Panorama-to-scene**: load a 2:1 equirectangular PIL image and call
  `_generate_world(pano_image, return_mesh=...)` to skip panorama diffusion.
- **Interactive viewer**: run the bundled `scripts/worldgen_demo.py`; it
  starts Viser at `http://localhost:8080`, renders the scene, and exposes camera
  path and novel-view export controls.

Read [`references/workflows.md`](references/workflows.md) for concrete code and
command recipes. Read [`references/troubleshooting.md`](references/troubleshooting.md)
for workflow-specific failures after the package-level checks in the root
[`references/troubleshooting.md`](../../references/troubleshooting.md).

## Select the output

- Leave `return_mesh=False` for the default `SplatFile` Gaussian scene. Save it
  with `scene.save("scene.ply")`.
- Set `return_mesh=True` for an Open3D triangle mesh and save it with
  `open3d.io.write_triangle_mesh("scene.glb", mesh)`.
- Do not combine `return_mesh=True` and `inpaint_bg=True` in the bundled demo.
  The inpainting implementation merges foreground/background splats.

## Select runtime options

- Use `low_vram=True` when the GPU has limited memory or when model loading
  causes an OOM. The bundled launcher auto-enables it below 24 GB.
- Use `use_sharp=True` only after the base pipeline works and the optional Sharp
  package/checkpoint is available.
- Use `inpaint_bg=True` only for an explicitly experimental background repair;
  it adds segmentation and LaMa model dependencies and extra downloads.
- Use `resolution` to trade panorama detail against memory and latency. Start
  lower when debugging an environment or an input contract.

## Safe preflight

Before a long model download or generation run:

```bash
python scripts/check_worldgen_env.py --demo-help
```

This confirms the installed public API and a tiny CUDA allocation without
loading FLUX, DA-2, Sharp, or LaMa weights. For the full flag surface, run:

```bash
python scripts/worldgen_demo.py --help
```

## Boundaries

This sub-skill owns user-facing generation, output conversion, the bundled
viewer helper, and optional generation modes. It does not own package
installation diagnosis, upstream DA-2/PyTorch3D development, model training,
release engineering, or repository maintenance. Route those questions to the
root references or a more appropriate skill.
