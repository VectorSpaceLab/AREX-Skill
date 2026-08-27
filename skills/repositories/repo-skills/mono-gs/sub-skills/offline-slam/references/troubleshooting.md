# Troubleshooting

## Common offline-SLAM failures

| Symptom | Likely cause | Safe response |
| --- | --- | --- |
| `slam.py` cannot open the config or an inherited base YAML | The config path is wrong, the repo root is wrong, or an `inherit_from` file is missing | Re-run `scripts/plan_slam_run.py --check-files` and fix the config path before launching SLAM. |
| `ModuleNotFoundError` for `simple_knn._C` or `diff_gaussian_rasterization` | The CUDA extensions were not built in the active environment | Reinstall the CUDA runtime environment and rebuild the repo extensions before retrying. Offline SLAM has no CPU-only substitute. |
| CUDA tensor allocation fails or `torch.cuda.is_available()` is false | Wrong PyTorch/CUDA stack or no visible GPU | Stop and fix the environment; this workflow requires CUDA. |
| GUI window does not appear or the run hangs on a remote/headless machine | GUI was left on, or the session has no display path | Use `--eval` for a headless plan, or prepare a config copy with `Results.use_gui: false`. Do not add a runtime `--headless` flag; `slam.py` does not have one. |
| Replica run feels only partly serialized | `Training.single_thread` and `Dataset.single_thread` disagree | Use the shipped `_sp` config variant when you want the backend-side serialized path. The code still uses spawned processes either way. |
| Stereo EuRoC depth is empty or unstable | The stereo config is wrong, the left/right pair is missing, or calibration/layout is broken | Verify the EuRoC stereo config family and route deeper data-layout checks to `data-and-configs`. |
| Monocular TUM keeps reinitializing | Poor overlap, bad frame pairing, or a mismatch between the selected config and the dataset | Confirm that you chose a monocular TUM config and that the dataset pairings exist. |
| No result tree or point cloud appears after a run | `Results.save_results` is false, or the run never reached the save path | Use a config that saves results or add `--eval`, which forces result saving. |
| W&B setup becomes a blocker during evaluation | `--eval` forces `use_wandb: true` | If you only need a local preview, avoid `--eval` and use a config copy instead. |
| The command looks like a live camera workflow | A `configs/live/*` file was selected | Stop and route the task to `live-demo`; live RealSense runs are not offline SLAM. |

## Checklist before long runs

1. Confirm the config family matches the sensor type.
2. Confirm CUDA and the two compiled extensions are already available.
3. Confirm the dataset path exists if you asked for `--check-files`.
4. Choose GUI or headless behavior intentionally.
5. Prefer the Replica `_sp` config when you need the serialized variant.
