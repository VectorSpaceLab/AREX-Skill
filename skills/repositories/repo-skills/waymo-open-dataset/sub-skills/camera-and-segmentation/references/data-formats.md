# Camera and Segmentation Data Formats

- Camera image fields: RGB arrays plus camera intrinsics, extrinsics, width/height, pose, and rolling-shutter timing.
- Camera names must match WOD camera enums when producing 2D objects or segmentation outputs.
- Camera segmentation protos distinguish labels, metrics, and submission containers.
- 3D semantic segmentation protos are lidar-oriented; keep class ids and frame/laser association intact.
- E2E driving protos carry camera data and driving command/submission fields; do not substitute motion `Scenario` protos.

WDL-limited directories have additional license and patent terms. Check suitability before redistributing or adapting code.
