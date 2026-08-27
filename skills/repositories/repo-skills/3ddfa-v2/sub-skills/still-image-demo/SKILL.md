---
name: "still-image-demo"
description: "Run 3DDFA_V2 still-image alignment, rendering, pose, texture, and
  mesh export workflows."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# Still-image demo

Use this sub-skill for `demo.py` workflows on a single image: sparse or dense
landmarks, 3D renderings, depth, PNCC, UV texture, pose boxes, and PLY/OBJ mesh
exports.

## When to read

Read this sub-skill when the task asks to:

- Run 3DDFA_V2 on a still image.
- Generate `2d_sparse`, `2d_dense`, `3d`, `depth`, `pncc`, `uv_tex`, `pose`,
  `ply`, or `obj` outputs.
- Use `--onnx` for a single-image demo.
- Diagnose `No face detected`, missing result files, headless plotting, or
  mode-specific failures.

## Before running

1. Use `../setup-and-assets/` if native extensions or checkpoints are not known
   to be ready.
2. Check `../../references/model-assets.md` when switching configs or missing
   weight files.
3. In headless environments, keep `--show_flag false`; the bundled wrapper also
   sets a headless plotting backend.

## Main wrapper

The bundled wrapper preserves the original `demo.py` CLI. Put original demo
arguments after `--`:

```bash
python <skill-root>/sub-skills/still-image-demo/scripts/run-still-image.py \
  --repo-root <checkout> -- \
  -f <image-path> -o 3d --show_flag false --onnx
```

Use direct repo commands only when you already applied the same compatibility
and headless setup the wrapper provides.

## Output selection

Read `references/workflows.md` for the full output-mode table. The highest-use
choices are:

- `2d_sparse` for 68-point landmark overlays.
- `2d_dense` for dense landmark visualization.
- `3d` for rendered dense mesh overlay.
- `depth`, `pncc`, and `uv_tex` for specialized per-pixel visual products.
- `pose` for yaw/pitch/roll pose-box visualization.
- `ply` and `obj` for mesh serialization.

Outputs default to `examples/results/` and use the input basename plus the
selected option.

## Decision points

- Prefer `--onnx` for CPU latency and when the `.onnx` assets are already
  present or can be auto-converted.
- Use `configs/mb05_120x120.yml` when the task values speed over the default
  backbone.
- Use dense reconstruction for `3d`, `depth`, `pncc`, `uv_tex`, `ply`, and
  `obj`; sparse mode is enough for `2d_sparse` and `pose`.
- If the user needs multi-frame tracking, route to `../video-and-tracking/`.
- If the user asks about latency numbers rather than a saved image, route to
  `../onnx-and-benchmarking/`.

## Troubleshooting

Read `references/troubleshooting.md` for still-image-specific failures and
`../../references/troubleshooting.md` for shared build/import failures.
