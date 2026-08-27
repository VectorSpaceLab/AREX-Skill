# Camera and Segmentation Workflows

## Camera-only detection

Use camera images/calibrations from `Frame` data, preserve camera names and timing fields, then produce detection outputs compatible with WOD metric/submission expectations. Route accuracy scoring to `metrics-evaluation` and latency timing to `latency-submissions`.

## 2D PVPS

PVPS workflows combine camera image streams, panoptic segmentation labels, and camera segmentation metric protos. Confirm the exact task split and available frames before trying to execute examples; many tutorial assets require dataset access.

## 3D semantic segmentation

3D semantic segmentation workflows use lidar segmentation labels and segmentation metric/submission protos. Keep lidar return, frame timestamp, and class-id mapping consistent.

## E2E driving

End-to-end driving protos model camera data and high-level commands/submissions. Treat E2E data as a distinct dataset surface, not a generic perception frame.

## Deeplab2 camera segmentation metrics

Install Deeplab2 only when the task requires camera segmentation metric code. If absent, document the optional block and continue with data/schema guidance rather than claiming metric execution.
