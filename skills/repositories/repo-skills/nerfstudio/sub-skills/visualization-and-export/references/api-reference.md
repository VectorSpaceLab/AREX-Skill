# Visualization and export API notes

## Shared checkpoint loading

Viewer, evaluation, rendering, and exporters load a saved training config through Nerfstudio's evaluation setup utility. The loaded pipeline, datamanager, and model must match the saved method and checkpoint artifacts.

## Key command classes

- `RunViewer`: loads a `config.yml`, reconstructs the pipeline, starts a viewer state, and runs indefinitely.
- `ComputePSNR`: loads a config, computes average eval image metrics, and writes a JSON file.
- Render command dataclasses: camera-path, interpolated, spiral, and dataset render variants; each loads a pipeline and writes video/images.
- Exporter dataclasses: `ExportPointCloud`, `ExportTSDFMesh`, `ExportPoissonMesh`, `ExportMarchingCubesMesh`, `ExportCameraPoses`, and `ExportGaussianSplat`.

## Export behavior to verify

- `pointcloud` samples model outputs into a point cloud and can crop with an oriented bounding box.
- Mesh exporters depend on depth/normal/RGB output names and may use Open3D, pymeshlab, xatlas, and texture helpers.
- `cameras` exports poses to JSON.
- `gaussian-splat` writes PLY attributes for Splatfacto-style models; a test-backed utility raises `ValueError` when attribute array lengths do not match the point count.

## Safe inspection

Use `--help` and bundled preflight scripts to inspect options. Do not import a command class and call `.main()` unless the task explicitly intends to load a checkpoint and write outputs.
