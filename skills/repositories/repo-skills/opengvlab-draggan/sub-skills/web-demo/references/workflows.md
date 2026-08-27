# Web demo workflow

## Purpose

Read this when you need to explain how to use the DragGAN browser UI after the bundled launcher is already installed and the preflight passed.

## Typical flow

1. Launch the UI with the bundled wrapper.
2. Wait for the default checkpoint to finish loading.
3. Pick a model from the dropdown if the current default is not the right domain.
4. Press `New Image` to generate a fresh seed image for the selected checkpoint.
5. Click once on the image to create a handle point.
6. Click again to create the matching target point.
7. Press `Drag it` to run the point-based optimization.
8. Use `Undo Last` or `Reset All` if the points are wrong.
9. Save the resulting image and video from the save panel.

## Launch flags

The bundled launcher forwards the same public flags as the installed demo module:

- `--device cuda` for the verified path.
- `--share` to create a public Gradio link.
- `--ip` to bind to a specific host address.
- `--port` to bind to a specific port.

## Point editing notes

- Handle points mark the source location you want to move.
- Target points mark the destination.
- The UI stores points in the same order used by the bundled API helpers: `[y, x]`.
- The demo saves point-tracking history only after the drag loop starts.

## Output files

When a drag session finishes, the UI writes files in a `draggan_tmp/` directory under the current working directory of the launcher process.
The image output is a PNG and the trajectory output is an MP4.

## Model selection

See `../../references/checkpoints.md` for the full checkpoint list and the default UI checkpoint.
If model loading is slow, the launcher is usually downloading the checkpoint into the cache root.

## Verified workflow reminder

This sub-skill documents the reliable seeded-image path.
The current build also exposes a mask tab and an upload tab, but those surfaces are not part of the verified core workflow and may fail or have no effect.
