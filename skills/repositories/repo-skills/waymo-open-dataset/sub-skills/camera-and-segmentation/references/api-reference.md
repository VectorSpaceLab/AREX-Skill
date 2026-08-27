# Camera and Segmentation API Reference

The verified baseline imports WDL camera op wrappers and WOD camera/segmentation utilities, but does not install Deeplab2. Treat camera segmentation metrics as optional until `deeplab2` is available.

Relevant surfaces:

- `waymo_open_dataset.wdl_limited.camera.ops.py_camera_model_ops`: camera model custom-op wrapper.
- `waymo_open_dataset.utils.camera_segmentation_utils`: helper functions for camera segmentation labels and visualization/processing.
- `waymo_open_dataset.wdl_limited.camera_segmentation.camera_segmentation_metrics`: optional path that imports `deeplab2`.
- Camera and segmentation protos cover camera segmentation labels/submissions, 3D segmentation labels/submissions, and E2E driving data/submission messages.

Use `dataset-utils` for raw image extraction from `Frame` protos before applying camera-specific challenge workflows.
