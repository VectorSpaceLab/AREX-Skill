# Data Preparation Workflows

This reference is for planning and validating data before Neuralangelo training. It deliberately stops at a prepared dataset and YAML config; training commands and optimization choices belong to `training-and-configs`, and mesh extraction belongs to `mesh-extraction`.

## Common Prerequisites

- A writable dataset root.
- `ffmpeg` for extracting frames from video.
- A working `colmap` executable for self-captured video or Tanks-and-Temples pose refinement. CUDA-enabled COLMAP is faster, but CPU mode can be planned by setting GPU flags to false.
- Sufficient image quality: avoid heavy motion blur, defocus, rolling-shutter artifacts, reflective surfaces, and long textureless segments.
- A clear decision about `scene_type` before metadata conversion and config generation.
- A final `transforms.json` in the Instant-NGP-style format described in `data-formats.md`.

Use the planner first to make the shell plan explicit without running anything:

```bash
python scripts/plan_preprocessing_commands.py --mode video --sequence-name scene01 --video /data/scene01.mp4 --downsample-rate 2 --scene-type object --data-dir /data/neuralangelo/scene01_ds2
```

## Choosing `scene_type`

`scene_type` affects both bounding-region heuristics and generated config fields.

| scene_type | Best for | Bound heuristic to expect | Config effects |
| --- | --- | --- | --- |
| `object` | object-centric captures and turntables | camera-pose-derived sphere | `inside_out: false`, `init_active_level: 4`, background stays enabled |
| `outdoor` | building-scale or unbounded outdoor scenes | SfM point bounds unless the cameras are strongly concentric | `inside_out: false`, `init_active_level: 8`, background stays enabled |
| `indoor` | room-scale scenes where the camera is inside the space | SfM point bounds | `inside_out: true`, `init_active_level: 8`, `background.enabled: false`, `num_samples.background: 0` |

If the wrong type was used, do not try to repair symptoms in training first. Regenerate metadata/configs or explicitly document the difference and adjust `data.readjust` only after validating the resulting bounds.

## Workflow A: Self-Captured Video

1. Pick a sequence name, frame downsample rate, and scene type.
2. Use the planner with `--mode video` to produce a command sequence. The planned stages are:
   - create `<data_dir>/images_raw`;
   - extract frames with `ffmpeg` into zero-padded image names;
   - run COLMAP feature extraction and matching;
   - run COLMAP mapping, merge/refine sparse models when needed, and undistort images;
   - create `transforms.json` from the undistorted images and sparse model using a Neuralangelo-compatible conversion step;
   - validate `transforms.json` with the bundled validator;
   - generate a config patch with the bundled config generator.
3. Prefer a higher shutter speed and stable exposure during capture. If exposure or white balance visibly changes, pass `--auto-exposure-wb` to the bundled config generator so Neuralangelo enables appearance embeddings and sets `data.num_images`.
4. After COLMAP, check that the undistorted image set used by Neuralangelo is under `images/`, not only under `images_raw/`.
5. Validate before config generation if possible; a missing or malformed metadata file is cheaper to fix than a failed training launch.

## Workflow B: Existing COLMAP Output

Use this when another tool already produced camera poses.

Expected minimum layout:

```text
<dataset>/
  images/                 # undistorted observations used by Neuralangelo
  sparse/
    cameras.bin|cameras.txt
    images.bin|images.txt
    points3D.bin|points3D.txt
  transforms.json          # generated from the active sparse model
```

Checks before accepting the handoff:

- `frames[*].file_path` in `transforms.json` must point to files under the dataset root, usually `images/<name>`.
- The metadata must use camera-to-world transforms in the OpenGL/Instant-NGP convention; COLMAP/OpenCV transforms require an axis-convention conversion before use.
- If COLMAP produced multiple sparse models (`sparse/0`, `sparse/1`, ...), record which model was used or how models were merged. Broken or split trajectories usually need re-matching rather than training retries.
- Use `validate_transforms_json.py` with `--camera-centers-csv` to make a lightweight camera-center table for external plotting or inspection.

## Workflow C: DTU-Style Data

DTU/NeuS-preprocessed scans typically have per-scan directories like:

```text
<dtu_root>/
  scan24/
    image/
      000000.png
      ...
    cameras_sphere.npz
    transforms.json
```

Caveats:

- Check dataset license and usage permissions before download or redistribution.
- DTU metadata often uses `sphere_center: [0, 0, 0]` and `sphere_radius: 1` because scans are already normalized.
- `aabb_range` may be absent in DTU-style metadata; the Neuralangelo data loader can still use `sphere_center` and `sphere_radius`, but downstream mesh-bounds planning has less information.
- For generated configs, use object-like geometry defaults (`inside_out: false`, lower coarse-to-fine start) unless the scan has been deliberately reformulated as an indoor room.
- Keep `auto_exposure_wb` disabled unless the scan images actually have changing exposure/white balance.

Validate every scan independently. If one scan is malformed, do not infer that all scans are broken.

## Workflow D: Tanks-and-Temples-Style Data

Expected scene layout:

```text
<tnt_root>/
  Barn/
    Barn_COLMAP_SfM.log
    Barn.json
    Barn.ply
    Barn_trans.txt
    images_raw/
      000001.png
      ...
    images/
    sparse/
    transforms.json
```

Caveats:

- The images are usually downloaded separately from the pose/alignment files; verify that `images_raw/` actually contains the scene images before planning COLMAP commands.
- TNT conversion uses scene alignment/point-cloud evidence to compute the bounding region. If `aabb_range` is missing, confirm whether the alignment inputs were available.
- Large outdoor scenes usually use `scene_type outdoor`; room-like scenes may require indoor-style reasoning, and some scenes may need an `inside_out` override in the generated config.
- If generated poses look globally correct but the object is cropped, focus on `sphere_center`, `sphere_radius`, `aabb_range`, and `data.readjust` before changing model parameters.

## Pose and Bounds Inspection Plan

Use this plan before blaming reconstruction quality on optimization:

1. Run the validator and export camera centers:

   ```bash
   python scripts/validate_transforms_json.py --transforms /data/scene/transforms.json --data-dir /data/scene --camera-centers-csv /tmp/scene_camera_centers.csv
   ```

2. Plot or inspect the camera centers with any trusted local plotting tool. Check for:
   - cameras collapsed to one point;
   - disconnected arcs from split COLMAP models;
   - trajectories pointed away from the object;
   - extremely large coordinates relative to `sphere_radius`;
   - missing frames that break temporal continuity.
3. Compare the intended subject with the metadata sphere/AABB:
   - `sphere_center` should be close to the scene/object center after conversion;
   - `sphere_radius` should include the subject without making it tiny in normalized coordinates;
   - `aabb_range`, when present, should bracket the region intended for mesh extraction.
4. If the bound is systematically shifted or scaled but poses are credible, set `data.readjust.center` and/or `data.readjust.scale` in the YAML config. Keep the original metadata unchanged unless regenerating it from source evidence.

## Validation Signals to Preserve in Handoffs

- source type and `scene_type`;
- exact dataset root and image subdirectory;
- number of metadata frames and discovered images;
- missing/duplicate image paths;
- `sphere_center`, `sphere_radius`, `aabb_scale`, and whether `aabb_range` exists;
- camera-center distance summary;
- config output path and whether `auto_exposure_wb` was enabled;
- unresolved warnings that could affect training or mesh extraction.
