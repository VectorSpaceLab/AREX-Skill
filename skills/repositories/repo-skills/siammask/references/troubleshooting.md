# Cross-Cutting Troubleshooting

## `ModuleNotFoundError: No module named 'utils'` or `No module named 'models'`

Cause: the legacy repo is not installed as a package and direct script execution sets `sys.path[0]` to the script directory, not the checkout root.

Fix:

1. Prefer bundled wrappers, which prepend the checkout root and selected experiment directory to `PYTHONPATH`.
2. If running manually, set `PYTHONPATH=<siammask-checkout>:<selected-experiment-dir>:$PYTHONPATH` before invoking native Python entry points.

## `ImportError` for `utils.pyvotkit.region`, `utils.pysot.utils.region`, or `_mask`

Cause: local Cython extensions were not built in the checkout or were built with a different Python ABI.

Fix:

```bash
bash scripts/build_extensions.sh --repo-root <siammask-checkout> --python <python-in-your-env>
python scripts/check_environment.py --repo-root <siammask-checkout> --check-cli
```

If the build fails, confirm Cython, NumPy headers, and a C compiler are available in the same environment.

## NumPy alias errors (`np.float`, `np.int`, `np.int0`)

Cause: modern NumPy removed or changed legacy aliases used by this codebase.

Fix: use NumPy `<1.24` for unpatched operation, or patch the checkout consistently before running workflows. Do not mix a patched checkout with an unpatched skill provenance baseline without refreshing the skill.

## Legacy requirements fail to install exactly

Cause: the README/requirements target Python 3.6, PyTorch 0.4.1, CUDA 9.2, and old scientific Python packages. These pins may be unavailable on modern Python or A100-era hosts.

Fix: install the minimum compatible package set for the selected workflow. Use modern PyTorch/CUDA only after verifying imports and CUDA smoke checks. Preserve the exact legacy stack only when reproducing historical results on matching hardware.

## CUDA is missing or unusable

Symptoms:

- `torch.cuda.is_available()` is false.
- Training crashes at `model.cuda()` or `DataParallel(...).cuda()`.
- VOS tuning crashes when moving the model to CUDA.

Fix:

1. Run `python scripts/check_environment.py --repo-root <siammask-checkout> --expect-cuda yes`.
2. Install a CUDA-capable PyTorch build matching the host driver.
3. If no CUDA device is available, restrict work to CPU-capable tracking/evaluation guidance and do not claim training/VOS-tuning backend verification.

## Checkpoint path assertions fail

Symptoms: errors like `Please download <checkpoint> first` or `<path> is not a valid file`.

Fix: decide which family you need in [model-overview.md](model-overview.md), then validate the checkpoint path relative to the selected experiment directory or pass an absolute path to the bundled wrapper. Do not start network downloads without user approval.

## OpenCV GUI problems

Symptoms: demo exits at ROI selection, `cv2.imshow`/`cv2.selectROI` fails, or no display appears.

Fix: run demo mode only in a display-capable session with GUI OpenCV. On headless servers, use non-interactive benchmark/test wrappers, avoid `--visualization`, and validate inputs without opening windows.

## Dataset path errors

Symptoms: missing `list.txt`, `groundtruth.txt`, `ImageSets`, `meta.json`, `crop511`, or train/val JSON files.

Fix:

```bash
python sub-skills/data-preparation/scripts/check_dataset_layout.py --data-root <siammask-checkout>/data --dataset training
```

Then read [sub-skills/data-preparation/references/data-layouts.md](../sub-skills/data-preparation/references/data-layouts.md) for the expected raw and generated layouts.
