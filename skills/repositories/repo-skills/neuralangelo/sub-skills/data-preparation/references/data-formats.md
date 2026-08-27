# Neuralangelo Data Formats

Neuralangelo expects a dataset root containing images plus an Instant-NGP-style `transforms.json`. The training config points `data.root` at that dataset root and the data loader reads `<data.root>/transforms.json`.

## Dataset Layouts

### Self-Captured Video After Preprocessing

```text
<dataset>/
  database.db              # COLMAP database
  images_raw/              # frames extracted from video
  images/                  # undistorted images consumed by Neuralangelo
  sparse/
    cameras.bin
    images.bin
    points3D.bin
    0/                     # optional original model directory
  stereo/                  # optional COLMAP output, not used by Neuralangelo data loading
  transforms.json
```

### Existing COLMAP Reconstruction

```text
<dataset>/
  images/                  # preferred image directory for frame paths
  sparse/
    cameras.bin|cameras.txt
    images.bin|images.txt
    points3D.bin|points3D.txt
  transforms.json
```

If the active sparse model is nested under `sparse/0/`, record whether metadata was generated from the nested model or from files copied/merged into `sparse/`.

### DTU-Style Scan

```text
<dtu_root>/
  scanXX/
    image/
      *.png
    cameras_sphere.npz
    transforms.json
```

DTU-style metadata is commonly normalized with `sphere_center: [0, 0, 0]` and `sphere_radius: 1`; `aabb_range` may be missing.

### Tanks-and-Temples-Style Scene

```text
<tnt_root>/
  <Scene>/
    <Scene>_COLMAP_SfM.log
    <Scene>.json
    <Scene>.ply
    <Scene>_trans.txt
    images_raw/
      *.png
    images/
    sparse/
    transforms.json
```

The point cloud and alignment transform are used to define the scene bound. Missing alignment files are a data-preparation problem, not a training problem.

## `transforms.json` Schema

Neuralangelo uses the same broad metadata style as Instant NGP. A robust custom file should contain:

```json
{
  "camera_angle_x": 0.8,
  "camera_angle_y": 0.6,
  "fl_x": 1200.0,
  "fl_y": 1200.0,
  "sk_x": 0.0,
  "sk_y": 0.0,
  "cx": 800.0,
  "cy": 600.0,
  "w": 1600,
  "h": 1200,
  "k1": 0.0,
  "k2": 0.0,
  "k3": 0.0,
  "k4": 0.0,
  "p1": 0.0,
  "p2": 0.0,
  "is_fisheye": false,
  "aabb_scale": 2.0,
  "aabb_range": [[-1.0, 1.0], [-1.0, 1.0], [-1.0, 1.0]],
  "sphere_center": [0.0, 0.0, 0.0],
  "sphere_radius": 1.0,
  "frames": [
    {
      "file_path": "images/000001.jpg",
      "transform_matrix": [
        [1.0, 0.0, 0.0, 0.0],
        [0.0, 1.0, 0.0, 0.0],
        [0.0, 0.0, 1.0, 2.0],
        [0.0, 0.0, 0.0, 1.0]
      ]
    }
  ]
}
```

### Fields the Neuralangelo Data Loader Directly Uses

- `fl_x`, `fl_y`, `sk_x`, `sk_y`, `cx`, `cy`: assembled into the camera intrinsic matrix.
- `frames[*].file_path`: image path relative to `data.root`.
- `frames[*].transform_matrix`: camera-to-world pose in OpenGL/Instant-NGP convention.
- `sphere_center`: subtracted from camera translations before normalization.
- `sphere_radius`: divides camera translations to normalize the scene.

### Fields Used by Other Neuralangelo Workflows or Diagnostics

