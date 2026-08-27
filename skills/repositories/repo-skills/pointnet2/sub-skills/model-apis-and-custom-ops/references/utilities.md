# Point-cloud utilities and visualization helpers

This reference covers `utils/provider.py`, `utils/pc_util.py`, and `utils/show3d_balls.py`.

## `utils/provider.py`: data augmentation and H5 helpers

`provider.py` is NumPy/HDF5 utility code. It is Python 2-era source: several augmentation functions use `xrange`. In Python 3, a compatibility shim (`builtins.xrange = range`) is enough for these functions, but workflow scripts should not rely on raw source execution without checking.

### Data shuffling

| Function | Input | Output / behavior |
| --- | --- | --- |
| `shuffle_data(data, labels)` | `data: B,N,...`; `labels: B,...` | Returns `(data[idx,...], labels[idx], idx)` with a batch permutation. |
| `shuffle_points(batch_data)` | `batch_data: B,N,C` | Shuffles point order with one shared point-index permutation for the whole batch. This changes farthest point sampling behavior. |

### Rotation and perturbation

| Function | Input | Axis / behavior |
| --- | --- | --- |
| `rotate_point_cloud(batch_data)` | `B,N,3` | Random Y-axis rotation per shape. |
| `rotate_point_cloud_z(batch_data)` | `B,N,3` | Random Z-axis rotation per shape. |
| `rotate_point_cloud_with_normal(batch_xyz_normal)` | `B,N,6` | In-place random Y-axis rotation for XYZ and normals. |
| `rotate_perturbation_point_cloud_with_normal(batch_data, angle_sigma=0.06, angle_clip=0.18)` | `B,N,6` | Small random XYZ Euler perturbation for points/normals. |
| `rotate_point_cloud_by_angle(batch_data, rotation_angle)` | `B,N,3` | Deterministic Y-axis rotation by `rotation_angle`; returns a new array. |
| `rotate_point_cloud_by_angle_with_normal(batch_data, rotation_angle)` | `B,N,6` | Deterministic Y-axis rotation for points/normals. |
| `rotate_perturbation_point_cloud(batch_data, angle_sigma=0.06, angle_clip=0.18)` | `B,N,3` | Small random XYZ Euler perturbation. |

### Jitter, shift, scale, dropout

| Function | Input | Behavior |
| --- | --- | --- |
| `jitter_point_cloud(batch_data, sigma=0.01, clip=0.05)` | `B,N,C` | Adds clipped Gaussian noise; asserts `clip > 0`; shape-preserving. |
| `shift_point_cloud(batch_data, shift_range=0.1)` | `B,N,3` | Adds one random 3-D shift per batch item; mutates input array. |
| `random_scale_point_cloud(batch_data, scale_low=0.8, scale_high=1.25)` | `B,N,3` | Multiplies each batch item by one random scale; mutates input array. |
| `random_point_dropout(batch_pc, max_dropout_ratio=0.875)` | `B,N,3` | Replaces randomly dropped points by the first point in that cloud; mutates input array. |

### HDF5 helpers

| Function | Contract |
| --- | --- |
| `getDataFiles(list_filename)` | Reads newline-separated paths. |
| `load_h5(h5_filename)` | Opens H5 file and returns `(f['data'][:], f['label'][:])`. |
| `loadDataFile(filename)` | Alias for `load_h5`. |

## `utils/pc_util.py`: conversions, PLY I/O, and static rendering

Top-level imports require:

- `numpy`
- `eulerangles` with `euler2mat`
- `plyfile` with `PlyData`/`PlyElement`

The bundled `scripts/smoke_geometry_utils.py` checks those before running `pc_util` functionality so missing packages are not mistaken for malformed point-cloud data.

### Volume/image conversion helpers

| Function | Input | Output / notes |
| --- | --- | --- |
| `point_cloud_to_volume_batch(point_clouds, vsize=12, radius=1.0, flatten=True)` | `B,N,3`; points assumed within `[-radius, radius]` | Either `B x (vsize^3)` flattened occupancy or `B x vsize x vsize x vsize x 1`. |
| `point_cloud_to_volume(points, vsize, radius=1.0)` | `N,3` | Occupancy grid `vsize x vsize x vsize`; point exactly at `+radius` can index out of bounds because of integer binning. |
| `volume_to_point_cloud(vol)` | cubic occupancy grid | `M,3` integer voxel coordinates where occupancy is `1`; empty grid returns `(0,3)`. |
| `point_cloud_to_volume_v2_batch(point_clouds, vsize=12, radius=1.0, num_sample=128)` | `B,N,3` | `B x V x V x V x num_sample x 3`, sampled/padded per voxel and local-normalized. |
| `point_cloud_to_volume_v2(points, vsize, radius=1.0, num_sample=128)` | `N,3` | Per-voxel sampled local coordinates. Uses `np.lib.pad` in source; NumPy compatibility should be checked in modern environments. |
| `point_cloud_to_image_batch(point_clouds, imgsize, radius=1.0, num_sample=128)` | `B,N,3` | `B x I x I x num_sample x 3`. |
| `point_cloud_to_image(points, imgsize, radius=1.0, num_sample=128)` | `N,3` | 2-D pixel bins over XY with sampled/padded local point values. |

