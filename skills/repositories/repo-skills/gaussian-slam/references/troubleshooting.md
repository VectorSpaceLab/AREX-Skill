# Cross-cutting troubleshooting

Read this when installation, imports, paths, outputs, logging, or evaluation
fails before choosing a recovery.

| Symptom | Likely cause | Safe check and recovery |
|---|---|---|
| `ModuleNotFoundError: simple_knn._C` or `gaussian_rasterizer` | Pinned CUDA extension was not built for the active Python/Torch/CUDA ABI | Run `scripts/check_env.py`; verify the active Torch version, `torch.version.cuda`, `nvcc`, host compiler, and GPU architecture. Rebuild both extensions together with the active environment; do not replace them with CPU packages. |
| `torch.cuda.is_available()` is false | CPU-only Torch, missing driver passthrough, incompatible CUDA runtime, or hidden device | Run the target environment's Torch CUDA smoke and `nvidia-smi`. Install a documented compatible CUDA Torch variant or fix device exposure before using SLAM. |
| CUDA compile says unsupported GNU version or ABI/header errors | nvcc/compiler mismatch, wrong C++ standard, or newer system headers | Match compiler/toolkit to the repository's Torch/CUDA pins; use a supported `CC`/`CXX`, `nvcc`, `-std=c++17`, and an architecture target supported by the GPU. Treat temporary compatibility patches as build diagnostics, not runtime skill dependencies. |
| `FileNotFoundError` for inherited YAML | `inherit_from` is resolved from the process working directory by the source loader | Run the bundled config validator, launch from the repository root, or use a config whose inheritance paths resolve from that working directory. Keep explicit input/output overrides. |
| Unsupported dataset / missing `rgb.txt`, `results`, `color`, `depth`, or pose files | Wrong case-sensitive alias or dataset layout | Use `datasets-and-configuration`; exact aliases are `replica`, `tum_rgbd`, `scan_net`, `scannetpp`. Validate paired files and scene metadata before a GPU run. |
| TUM sequence has unexpectedly few frames | RGB/depth/pose timestamps fail the 0.08-second association threshold or 32 FPS sampling | Inspect timestamps and pose source (`groundtruth.txt` or `pose.txt`); fix data association or accept the reduced frame set, then record it. |
| ScanNet++ key error for split/camera metadata | Missing `dslr/train_test_lists.json`, transforms JSON, or selected split image | Validate the selected train/test split and exact file paths; do not silently switch `use_train_split`. |
| Output says `All done.✨` but metrics are missing | `Evaluator.run()` catches each stage exception and continues | Check `estimated_c2w.ckpt`, `submaps/`, and each expected metric file. Read the first traceback; classify the failed stage rather than treating the final line as success. |
| W&B login/network/path error | `use_wandb` enabled, credentials absent, network unavailable, or source's hard-coded run directory is unwritable | Set `DISABLE_WANDB=true` or `use_wandb: False` for local work. If online tracking is required, patch the run directory to a writable location and configure credentials separately. |
| Out of memory during mapping/rendering | Large frame resolution, point seeding counts, mapping iterations, or competing GPU jobs | Preserve the partial output, reduce only diagnostic `frame_limit`, point sample, resolution, or iterations in a new output directory, and label the result as a smoke test—not paper reproduction. |
| Replica mesh/reconstruction stage skipped or fails | Reconstruction is implemented only for `dataset_name: replica`, needs Replica ground truth, headless Open3D, and `evaluate_3d_reconstruction` | Verify dataset and ground-truth assets; use headless Open3D on clusters. A non-Replica skip is expected, not a failed SLAM run. |
| Evaluation can render but global-map/NVS fails | Missing submaps, FAISS-GPU, or ScanNet++ test split; global-map NVS is only supported for ScanNet++ | Validate checkpoint artifacts and dependencies, then run only the supported stage. Do not infer NVS metrics for other datasets. |
| Warnings about nondeterministic metrics | Differential Gaussian rasterizer is nondeterministic | Compare seeds/runs with tolerance and record GPU, driver, config, and extension build. Do not claim bitwise reproducibility. |

Never delete partial outputs while diagnosing. Use a fresh output path for each
recovery and preserve the effective config and logs.
