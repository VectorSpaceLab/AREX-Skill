# Cross-cutting troubleshooting

Use the focused sub-skill first; this page covers issues that cross installation, data, model, and output boundaries.

| Symptom | Likely cause | Action |
| --- | --- | --- |
| `ModuleNotFoundError` for `torch`, `torchvision`, `skimage`, `dominate`, or `wandb` | The environment does not match the documented runtime baseline. | Run `scripts/check_env.py --repo-root TARGET_CHECKOUT`; install only the missing dependency in an isolated environment. The current visualizer imports W&B at module import time. |
| Repo modules import from an unexpected Python or checkout | An unqualified `python`/`pip` or a stale shell import override is being used. | Run the check with the intended isolated environment and `--repo-root`; inspect the interpreter and module locations before running train/test. |
| CUDA is visible in `nvidia-smi` but PyTorch reports unavailable | CPU wheel, incompatible driver/wheel, or missing GPU passthrough. | The current parser has no `--gpu_ids` flag. Use a CPU-only PyTorch environment or prefix a Linux command with `CUDA_VISIBLE_DEVICES=` to hide GPUs; otherwise install a compatible CUDA build and rerun `scripts/check_env.py --require-cuda`. Do not claim CUDA support from hardware visibility alone. |
| Training imports succeed but data loader fails | `--dataset_mode`, `--phase`, or `--dataroot` does not match the directory layout. | Run `data-preparation/scripts/validate_layout.py` for the selected mode and phase. |
| Training creates no usable result or checkpoint | Experiment name/path collision, too-short run, `--no_html`, or save cadence larger than the smoke run. | Use a fresh `--name`, lower `--save_latest_freq`/`--save_epoch_freq` for a tiny smoke, and check the configured checkpoint/result roots. |
| Testing fails to load a checkpoint | Architecture/default mismatch or wrong `--name`, `--epoch`, `--load_iter`, or `--model_suffix`. | Follow `translation-workflows/references/troubleshooting.md`; repeat the training architecture flags explicitly at test time. |
| Paired data produces reversed results | Side-by-side A/B orientation and `--direction` disagree. | Confirm left half is A and right half is B; use `AtoB` or `BtoA` deliberately. |
| The pair combiner refuses to run | Missing A/B filenames, unequal image sizes, existing output, or unsupported extension. | Use `data-preparation/scripts/combine_pairs.py --dry-run`; fix the first reported mismatch or pass `--overwrite` only after confirming the output is disposable. |
| Network asset download stalls or leaves a partial directory | Archive/network/URL/license problem. | Do not retry blindly. Confirm the exact allowlisted asset, destination, free space, license, and whether a synthetic/local fixture is sufficient. |
| Cityscapes or HED workflow asks for Caffe/MATLAB | Optional external workflow is being treated as core. | Read `data-preparation/references/advanced-external-workflows.md`; keep the required scope CPU-only unless the user explicitly provides the external backend and accepts the verification cost. |

## Current-source caveats worth checking before a long run

- The source parser accepts `syncbatch`, while some repository prose spells synchronized normalization differently. The DDP setup guard around `syncbatch` is contradictory; perform a bounded setup smoke before a multi-process run.
- The source `datasets/combine_A_and_B.py` imports OpenCV and references `Path` without importing it. Prefer the bundled Pillow adapter rather than relying on that source helper.
- Legacy docs mention visdom, but the current main code path saves HTML and uses W&B; verify the actual checkout before installing or starting a visdom server.