### PLY and simple rendering helpers

| Function | Contract |
| --- | --- |
| `read_ply(filename)` | Reads XYZ vertices from a PLY file and returns `N x 3` NumPy array. |
| `write_ply(points, filename, text=True)` | Writes `N x 3` points as PLY vertices. |
| `draw_point_cloud(input_points, canvasSize=500, space=200, diameter=25, xrot=0, yrot=0, zrot=0, switch_xyz=[0,1,2], normalize=True)` | Returns a grayscale `canvasSize x canvasSize` image using a software z-buffer/disk renderer. Needs `eulerangles`. Empty input returns zeros. Degenerate all-identical points can divide by zero during normalization. |
| `point_cloud_three_views(points)` | Concatenates three rendered views into a `500 x 1500` grayscale image. |
| `pyplot_draw_point_cloud(points, output_filename)` | Builds a Matplotlib 3-D scatter figure; source has save call commented out. |
| `pyplot_draw_volume(vol, output_filename)` | Converts occupancy to points then calls the Matplotlib helper. |
| `write_ply_color(points, labels, out_filename, num_classes=None)` | Writes colored OBJ-style vertex lines (`v x y z r g b`) using a Matplotlib colormap. |

## `utils/show3d_balls.py`: interactive OpenCV renderer

`show3d_balls.py` is not safe to import blindly in headless or unprepared environments because it performs side effects at import time:

- Calls `cv2.namedWindow('show3d')`, `cv2.moveWindow(...)`, and `cv2.setMouseCallback(...)` at top level.
- Loads `render_balls_so` at top level with `np.ctypeslib.load_library(os.path.join(BASE_DIR, 'render_balls_so'), '.')`.
- Requires OpenCV GUI support and a display, not just the `cv2` Python package.

### Public renderer function

```python
showpoints(
    xyz, c_gt=None, c_pred=None, waittime=0, showrot=False,
    magnifyBlue=0, freezerot=False, background=(0,0,0),
    normalizecolor=True, ballradius=10)
```

Behavior:

- Recenters and scales `xyz` to fit an `800 x 800` viewport.
- Renders white points by default; `c_gt` and `c_pred` can provide RGB colors.
- Keyboard controls: `q` exits current viewer, `Q` exits process, `t`/`p` switch ground-truth/predicted colors, `n`/`m` zoom, `r` reset zoom, `s` saves `show3d.png`.
- Returns the final keyboard command.

### Renderer build helper

The original source build recipe is:

```bash
g++ -std=c++11 render_balls_so.cpp -o render_balls_so.so -shared -fPIC -O2 -D_GLIBCXX_USE_CXX11_ABI=0
```

Use the bundled safer helper:

```bash
bash scripts/compile_render_balls_so.sh --repo-root /path/to/pointnet2 --dry-run
bash scripts/compile_render_balls_so.sh --repo-root /path/to/pointnet2 --out-dir /path/to/pointnet2/utils
```

This helper only builds the visualization renderer; it does not compile TensorFlow custom ops.

## Geometry smoke workflow

Run:

```bash
python scripts/smoke_geometry_utils.py --repo-root /path/to/pointnet2
```

Expected checks:

1. `numpy` import and deterministic tiny point cloud creation.
2. `provider.py` import with Python 3 `xrange` compatibility shim when needed.
3. Shape-preserving provider transforms: shuffle, deterministic rotation, jitter, shift, scale, dropout.
4. `eulerangles` and `plyfile` dependency check before importing `pc_util.py`.
5. Occupancy conversion, image conversion, and PLY write/read round-trip if dependencies are present.

If dependency checks fail, install or repair the named packages first. If dependencies pass but conversion checks fail, investigate data shape/range: most `pc_util` functions expect `N x 3` or `B x N x 3` points within `[-radius, radius]`, not arbitrary coordinates.