- `camera_angle_x`, `camera_angle_y`: redundant with focal length and image size but useful for schema compatibility.
- `w`, `h`: expected raw image dimensions; used by validators and converters to catch stale metadata.
- `k1`, `k2`, `k3`, `k4`, `p1`, `p2`, `is_fisheye`: distortion metadata. Neuralangelo expects undistorted images for standard custom data, so these should usually be zero and `false`.
- `aabb_scale`: power-of-two scale derived from the bound radius for Instant-NGP-style resolution computations.
- `aabb_range`: 3D axis-aligned bounding range in source coordinates. It is especially useful for mesh extraction bounds. DTU-style data may omit it.

## Coordinate Convention

`transform_matrix` should be camera-to-world (`c2w`) in the OpenGL/Instant-NGP convention. COLMAP poses are usually in an OpenCV-style convention and must be converted before being stored in `transforms.json`. A common symptom of a convention mistake is that camera centers look plausible but all cameras point away from the target or the reconstruction appears inside-out.

Every matrix should be 4x4, finite, and have a final row close to `[0, 0, 0, 1]`. The upper-left 3x3 block should be approximately a rotation matrix with determinant near `+1` or `-1` depending on convention handling; a determinant near zero indicates a malformed transform.

## Bounds and Readjustment

Neuralangelo normalizes the scene using:

1. subtract `sphere_center` from each camera translation;
2. optionally add `data.readjust.center` from the config;
3. divide by `sphere_radius` multiplied by `data.readjust.scale`.

Use `data.readjust` for small manual corrections after validation:

```yaml
data:
  readjust:
    center: [0.0, 0.0, 0.0]
    scale: 1.0
```

Guidance:

- Increase `scale` if the region is too tight and clips the subject.
- Decrease `scale` if the subject is tiny inside a huge sphere.
- Adjust `center` if the sphere is consistently shifted away from the subject.
- If camera poses are broken, do not use `readjust` as a substitute for rerunning or repairing COLMAP.

## Generated YAML Config Fields

The bundled `generate_config_from_images.py` creates a patch config with these fields:

```yaml
_parent_: "projects/neuralangelo/configs/base.yaml"
model:
  object:
    sdf:
      mlp:
        inside_out: false
      encoding:
        coarse2fine:
          init_active_level: 4
  appear_embed:
    enabled: false
data:
  type: "projects.neuralangelo.data"
  root: "/data/neuralangelo/scene"
  train:
    image_size: [1200, 1600]
  val:
    image_size: [300, 400]
  readjust:
    center: [0.0, 0.0, 0.0]
    scale: 1.0
```

The script changes values according to `scene_type`:

- `object`: `inside_out: false`, `init_active_level: 4`.
- `outdoor`: `inside_out: false`, `init_active_level: 8`.
- `indoor`: `inside_out: true`, `init_active_level: 8`, disables background rendering.

With `--auto-exposure-wb`, it also writes:

```yaml
model:
  appear_embed:
    enabled: true
    dim: 8
data:
  num_images: <number of files in images/>
```

`data.num_images` must be at least the number of training images when appearance embeddings are enabled. If it is too small, the model can index outside the embedding table; if it is stale, frame-to-embedding alignment may be wrong.

## Dataset-Specific Caveats

### DTU

- Treat scans as already normalized unless there is evidence otherwise.
- Do not assume `aabb_range` exists.
- Use image dimensions from the actual scan images, not from another scan's config.
- Keep exposure embeddings disabled unless the data source has real exposure variation.

### Tanks and Temples

- Scene files, image files, and alignment files can be downloaded from different sources; verify they belong to the same scene.
- Large outdoor scenes can have many frames; consider downsampled validation subsets in config generation.
- If a scene has room-like geometry, document any indoor/inside-out override instead of relying on the default outdoor interpretation.

### Self-Captured Video

- `images_raw/` is not necessarily the image directory used for training after undistortion; frame paths in metadata should normally use `images/`.
- Temporal downsampling should leave enough parallax and overlap for COLMAP.
- Auto exposure and white-balance changes should be handled before training config handoff.
