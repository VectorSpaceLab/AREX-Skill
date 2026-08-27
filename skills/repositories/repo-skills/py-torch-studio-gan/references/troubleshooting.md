# Cross-cutting troubleshooting for PyTorch-StudioGAN

## When to read

Read this when StudioGAN does not import, a checkout is missing expected scripts, CUDA is not available, W&B/logging blocks a run, pretrained metric weights download unexpectedly, or StyleGAN custom ops fail. For workflow-specific errors, also read the nearest sub-skill troubleshooting page.

## Script-first checkout issues

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `python: can't open file 'src/main.py'` or `src/evaluate.py` | The command is not pointed at a StudioGAN checkout. | Use this skill's helpers with `--repo-root /path/to/PyTorch-StudioGAN`. Confirm that checkout contains `README.md`, `src/main.py`, `src/evaluate.py`, and `src/config.py`. |
| `ModuleNotFoundError: config`, `loader`, `utils`, `metrics`, or `models` | The script is not run with the checkout's `src/` import root available. | Run native commands from the StudioGAN checkout or set `PYTHONPATH` to include its `src/`. The bundled helpers add the path internally when validating configs. |
| No package version or `pip show` result | StudioGAN has no normal package metadata. | Treat the Git checkout state and `src/` files as the version baseline; use `references/repo-provenance.md` for the distilled snapshot. |

## Dependency/import issues

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError` for `yaml`, `h5py`, `kornia`, `sklearn`, `wandb`, `pyspng`, `timm`, or similar | Runtime dependencies from the README are missing. | Install only the dependencies needed by the selected workflow. Use `scripts/check_studiogan_environment.py --repo-root ...` to list missing imports before a long run. |
| `ModuleNotFoundError: sklearn` after installing `sklearn` fails | The maintained package is `scikit-learn`; it imports as `sklearn`. | Install `scikit-learn`. |
| TensorFlow import errors from `src/metrics/ins_tf13.py` | That file is a legacy TensorFlow 1.3-era metric path. | Prefer the current PyTorch metrics in `src/evaluate.py` and `src/metrics/`. Install TF1 only for an explicit legacy reproduction task. |

## CUDA and distributed runtime issues

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `torch.cuda.is_available()` is false or `torch.cuda.current_device()` fails | CPU-only PyTorch, unavailable GPU passthrough, or driver/wheel mismatch. | Install a CUDA-enabled PyTorch/TorchVision pair compatible with the user's driver and GPU. Do not treat CPU config checks as proof of training support. |
| `Cannot perform distributed training with a single gpu` | `-DDP` was requested but only one visible GPU is available. | Remove `-DDP` or expose multiple GPUs and ensure `OPTIMIZATION.batch_size` is divisible by world size. |
| DDP command hangs at startup | Missing `MASTER_ADDR`/`MASTER_PORT`, blocked node networking, or mismatched `-tn`/`-cn` across nodes. | Set `MASTER_ADDR` and `MASTER_PORT` before launching, use consistent node counts/ranks, and verify ports between nodes. |
| Analysis flags fail under DDP | StudioGAN rejects visualization, KNN, interpolation, frequency, t-SNE, SeFa, Langevin/DDLS, and CAS with DDP. | Use a single visible GPU or DataParallel-style execution for analysis. Route to `sub-skills/sampling-and-analysis/`. |

## W&B/logging and save paths

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Training prompts for W&B login or fails without an API key | The worker initializes W&B for rank 0. | Decide whether to login, use offline mode according to the user's environment policy, or set project/entity fields explicitly. Do not put tokens in commands or skill files. |
| Output files appear under unexpected folders | StudioGAN creates run-named subdirectories. | Check `logs/`, `checkpoints/`, `statistics/`, `samples/`, and `figures/` under the chosen `-save` root. |
| Long runs overwrite or mix artifacts | Reusing the same save directory and config/run name. | Choose a fresh save root for experiments or archive old checkpoints/statistics before rerunning. |

## Pretrained metric weights and network/cache issues

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Metric run downloads weights or fails on network | Inception, TorchVision, SwAV, DINO, or Swin backbones may load pretrained weights from URLs or torch hub caches. | Confirm network/cache budget before running. If unavailable, use cached `.npz` features/moments when appropriate or postpone metric execution. |
| Tiny fixture FID/PRDC looks nonsensical | Too few samples produce meaningless covariance/neighborhood estimates. | Use tiny data only to verify wiring. Do not report tiny fixture metric values as scientific results. |

## StyleGAN custom op issues

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Failure while setting up a PyTorch plugin such as `bias_act`, `upfirdn2d`, or `filtered_lrelu` | First-time StyleGAN2/3 custom C++/CUDA op compilation needs compatible compiler/toolkit/cache permissions. | Verify CUDA toolkit/compiler availability, PyTorch CUDA version, write access to the extension cache, and GPU architecture support. If compiler installation is out of scope, use a non-StyleGAN config or run on an environment where extensions are already built. |
| `no kernel image is available`, undefined symbols, or ABI errors | Mismatch among GPU compute capability, PyTorch CUDA wheel, compiled extension, and driver/toolkit. | Rebuild extension caches under a matching PyTorch/CUDA stack; do not reuse stale extension cache directories from another GPU or torch version. |

## Where to go next

- Config, dataset, HDF5, and training-command errors: `sub-skills/training-and-configuration/references/troubleshooting.md`.
- Standalone metric input/backbone errors: `sub-skills/evaluation-metrics/references/troubleshooting.md`.
- Checkpoint sampling/analysis errors: `sub-skills/sampling-and-analysis/references/troubleshooting.md`.
