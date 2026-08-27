# LiDAR and external-data workflows

LiDAR mapping requires `lidar_num_sensors`, ray/image dimensions, and a
calibration/observation contract matching the configured sensor. Validate ray
projection and interpolation thresholds on a tiny synthetic scan before
integrating a sequence.

The full reference workflow may acquire an external dataset and start a Viser
viewer. Treat dataset download, Hugging Face access, camera calibration, mesh
export, and text/feature models as separate optional stages. Do not encode
credentials, cache paths, or large dataset assumptions into a reusable skill.

If ESDF values look shifted, check sensor-to-world pose, ray origin/direction,
voxel size, grid center, and coordinate convention before changing truncation or
interpolation thresholds.
