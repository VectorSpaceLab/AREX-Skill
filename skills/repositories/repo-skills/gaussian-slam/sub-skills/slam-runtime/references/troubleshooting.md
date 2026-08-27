# Runtime troubleshooting and recovery

Classify the first error before changing the experiment. Keep the original log,
effective `config.yaml`, and partial output. Recovery should use a fresh output
path unless a deliberate, source-supported resume procedure is available.

| Symptom | Likely cause | Safe check | Recovery |
|---|---|---|---|
| `torch.cuda.is_available()` is false, or tensors fail at `.cuda()` | CPU-only Torch, hidden GPU, or bad driver/runtime | `nvidia-smi`; print Torch CUDA/version/device capability | Activate a CUDA environment and repair the driver/Torch pairing. There is no CPU substitute. |
| `No module named simple_knn._C` | Pinned `simple-knn` extension absent or built for another ABI | `python -c 'import simple_knn._C'` | Build/install the pinned extension with a compatible compiler, CUDA toolkit, Torch ABI, and target GPU architecture. |
| `No module named gaussian_rasterizer` or rasterizer launch failure | Custom rasterizer absent or incompatible | `python -c 'import gaussian_rasterizer._C'`; run the repo help command | Rebuild the pinned rasterizer for the active stack/GPU. Do not replace it with a CPU renderer. |
| `no kernel image is available` / illegal instruction in an extension | Extension was not compiled for the GPU's compute capability | Print `torch.cuda.get_device_capability()` and inspect the build target | Rebuild for the host architecture. SM80/A100 is verified; other architectures require their own check. |
| `FileNotFoundError` for an inherited YAML | `inherit_from` is relative to the current working directory | Run the CLI checker; print current directory and config path | Launch from repository root or fix the path in a copied config. Use explicit scene/input/output overrides. |
| `KeyError: data` or missing `scene_name`/camera key | A base dataset config was used without a scene overlay | Check merged-config report and required keys | Use a scene config and obtain the dataset contract from the dataset skill. |
| Output path is absent, unexpectedly timestamped, or mixed with old files | Missing explicit `data.output_path` or reused directory | Check effective `config.yaml` and directory timestamps | Always pass a unique `--output_path`; preserve the old directory and rerun separately. |
| CUDA out of memory during first mapping or point growth | Large point seed, high image resolution, competing jobs, or large submap | `nvidia-smi`; inspect `new_submap_points_num`, image size, and iteration settings | Stop the failed run, reduce diagnostic point/iteration settings in a copied config or request more VRAM, and use a new output. A reduced run is not a reproduction. |
| CUDA out of memory during tracking | High tracking iterations or unusually large Gaussian model | Inspect initial loss/iteration messages and memory usage | Reduce tracking iterations for diagnosis, close competing work, or use a larger GPU; keep the change recorded. |
| Tracking starts with high loss and doubles iterations | Initial pose estimate is poor relative to prior losses | Inspect `Higher initial loss` and configured `init_err_ratio` | Use the configured odometer initialization aid where appropriate, check RGB-D synchronization through the dataset skill, and rerun with a recorded config. |
| Pose tracking diverges after changing `--gt_camera` | The flag is parsed but ignored | Inspect saved `config.yaml`; it will not show an odometry change from this flag | Set `tracking.odometry_type: gt` in YAML only when ground truth is intentionally requested. Do not claim a CLI override worked. |
| `--track_w_color_loss` appears to have no effect | Parsed but not copied into config | Compare saved `config.yaml` with the command | Edit `tracking.w_color_loss` in YAML and rerun with a fresh output. |
| A zero CLI override has no effect | Several assignments are guarded by truthiness | Check `--seed 0`, `--map_every 0`, or `--track_cam_trans_lr 0` cases | Use YAML for zero values; use a positive value only when semantically valid. |
| W&B login/network/permission or run-directory error | W&B enabled, unavailable network, missing auth, or source's site-specific absolute directory | Inspect `use_wandb`, `DISABLE_WANDB`, and W&B error; do not expose credentials | Set `DISABLE_WANDB=true` for local execution. If logging is required, patch the run directory to a writable site path and choose online/offline policy explicitly. |
| `All done.✨` but a metric/mesh/global-map file is missing | Evaluator catches phase errors and continues | Read the traceback and list output files | Treat only the affected evaluation phase as failed; validate pose/submap artifacts independently. |
| No final submap for the last frame | Active model is not explicitly finalized after the main loop, especially at a boundary | Inspect boundary IDs and `submaps/` against the effective config | Consume only completed prior submaps; preserve output and report incomplete finalization. Do not fabricate or silently merge it. |
| SLURM array element selects wrong scene or config | Fixed source array, scene list mismatch, or ScanNet++ case mismatch | Review planner output, array bounds, and config paths with `--check-files` | Regenerate a plan with explicit scenes and corrected config directory; manually review before submission. |
| SLURM command behaves as if `echo`/another line were an argument | Trailing `\\` after the last command argument in the source template | Print the batch file with line numbers and inspect shell continuation | Remove the final continuation; use the planner's command shape. |
| Partial output after preemption or kill | No general resume flag in the entry point | Check log end and last complete submap/pose checkpoint | Preserve artifacts, start a new diagnostic/reproduction output, and record whether the source checkpoint is complete enough for downstream use. |

## Hard cases

### Parsed flags disagree with user intent

If a user supplies `--gt_camera --track_w_color_loss 0.1 --seed 0`, do not
translate that into a ground-truth, low-color-loss, seed-zero run. The source
only parses the first two without applying them and ignores the zero seed
assignment. Report the exact effective YAML and request a YAML edit or positive
seed before execution.

### OOM at a submap boundary

A boundary can save the prior checkpoint and then fail while seeding or
optimizing the new submap. Preserve the prior checkpoint and `estimated_c2w`
if present. Classify the run as partial, make a copied low-memory diagnostic
config, choose a fresh output path, and verify that downstream consumers do not
mistake the prior submap for a complete scene map. Never fall back to CPU.
