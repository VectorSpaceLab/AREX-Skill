# Cross-cutting troubleshooting

Read this when a docTR task fails before the issue clearly belongs to a specific sub-skill.

## Package import fails

Symptoms:

- `ModuleNotFoundError: No module named 'doctr'`
- `PackageNotFoundError: python-doctr`
- `ImportError` from core dependencies such as `torch`, `cv2`, `pypdfium2`, `pyclipper`, `shapely`, `anyascii`, or `huggingface_hub`.

Actions:

1. Verify the active Python environment:
   ```bash
   python -m pip show python-doctr
   python - <<'PY'
   import doctr
   print(doctr.__version__)
   PY
   ```
2. If missing, install the base package: `pip install python-doctr`.
3. Run the root diagnostic: `python scripts/doctr_env_check.py --json`.
4. If imports fail after installation, run `python -m pip check` and reinstall into the same environment that will run OCR.

## Optional extra is missing

| Symptom | Likely missing extra | Recovery |
|---|---|---|
| `result.show()` / `page.show()` cannot import matplotlib/mplcursors | `viz` | `pip install "python-doctr[viz]"` |
| `DocumentFile.from_url(...)` or HTML conversion fails around WeasyPrint | `html` | `pip install "python-doctr[html]"` and verify system libraries required by WeasyPrint if needed |
| `ArtefactDetector` or ONNXRuntime-backed contrib path fails | `contrib` | `pip install "python-doctr[contrib]"` |
| FastAPI/Streamlit demo imports fail | demo/API requirements | Treat as optional deployment; read [deployment-and-contrib](../sub-skills/deployment-and-contrib/SKILL.md) before installing service stacks |

Do not install `dev` or all extras just to fix one optional feature.

## Pretrained weights or network/cache problems

Symptoms:

- First `pretrained=True` run downloads weights.
- Offline jobs hang or fail during model construction.
- A cache file is corrupt or a URL is blocked.

Actions:

1. Confirm whether the task needs real OCR accuracy. If it is only a parser/API smoke check, use `pretrained=False` and record that output is random/unusable.
2. If real OCR is needed, allow network or pre-populate the model cache according to the user's environment policy.
3. If the cache is corrupt, remove only the failing model file and retry with authorization; do not delete unrelated user caches.
4. Keep construction-time cache paths out of generated reports or user-facing artifacts.

## Input file or image shape failures

Symptoms:

- File not found from `doctr-cli`.
- PDF/image decode errors.
- NumPy array shape/dtype errors.
- Poor OCR from grayscale/BGR images.

Actions:

1. For file loading/export behavior, read [document-io-and-exports](../sub-skills/document-io-and-exports/SKILL.md).
2. Ensure images are RGB `uint8` arrays shaped `(H, W, C)` or valid image/PDF paths.
3. Convert grayscale arrays to 3 channels and OpenCV BGR arrays to RGB before prediction.
4. For CLI output path failures, ensure the parent directory exists and the output path is a file, not a directory.

## Device, CUDA, MPS, and precision failures

Symptoms:

- `torch.cuda.is_available()` is false despite expecting GPU.
- `no kernel image is available`, CUDA driver/runtime mismatch, or missing NVIDIA libraries.
- Half precision produces CPU errors or unstable output.
- MPS is requested on non-macOS hardware.

Actions:

1. Run `python scripts/doctr_env_check.py --json --probe-gpu-commands`.
2. For ordinary OCR correctness, fall back to CPU unless the user explicitly needs device performance.
3. Use GPU/MPS only after verifying the framework backend and moving the predictor/model to the selected device.
4. Use BF16/FP16 only on supported GPU devices; keep CPU inference in FP32.
5. For multi-GPU training, use a launcher such as `torchrun` only after confirming CUDA/NCCL and dataset smoke checks.

## Wrong route or output interpretation

- If the user has `DocumentFile`, export formats, reading order, hOCR, Markdown, tables, or KIE page structures: route to [document-io-and-exports](../sub-skills/document-io-and-exports/SKILL.md).
- If the user has architecture names, custom checkpoints, vocabs, Hub, ONNX, compile, device precision: route to [models-and-customization](../sub-skills/models-and-customization/SKILL.md).
- If the user has labels, custom datasets, training, evaluation, metrics, DataLoader, DDP: route to [datasets-training-and-evaluation](../sub-skills/datasets-training-and-evaluation/SKILL.md).
- If the user has `doctr-cli`, batch OCR, output files, or command parsing: route to [cli-and-scripts](../sub-skills/cli-and-scripts/SKILL.md).
- If the user has FastAPI/Streamlit/Docker/contrib/Hub publishing: route to [deployment-and-contrib](../sub-skills/deployment-and-contrib/SKILL.md).

## When to stop and ask

Ask before:

- installing broad extras, dev stacks, demo/API service requirements, or GPU-specific packages,
- deleting caches or overwriting output/checkpoint directories,
- starting long training/evaluation/benchmark runs,
- launching services, exposing ports, building/running Docker images,
- downloading large datasets/weights when network/cost policy is unclear,
- using credentials or pushing to Hugging Face Hub.
