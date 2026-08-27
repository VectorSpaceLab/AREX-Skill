# Outputs and Export Dependencies

## Workspace Layout

`main.py` rewrites the user-supplied workspace name as:

```python
opt.workspace = os.path.join('results', opt.workspace)
```

So `--workspace corgi` writes under `results/corgi` in the runtime working directory.

Expected output categories:

| Output | Source owner | Purpose |
| --- | --- | --- |
| `setting.txt` | `main.py` | Captures parsed options for the run. |
| `checkpoints/` | `Trainer` | Stores latest/best model checkpoints. |
| `log_df.txt` | `Trainer` | Training log for the experiment name `df`. |
| `train/` and validation/test renders | `Trainer` | Intermediate and final rendered images/videos. |
| DPT depth PNGs | `main.py` + `DPT.util.io.write_depth_name` | Depth prior visualization/normalization input. |
| `mvimg/` | refine path | Multi-view images used by refinement. |
| OBJ/MTL/albedo files | mesh export path | Textured mesh output when `--save_mesh` succeeds. |

## Mesh Export Dependency Chain

The mesh export path in `nerf/renderer.py` performs:

1. density grid query;
2. marching cubes via `mcubes`;
3. UV unwrap with `xatlas`;
4. CUDA rasterization with `nvdiffrast.torch`;
5. nearest-neighbor texture padding with scikit-learn;
6. image writes with OpenCV;
7. OBJ/MTL/texture file creation.

If any dependency is missing, provide a targeted recovery step rather than rerunning training.

## Point-Cloud/Refinement Dependency Chain

The refinement utilities convert depth and multi-view predictions into point representations and use PyTorch3D point rasterization/compositing. They also rely on OpenCV, NumPy, imageio, and Open3D-oriented output paths.

## Resuming After Interruption

Do not delete a workspace after an interruption until you inspect:

- whether a recent checkpoint exists;
- whether `setting.txt` matches the intended flags;
- whether `log_df.txt` ended during training, testing, refine, or export;
- whether partially generated `mvimg` frames or mesh files exist.

Use the same workspace and `--ckpt latest` to resume when checkpoint state is valid. Use a new workspace or `--ckpt scratch` for a clean rerun.
