# Visualization Workflows

Det3D includes Python helpers for KITTI, prediction, BEV/simple views, network
visualization, and optional VTK/Open3D-based interactive rendering. Inputs may
include point clouds, boxes, class/score arrays, calibration, images, and
per-sample metadata.

Before rendering, identify whether boxes are lidar-, camera-, or global-frame;
confirm center versus bottom-center convention, dimension order, yaw sign/axis,
and the calibration transform. Filter by score/class only after preserving raw
results for analysis.

For servers and CI, use Matplotlib's non-interactive backend and save to a file.
The documented Qt failure `Could not connect to display` can often be avoided
with `QT_QPA_PLATFORM=offscreen`, but some VTK/Open3D paths still need native
headless support. Do not install GUI-heavy packages for log-only work.

Repository notebooks are exploratory evidence, not stable CLI contracts. Adapt
the coordinate/data ideas into a small user-owned script rather than depending
on an original notebook path.
