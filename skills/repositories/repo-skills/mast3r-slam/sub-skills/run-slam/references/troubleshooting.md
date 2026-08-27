# Runtime Troubleshooting

## When to read

Read this when command construction, dataset loading, calibration, visualization,
or output saving fails after the environment is already installed.

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `No calibration provided for this dataset!` | `use_calib` was true but the loader did not have intrinsics and no valid `--calib` file was supplied | Use a no-calibration config, choose a supported dataset with built-in intrinsics, or supply a valid calibration YAML. |
| A generic folder is treated as TUM/EuRoC/ETH3D/7-Scenes | Dataset selection is based on path tokens | Rename/move the folder or pass a path without reserved tokens; run `validate_inputs.py`. |
| Video loading is slow | `torchcodec` is not installed | Install `torchcodec==0.1` only if MP4 decoding is the bottleneck; OpenCV fallback is valid. |
| OpenGL/GLFW/window errors | Visualization needs a display context and the in3d/ModernGL stack | Use `--no-viz` for headless runs, SSH, CI, or evaluation. |
| `Skipped frame` appears repeatedly | Too few valid matches for tracking thresholds | Check input quality, motion blur, frame sampling, config thresholds, and whether calibration is mismatched. |
| `Cholesky failed` | Pose optimization became numerically unstable | Check calibration, match confidence thresholds, frame overlap, and whether the scene is degenerate. |
| `Failed to relocalize` | Retrieval found candidates but factor graph constraints were not strong enough | Inspect frame quality and `retrieval.*` / `reloc.*` config settings. |
| No trajectory/PLY is written | Dataset has `save_results=False` or run terminated before completion | Live RealSense/webcam paths intentionally do not save results by default. For datasets/videos/folders, check `--save-as` and run completion. |
| Missing checkpoint or MASt3R model load error | Assets are not staged | Route to `setup-and-backends` and verify checkpoint filenames. |

## Safe escalation

1. Re-run `scripts/run_mast3r_slam.py --dry-run` and inspect the command.
2. Re-run `scripts/validate_inputs.py --strict` on the dataset/calibration.
3. Re-run the root `scripts/check_install.py --check-cuda` if imports or CUDA
   errors appear.
4. Use `--no-viz` to separate SLAM runtime errors from visualization errors.
5. For benchmark loops and `evo_ape` issues, switch to `evaluation`.
