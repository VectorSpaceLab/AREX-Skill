# Viewer, evaluation, rendering, and export workflows

## Viewer from a completed run

```bash
ns-viewer --load-config OUTPUTS/SCENE/METHOD/RUN/config.yml
```

Use when a model was already trained and the task is visual inspection. The viewer is a long-running service; do not start it from an automated preflight. For remote machines, forward the websocket port configured in the run or viewer flags.

## Evaluation metrics

```bash
ns-eval --load-config OUTPUTS/SCENE/METHOD/RUN/config.yml --output-path metrics.json
```

The output JSON includes experiment/method/checkpoint metadata and average image metrics. Add a render output directory only when image outputs are needed and disk is available.

## Rendering

Use `ns-render --help` to choose the render subcommand and confirm required camera-path arguments. Common concepts:

- camera path rendering from a viewer-exported path;
- spiral/interpolated trajectories;
- dataset image rendering for train/eval frames;
- rendered output names such as RGB, depth, accumulation, or RGBA where supported.

Rendering loads the model and can be GPU/memory-heavy; preflight output directories and batch/chunk sizes first.

## Geometry and Gaussian Splat export

```bash
ns-export pointcloud --load-config CONFIG.yml --output-dir EXPORT_DIR
ns-export tsdf --load-config CONFIG.yml --output-dir EXPORT_DIR
ns-export poisson --load-config CONFIG.yml --output-dir EXPORT_DIR
ns-export marching-cubes --load-config CONFIG.yml --output-dir EXPORT_DIR
ns-export cameras --load-config CONFIG.yml --output-dir EXPORT_DIR
ns-export gaussian-splat --load-config CONFIG.yml --output-dir EXPORT_DIR
```

Point cloud and mesh exporters may need normal/depth/RGB output names that the trained model actually produces. Gaussian Splat export is for Splatfacto-style models and writes PLY data. Mesh texturing can import graphics/OpenGL-dependent packages on headless systems.

## Handoff between stages

Use the saved `config.yml` as the source of truth. If only a checkpoint directory is available, return to the training route and recover the full run config before attempting viewer/eval/render/export.
