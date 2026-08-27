# Perception API

`MapperCfg(extent_meters_xyz, voxel_size=0.005, esdf_voxel_size=0.05,
truncation_distance=0.04, depth_minimum_distance=0.1,
depth_maximum_distance=10.0, block_size=8, num_cameras=1, lidar_num_sensors=0,
feature_dim=0, device="cuda:0", ...)` controls sparse TSDF/ESDF storage,
projection, optional color/features, and integration kernels.

`Mapper` exposes `integrate`, `compute_esdf`, `extract_mesh`,
`extract_occupied_voxels`, `extract_matching_feature_voxels`, `get_stats`,
`memory_usage_mb`, `clear_region`, `reset`, `save_blocks`, and `load_blocks`.
The normal lifecycle is configure → integrate filtered observations → compute
ESDF → query/extract → update/clear/reset.

`FilterDepth` removes invalid or outside-range depth. `CameraObservation` stores
depth, color, pose, intrinsics, segmentation, and projection rays where
available. `LidarObservation` uses sensor/ray dimensions configured in
`MapperCfg`. Shape and frame conventions must remain consistent across all
observations; use float32 CUDA tensors for the kernel path.
