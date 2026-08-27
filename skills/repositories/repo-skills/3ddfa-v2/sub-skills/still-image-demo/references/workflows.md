# Still-image workflows

## Output mode table

| `-o` value | What it produces | Extra notes |
| --- | --- | --- |
| `2d_sparse` | Sparse landmark overlay | Fastest visual check; uses the landmark drawer. |
| `2d_dense` | Dense landmark overlay | Uses the dense vertex set for more points. |
| `3d` | Rendered 3D mesh overlay | Requires the Sim3DR and `render.so` build products. |
| `depth` | Depth visualization | Background is kept unless disabled. |
| `pncc` | PNCC visualization | Uses the renderer backend. |
| `uv_tex` | UV texture map | Requires SciPy plus the UV config assets. |
| `pose` | Pose box overlay | Prints yaw/pitch/roll values. |
| `ply` | PLY mesh export | Writes mesh files instead of an image. |
| `obj` | OBJ mesh export | Writes colored mesh files instead of an image. |

## Example command shapes

```bash
python <skill-root>/sub-skills/still-image-demo/scripts/run-still-image.py \
  --repo-root <checkout> -- \
  -f <image-path> -o 2d_sparse --show_flag false
```

```bash
python <skill-root>/sub-skills/still-image-demo/scripts/run-still-image.py \
  --repo-root <checkout> -- \
  -f <image-path> -o 3d --onnx --show_flag false
```

## Practical defaults

- Use `configs/mb1_120x120.yml` unless the user asked for a smaller or
  alternate backbone.
- Use `--show_flag false` for headless use.
- Use `--onnx` when the user wants the CPU-friendly acceleration path.
- The repo writes results under `examples/results/` using the input basename and
  the selected output mode.

## Common combinations

- `2d_sparse` or `2d_dense`: quick landmark QA.
- `3d`: most useful visual demo for alignment quality.
- `depth` / `pncc`: render-debugging views.
- `uv_tex`: texture-mapping output that exercises SciPy and BFM UV assets.
- `ply` / `obj`: mesh serialization for downstream tools.
