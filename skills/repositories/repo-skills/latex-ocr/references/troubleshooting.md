# Cross-Cutting Troubleshooting

Read this when `pix2tex` fails before you know which workflow owns the problem.
Then follow the route to the nearest sub-skill for deeper guidance.

## Install and Import Failures

| Symptom | Likely cause | Recovery |
|---|---|---|
| `ModuleNotFoundError: pix2tex` | Package not installed in the active Python environment. | Install `pix2tex` or an editable checkout, then run `python -c "import pix2tex"`. |
| `ModuleNotFoundError` for FastAPI, Streamlit, PyQt, torchtext, or imagesize | Optional extra missing. | Use the focused extra: `pix2tex[api]`, `pix2tex[gui]`, or `pix2tex[train]`. |
| `timm`, `torchvision`, or `torch` import errors | Incompatible PyTorch/TorchVision wheel variants or Python version. | Install a matching CPU or CUDA PyTorch/TorchVision pair from the same index; rerun the root environment checker. |
| Albumentations/Pydantic warnings during imports | Modern dependency versions emit non-fatal serialization/update warnings. | Treat as warning if imports still complete; pin older compatible dependencies only when runtime behavior breaks. |
| Model weights download starts unexpectedly | Instantiating `LatexOCR()` downloads missing checkpoints. | Run helper checks first; instantiate only when network/download and compute are acceptable or pass an existing checkpoint path. |

## Backend and Runtime Decisions

- CPU inference is supported with `--no-cuda` or an arguments object where
  `no_cuda=True`. Use CPU for deterministic smoke checks when speed is not the
  objective.
- CUDA is optional for speed/training. Verify `torch.cuda.is_available()` and a
  small tensor allocation in the target environment before relying on GPU.
- GUI workflows require desktop and Qt dependencies; API workflows require API
  extras; rendering formulas into PNGs requires system TeX/ImageMagick tooling;
  training requires datasets, checkpoints, and often GPU memory planning.

## Safe Diagnostics

Run:

```bash
python path/to/latex-ocr/scripts/check_pix2tex_environment.py --check-api
```

The script checks imports and CLI availability without loading model weights,
starting a server, launching the GUI, or training.
