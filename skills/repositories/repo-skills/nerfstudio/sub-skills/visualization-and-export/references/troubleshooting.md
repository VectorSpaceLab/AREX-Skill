# Visualization and export troubleshooting

## Config cannot be loaded

- Confirm the path points to `config.yml`, not a checkpoint directory.
- Confirm the checkpoint files and dataset referenced by the config still exist.
- Use `check_artifacts.py --config CONFIG.yml` to inspect likely path references without loading the model.

## Viewer unreachable

- Check the configured websocket port and whether it is already in use.
- On remote machines, port-forward the viewer websocket port and keep the training/viewer process running.
- Do not use the viewer as proof that training completed; it can attach to partial/in-progress runs.

## Metrics JSON missing or empty

- Ensure `--output-path` ends in `.json` and its parent directory is writable.
- Confirm the run has a valid eval split and checkpoint.
- GPU out-of-memory during eval can be mitigated by reducing eval chunk/ray settings before rerunning.

## Render output errors

- Verify that the requested rendered output name exists for the model; common names include RGB and depth, but not every model exposes every field.
- For camera paths, confirm the path file came from the same scene scale/coordinate convention.
- Reduce resolution, seconds, rays per chunk, or output count when memory is tight.

## Export errors

- `normal output not found`: choose `--normal-method open3d` when appropriate or train a model that predicts normals.
- Headless OpenGL/pymeshlab warnings: install required graphics libraries for mesh operations or choose a non-mesh export path.
- Gaussian Splat export should be used with Splatfacto-style checkpoints; other methods may not expose Gaussian attributes.
