# Data Preparation Troubleshooting

Use this reference when preprocessing succeeds mechanically but the dataset is not yet safe to hand to Neuralangelo training.

## Fast Preflight

Before training, confirm:

- `transforms.json` exists at the dataset root used by `data.root`.
- Every `frames[*].file_path` is relative and exists under the dataset root.
- Images are undistorted and match the global `w`/`h` metadata, or mismatches are intentionally documented.
- `fl_x`, `fl_y`, `sk_x`, `sk_y`, `cx`, `cy`, `sphere_center`, `sphere_radius`, and `frames` are present.
- `sphere_radius` is positive and on the same scale as camera translations.
- If appearance embeddings are enabled, `data.num_images` matches the training image count.
- `scene_type` is recorded and matches the capture geometry.

Run:

```bash
python scripts/validate_transforms_json.py --transforms /data/scene/transforms.json --data-dir /data/scene
```

## Common Validator Errors

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `missing required key fl_x` or similar | metadata is not in Neuralangelo/Instant-NGP style | regenerate or edit `transforms.json` to include global intrinsics |
| `frame path is absolute` | metadata captured machine-specific image paths | rewrite frame paths relative to `data.root` |
| `image file missing` | metadata points to `images/` but only `images_raw/` exists, or files were moved after conversion | undistort/copy images into the expected folder or rewrite frame paths consistently |
| `transform_matrix must be 4x4` | conversion wrote flattened or partial matrices | regenerate metadata with full homogeneous matrices |
| `sphere_radius must be positive` | bound computation failed or placeholder metadata was used | recompute bounds from poses/points or set a deliberate normalized sphere |
| `aabb_range min >= max` | AABB axes were transposed or malformed | regenerate bounds; check row/column order |
| many image-size warnings | metadata was generated before resizing/undistortion, or EXIF orientation changed size interpretation | regenerate metadata from the image set used for training |

## COLMAP and Video Issues

### Few or No Registered Frames

Likely causes:

- motion blur or defocus;
- too aggressive temporal downsampling;
- textureless or reflective scene;
- camera motion with little parallax;
- wrong camera model assumption.

Fixes:

- extract more frames by lowering the downsample rate;
- recapture with higher shutter speed and better focus;
- try exhaustive matching for small/ambiguous image sets;
- verify the camera model and whether the scene needs a different matcher;
- do not proceed to training if camera poses are visibly broken.

### Split or Broken Trajectories

COLMAP may produce multiple sparse models or a merged model with inconsistent arcs. Training cannot reliably fix this. Inspect camera centers, rerun matching, remove bad frames, or rebuild the sparse model. Document which sparse model was used to create metadata.

### GPU COLMAP Fails

If the host COLMAP build has no CUDA support or GPU access is unavailable, plan commands with GPU flags set to false. Expect slower feature extraction/matching. This affects preprocessing speed, not the final Neuralangelo data schema.

## Bounding Region Symptoms

| Symptom | Possible preparation issue | Action |
| --- | --- | --- |
| reconstruction subject missing or clipped | `sphere_radius` too small, center shifted, or `aabb_range` too tight | adjust `data.readjust.scale` upward, shift `data.readjust.center`, or regenerate bounds |
| subject tiny and low detail | sphere too large or wrong scene type | reduce readjust scale or regenerate with a more appropriate scene type |
| background dominates object capture | used `outdoor` for object-centric capture | regenerate with `scene_type object` or document an explicit config override |
| room/interior behaves like outside surface | indoor scene kept object/outdoor `inside_out` setting | regenerate config with `scene_type indoor` or override `inside_out: true` and disable background |
| mesh extraction later uses unexpected crop | `aabb_range` missing or stale | regenerate metadata with AABB, or hand off the missing AABB as a mesh-extraction limitation |

`data.readjust` is for correcting a plausible bound. It is not a replacement for bad poses or a malformed coordinate convention.

## Coordinate Convention Problems

Signs of a COLMAP/OpenCV to Instant-NGP/OpenGL convention mistake:

- cameras form a plausible trajectory but look away from the subject;
- reconstruction appears mirrored or inside-out;
- determinant/norm warnings appear for many rotation blocks;
- changing `data.readjust` cannot place the subject inside the view rays.

Fix the metadata conversion rather than changing Neuralangelo training code.

## Auto Exposure / White Balance

Use `--auto-exposure-wb` during config generation only when images have noticeable exposure or white-balance changes. It enables appearance embeddings and writes `data.num_images`.

Problems and fixes:

- If `data.num_images` is less than the number of training frames, regenerate the config from the final image directory.
- If image order changed after config generation, regenerate the metadata/config pair together.
- If exposure is stable, disabling appearance embeddings is simpler and avoids unnecessary embedding state.

## DTU Caveats

- A missing `aabb_range` is common and not automatically fatal for data loading.
- Each scan must be validated separately; do not reuse dimensions or frame counts across scans.
- `cameras_sphere.npz` and `image/` must correspond to the same scan.
- If a scan was renamed or reorganized, ensure frame paths still resolve under `data.root`.

## Tanks-and-Temples Caveats

- The pose log, alignment transform, point cloud, crop file, and images must belong to the same scene name.
- Missing `images_raw/` means the scene download is incomplete.
- Missing point cloud or alignment transform makes the AABB/bounding estimate suspect.
- Some room-like scenes may need indoor/inside-out config choices even though the dataset is often treated as outdoor-scale.

## Hard Synthetic Usability Ideas

These are planning ideas for verification artifacts, not runtime test files:

1. A tiny synthetic `transforms.json` with three frames where one frame path is absolute, one matrix has a malformed bottom row, and `aabb_range` is missing. The validator should report multiple independent issues without crashing.
2. A generated-config case with two valid images, `scene_type indoor`, and `--auto-exposure-wb`; the output should set `inside_out: true`, disable background samples, set `data.num_images: 2`, and clamp validation subset to the available image count.
