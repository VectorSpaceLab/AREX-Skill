# TSDF/ESDF workflows

## Tiny synthetic map

Choose a small extent and coarse voxel sizes, create a synthetic depth plane
with valid intrinsics and camera pose, filter it, integrate one or a few frames,
then compute the ESDF. Record map stats, occupied voxel counts, and memory use.
This isolates mapper shape/device issues from dataset and calibration issues.

## Depth camera stream

Filter each frame using the configured minimum/maximum distance. Update camera
pose and projection rays when the sensor moves. Integrate frames in a consistent
world frame; use static-obstacle updates for geometry that should not be fused
as transient depth.

## Optional features and visualization

Feature grids require configured feature dimensions, image/grid sizes, and an
external feature producer. Text matching and PCA visualization are application
layers. Viser is a long-lived server; keep it out of headless tests and close
its lifecycle deliberately.
