---
name: data-preparation
description: "Prepare and validate Neuralangelo datasets, transforms.json
  metadata, and data configs before training."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Neuralangelo Data Preparation

Use this sub-skill when the task is to prepare inputs for Neuralangelo from a self-captured video, an existing COLMAP reconstruction, DTU-style data, or Tanks-and-Temples-style data. The expected handoff is a dataset directory with usable images, an Instant-NGP-style `transforms.json`, and a Neuralangelo YAML config patch.

Do not use this sub-skill to run training, tune optimization, resume checkpoints, or choose GPU/memory settings; reroute those tasks to the sibling `training-and-configs` sub-skill. Do not use it for isosurface or textured mesh extraction; reroute to `mesh-extraction`.

## Start Here

1. Identify the source type:
   - `video`: a self-captured video that still needs frame extraction and COLMAP.
   - `colmap`: an already reconstructed scene with images and sparse camera data.
   - `dtu`: DTU/NeuS-style scans with `image/` folders and camera parameter archives.
   - `tnt`: Tanks-and-Temples-style scenes with images, COLMAP pose logs, alignment files, and point clouds.
2. Choose `scene_type` before generating metadata or configs:
   - `object`: object-centric turntable or bounded object; pose-derived bounds; lower coarse-to-fine start.
   - `outdoor`: building/large scene; point-derived bounds unless cameras are strongly concentric; background model remains enabled.
   - `indoor`: room-scale scene; point-derived bounds; inside-out SDF setting and no background samples.
3. Produce or collect `transforms.json` at the dataset root.
4. Validate `transforms.json` before launching any expensive training.
5. Generate a YAML config patch from the actual image dimensions and optional exposure/white-balance choice.
6. Inspect camera poses and bounding regions. If bounds are wrong, prefer editing `data.readjust.center` and `data.readjust.scale` in the generated config before changing training code.

## Bundled Helpers

Run helper scripts from this sub-skill directory, or replace `scripts/...` with the resolved path to the bundled script.

```bash
python scripts/plan_preprocessing_commands.py \
  --mode video \
  --sequence-name garden_scan \
  --video /data/videos/garden_scan.mp4 \
  --downsample-rate 2 \
  --scene-type object \
  --data-dir /data/neuralangelo/garden_scan_ds2
```

```bash
python scripts/validate_transforms_json.py \
  --transforms /data/neuralangelo/garden_scan_ds2/transforms.json \
  --data-dir /data/neuralangelo/garden_scan_ds2 \
  --camera-centers-csv /tmp/garden_scan_camera_centers.csv
```

```bash
python scripts/generate_config_from_images.py \
  --data-dir /data/neuralangelo/garden_scan_ds2 \
  --sequence-name garden_scan \
  --scene-type object \
  --auto-exposure-wb \
  --output /data/neuralangelo/garden_scan.yaml
```

The helpers are safe: they plan or validate files and do not import Neuralangelo source code, launch training, run COLMAP, download datasets, or extract meshes.

## Reference Map

- `references/workflows.md`: end-to-end data workflows, prerequisites, `scene_type` effects, and pose/bounds inspection planning.
- `references/data-formats.md`: expected directory layouts, `transforms.json` schema, coordinate conventions, bounding fields, and generated YAML fields.
- `references/troubleshooting.md`: common validation failures, COLMAP/data caveats, bounding-region symptoms, and dataset-specific fixes.

## Handoff Checklist

A prepared data handoff should state:

- dataset root and image subdirectory name;
- source type and `scene_type` used for metadata/config generation;
- number of frames/images validated;
- whether `auto_exposure_wb` / appearance embeddings were enabled;
- `sphere_center`, `sphere_radius`, and whether `aabb_range` is present;
- any manual `data.readjust.center` or `data.readjust.scale` recommendation;
- validation errors/warnings that remain unresolved.
