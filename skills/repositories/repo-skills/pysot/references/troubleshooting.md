# PySOT Troubleshooting

## When to read

Use this root troubleshooting reference for install/import/backend failures that affect multiple PySOT workflows. For config-specific, tracking, training-data, or evaluation-specific failures, read the nearest sub-skill troubleshooting reference after this one.

## Import failures

### `ModuleNotFoundError: No module named 'pysot'`

Likely causes:

- The `toolkit` distribution was installed, but the main `pysot` package is not on `sys.path`.
- The command is running outside the intended checkout/import context.

Recovery:

1. Confirm the environment can see the checkout root or equivalent editable registration.
2. Run:

   ```bash
   python scripts/check_env.py --repo-root <pysot-checkout>
   ```

3. If only evaluating result files and no `pysot` import is needed, the toolkit may still work; for tracking/training/model workflows, fix `pysot` import first.

### `ImportError: cannot import name region` or `No module named toolkit.utils.region`

Likely causes:

- The Cython extension was not built.
- Build isolation could not see Cython.
- Cython 3.x is incompatible with the legacy extension code.

Recovery:

1. Install Cython in the target environment; prefer `Cython<3` for this repository.
2. Build/install the toolkit extension in a controlled environment.
3. Verify:

   ```bash
   python -c "from toolkit.utils.region import vot_overlap; print(vot_overlap([0,0,10,10], [0,0,10,10], (20,20)))"
   ```

4. Route evaluation-specific region failures to `sub-skills/evaluation-toolkit/references/troubleshooting.md`.

## Dependency/version failures

### PyTorch/CUDA mismatch

Symptoms include `torch.cuda.is_available() == False`, `no kernel image is available`, CUDA driver/runtime errors, or source scripts failing at `.cuda()`.

Recovery:

- Decide whether the requested task really needs CUDA. CPU preflight checks do not.
- For unmodified `tools/test.py`, `tools/train.py`, and `tools/hp_search.py`, assume CUDA is required unless the user explicitly adapts the source workflow.
- Match Python, PyTorch, CUDA runtime, driver, and GPU architecture. Historical PySOT docs refer to older PyTorch/CUDA combinations; modern GPUs may require newer wheels and code adaptation.
- Do not claim a full GPU workflow is verified just because config/model construction passed on CPU.

### NumPy/OpenCV compatibility

PySOT source uses older NumPy idioms in some paths. If a runtime path fails with deprecated aliases or OpenCV image handling errors:

- Prefer an environment with NumPy compatible with the code path, often `<1.24` for legacy aliases.
- Confirm OpenCV imports with `python -c "import cv2; print(cv2.__version__)"`.
- For headless servers, avoid GUI demo calls unless OpenCV has display support or the workflow is adapted to save output without `imshow`/`selectROI`.

## Asset/data failures

### Missing model snapshot

Symptoms include file-not-found errors, state-dict load failures, or zero checkpoint keys used.

Recovery:

- Validate the snapshot path before running tracking:

  ```bash
  python sub-skills/tracking-inference/scripts/validate_tracking_inputs.py --config <config.yaml> --snapshot <model.pth>
  ```

- Ensure the snapshot matches the config family (backbone, RPN head, mask/refine, tracker type).
- Read `sub-skills/configuration-models/references/model-zoo.md` for naming and suffix guidance.

### Missing benchmark/training datasets

Benchmark/evaluation/training commands often assume external directories and JSON sidecars. Do not download large datasets automatically. Use the relevant safe validator first:

```bash
python sub-skills/training-data/scripts/validate_training_config.py --repo-root <pysot-checkout> --config <config.yaml> --check-files
python sub-skills/evaluation-toolkit/scripts/validate_results_layout.py --tracker-path <results> --dataset <dataset> --tracker-prefix <prefix>
```

## Workflow routing after a failure

- Config key, `TRACK.TYPE`, anchor, `RPN.KWARGS`, snapshot/config mismatch: `sub-skills/configuration-models/`.
- Demo/video/snapshot loading, tracker API, `tools/test.py` command construction: `sub-skills/tracking-inference/`.
- Training datasets, crop/annotation JSON, distributed launch, `size not match!`: `sub-skills/training-data/`.
- `eval.py`, tracker result tree, metrics, region-extension at evaluation time, hp-search outputs: `sub-skills/evaluation-toolkit/`.
