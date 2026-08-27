# Package and Capability Map

## Distribution and imports

- Distribution: `waymo-open-dataset-tf-2-12-0`
- Verified version: `1.6.7`
- Main import namespace: `waymo_open_dataset`
- Primary public package families: `waymo_open_dataset.v2`, `waymo_open_dataset.utils`, `waymo_open_dataset.metrics`, `waymo_open_dataset.protos`, and selected `waymo_open_dataset.wdl_limited` modules.

## Capability families

| Task family | Main modules | Owning sub-skill |
| --- | --- | --- |
| V2 columnar Perception data | `waymo_open_dataset.v2`, `v2.component`, `v2.dataframe_utils`, V2 perception components | `v2-components` |
| v1 Frame parsing and range images | `utils.frame_utils`, `utils.range_image_utils`, `utils.transform_utils` | `dataset-utils` |
| Geometry, boxes, maps, keypoint data | `utils.box_utils`, `utils.geometry_utils`, `utils.plot_maps`, `utils.keypoint_data` | `dataset-utils` |
| Detection/tracking/motion/keypoint metrics | `metrics.python.*`, `metrics.ops.py_metrics_ops`, metric protos | `metrics-evaluation` |
| Motion scenarios and sim agents | `utils.trajectory_utils`, `utils.sim_agents.*`, `protos.scenario_pb2` | `motion-sim-agents` |
| Occupancy flow | `utils.occupancy_flow_data`, `occupancy_flow_grids`, `occupancy_flow_metrics` | `motion-sim-agents` |
| WOMD camera/LiDAR feature merge | `utils.womd_camera_utils`, `utils.womd_lidar_utils` | `motion-sim-agents` |
| Real-time latency challenge | Source-derived `latency` scripts and README contract | `latency-submissions` |
| Camera ops and segmentation | `wdl_limited.camera`, `wdl_limited.camera_segmentation`, camera/segmentation protos | `camera-and-segmentation` |
| Build/test/package maintenance | Bazel workspace, `pip_pkg_scripts`, requirements, Docker docs | `repo-build-test` |

## V2 exported tags

The verified V2 API exports these component tags: `camera_box`, `camera_calibration`, `camera_hkp`, `camera_image`, `camera_segmentation`, `camera_to_lidar_box_association`, `lidar_box`, `lidar_calibration`, `lidar_camera_projection`, `lidar_camera_synced_box`, `lidar`, `lidar_hkp`, `lidar_pose`, `lidar_segmentation`, `projected_lidar_box`, `stats`, `vehicle_pose`, `object_asset_auto_label`, `object_asset_camera_sensor`, `object_asset_lidar_sensor`, `object_asset_refined_pose`, `object_asset_ray`, and `object_asset_ray_compressed`.

## Package versus source-only surfaces

The public wheel includes the installed V2, utils, metrics, protos, and most WDL-limited runtime modules. The latency evaluator directory is source evidence and is not importable as `waymo_open_dataset.latency` from the verified public wheel, so this skill bundles self-contained latency validation helpers under `sub-skills/latency-submissions/scripts/`.
