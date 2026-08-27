# Metrics and Mesh Export

## Purpose

Read this when exporting DreamCraft3D geometry/texture results or planning optional image-based metrics.

## Mesh export command

The repository quickstart exports textured meshes through `launch.py --export` with the `mesh-exporter`:

```bash
python launch.py --config <trial-dir>/configs/parsed.yaml --export --gpu 0 \
  resume=<trial-dir>/ckpts/last.ckpt \
  system.exporter_type=mesh-exporter
```

Use a completed texture trial for final textured output. A geometry checkpoint can be exported for geometry inspection, but it may not contain final texture quality.

## Exporter options

The `mesh-exporter` configuration includes:

| Option | Default | Meaning |
| --- | --- | --- |
| `fmt` | `obj-mtl` | `obj-mtl` writes OBJ with material; `obj` writes OBJ without material file. |
| `save_name` | `model` | Base name for exported mesh files. |
| `save_normal` | `false` | Whether to include normals. |
| `save_uv` | `true` | Required when saving texture maps. |
| `save_texture` | `true` | Exports texture maps when material output contains texture fields. |
| `texture_size` | `1024` | Resolution of exported texture maps. |
| `texture_format` | `jpg` | Texture file format. |
| `context_type` | `gl` | Rasterizer context default in exporter code; use `cuda` in headless/Docker cases when supported. |

For headless servers or Docker environments, add:

```bash
system.exporter.context_type=cuda
```

when OpenGL rasterization fails.

## Output expectations

Successful export writes one or more export subdirectories under the trial `save/` tree. Look for:

- `.obj` mesh files,
- `.mtl` material files when using `obj-mtl`,
- texture images such as base-color maps,
- validation/test images or videos that can be used for visual sanity checks.

Use the bundled output summarizer to locate these files before diagnosing quality.

## Metrics utilities

The repository includes metric utilities for CLIP similarity, LPIPS, contextual loss, and PSNR-like image comparison. They are useful for comparing rendered views against references, but they are not cheap core checks:

- CLIP metrics require Transformers CLIP models and cache/download availability.
- LPIPS/contextual metrics require `lpips`, VGG-like components, and often GPU acceleration.
- Input conventions include reference image lists, predicted view patterns, result folders, image postfix names such as `lambertian`, dataset directories, GPU device ids, and a save directory.

Do not run these metrics as part of a quick export check unless dependencies, model caches, and input view sets are confirmed.

## Progress video helper

The small video helper scans a trial's `save/*.mp4` validation videos and creates `save/training_vid.mp4`. It requires imageio/PIL and existing MP4s. Prefer the bundled output summarizer first; only create new videos when the user requests them and codecs are available.

## Practical export sequence

1. Summarize the trial directory.
2. Confirm `configs/parsed.yaml` and checkpoint path.
3. Build the `--export` command.
4. Add `system.exporter.context_type=cuda` if OpenGL context is unavailable.
5. Run export only in the DreamCraft3D CUDA environment.
6. Summarize output again and inspect OBJ/MTL/textures.
