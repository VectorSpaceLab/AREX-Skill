# Visualization reference

## Prerequisites and scene loading

The public visualization API is built on `matplotlib` and expects a loaded
NAVSIM `Scene`. A scene supplies `scene.frames`, `scene.map_api`, camera
calibration/images, and a merged LiDAR point cloud. Without log metadata,
sensor blobs, and maps, there is no meaningful frame to render; do not replace
those inputs with an invented image and claim a dataset visualization check.

A typical data-backed setup is:

```python
import os
from pathlib import Path
import hydra
from hydra.utils import instantiate
from navsim.common.dataclasses import SceneFilter, SensorConfig
from navsim.common.dataloader import SceneLoader

split = "mini"  # choose a data-backed split deliberately
hydra.initialize(config_path="<your installed NAVSIM config>")
cfg = hydra.compose(config_name="all_scenes")
scene_filter: SceneFilter = instantiate(cfg)
root = Path(os.environ["OPENSCENE_DATA_ROOT"])
loader = SceneLoader(
    data_path=root / f"navsim_logs/{split}",
    original_sensor_path=root / f"sensor_blobs/{split}",
    scene_filter=scene_filter,
    synthetic_sensor_path=root / "warmup_two_stage/sensor_blobs",
    synthetic_scenes_path=root / "warmup_two_stage/synthetic_scene_pickles",
    sensor_config=SensorConfig.build_all_sensors(),
)
scene = loader.get_scene_from_token(loader.tokens[0])
frame_idx = scene.scene_metadata.num_history_frames - 1
```

Adapt the config discovery to the installed package and local environment. The
notebook-derived example uses `hydra.initialize` and an installed config tree;
it is not a reason to depend on a checkout-relative path. For a blind agent,
`SensorConfig.build_no_sensors()` is enough for the loader, but camera/LiDAR
plots require those modalities to be included.

## Built-in plots

Import the public functions from `navsim.visualization.plots`:

- `plot_bev_frame(scene, frame_idx)` renders configured BEV map, annotations,
  and optional LiDAR for one history/future frame.
- `plot_bev_with_agent(scene, agent)` compares the human future trajectory with
  `agent.compute_trajectory(scene.get_agent_input())` at the current frame.
- `plot_cameras_frame(scene, frame_idx)` renders the eight cameras in a 3x3
  grid with a configured BEV panel in the center.
- `plot_cameras_frame_with_annotations(scene, frame_idx)` projects annotated
  boxes into each camera image and puts the configured BEV panel in the center.
- `plot_cameras_frame_with_lidar(scene, frame_idx)` projects the merged LiDAR
  points into each camera using each camera's extrinsics and intrinsics.

Each returns `(figure, axes)`. Call `plt.show()` interactively or
`figure.savefig(...)` in a non-interactive job, then close the figure when
rendering many frames.

Coordinates and defaults matter:

- BEV plots treat x as forward and y as sideways; the plotting helper uses the
  transposed axes and inverts the display x direction so left/right follow the
  NAVSIM convention.
- The standard configured view is a 64 m by 64 m window around the ego rear
  axle. This is a display configuration, not a change to the scene data.
- A `Lidar` point cloud is a `(6, N)` array with x, y, z, intensity, ring, and
  lidar id rows. The global LiDAR limits and coloring are configurable.
- Camera overlays need non-empty image, intrinsics, and sensor-to-LiDAR
  calibration. A camera loaded as an empty `Camera()` cannot be projected.

## Custom layers and animation

The lower-level functions accept an existing `matplotlib.axes.Axes`:

```python
import matplotlib.pyplot as plt
from navsim.visualization.bev import add_annotations_to_bev_ax, add_lidar_to_bev_ax
from navsim.visualization.plots import configure_bev_ax

fig, ax = plt.subplots(figsize=(6, 6))
frame = scene.frames[frame_idx]
add_annotations_to_bev_ax(ax, frame.annotations)
add_lidar_to_bev_ax(ax, frame.lidar)
configure_bev_ax(ax)
fig.savefig("scene-bev.png", dpi=150, bbox_inches="tight")
plt.close(fig)
```

`add_configured_bev_on_ax` reads the global `BEV_PLOT_CONFIG["layers"]` list;
add `"lidar"` deliberately when the point cloud is available. Other useful
helpers include `add_map_to_bev_ax`, `add_trajectory_to_bev_ax`,
`add_camera_ax`, `add_annotations_to_camera_ax`, and
`add_lidar_to_camera_ax`. Keep the configuration change local to the process
or restore it after a library/client that shares the process is finished.

For animations, pass a callable with signature `(scene, frame_idx) ->
(figure, axes)` to `frame_plot_to_gif(file_name, callable, scene,
frame_indices, duration=500)`. The helper renders all requested frames and
closes each figure. `frame_plot_to_pil` is useful when the caller needs the
images rather than a file. An empty frame list is invalid for GIF creation;
check it before calling.

## Visualization stop conditions

Stop with a clear missing-input report rather than fabricating output when:

- `OPENSCENE_DATA_ROOT`, logs, sensor blobs, or map data are missing;
- a split includes synthetic scenes but its synthetic sensor/scene roots are
  not available;
- requested cameras have empty images/calibration, or LiDAR is not loaded;
- the map API cannot be constructed for the scene's map.

The visualization tutorial is distilled here rather than shipped or executed:
its random scene choice, notebook kernel state, and data paths are not
reproducible without the user's dataset.
