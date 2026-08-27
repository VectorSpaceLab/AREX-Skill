# Environment and installation

## Normal installation

```bash
pip install kornia
python -c "import kornia, torch; print(kornia.__version__, torch.__version__)"
```

For an editable source checkout:

```bash
pip install -e .
```

Kornia in this snapshot targets Python 3.11+ and declares base dependencies on PyTorch, NumPy, packaging, and `kornia-rs`.

## Development commands

Kornia uses Pixi and uv for development tasks:

```bash
pixi install
pixi run test
pixi run test-quick
pixi run lint
pixi run typecheck
pixi run doctest
pixi run build-docs
```

Tests run through `uv run pytest` in the repository's Python environment. Device and dtype can be selected through environment variables or pytest flags:

```bash
KORNIA_TEST_DEVICE=cuda KORNIA_TEST_DTYPE=float32 pixi run test
KORNIA_TEST_RUNSLOW=true pixi run test-slow
```

## Optional dependency groups

| Surface | Optional requirements |
| --- | --- |
| ONNX export/runtime | `onnx`, `onnxruntime`, `onnxscript`. |
| Docs | Sphinx/furo/docs extensions plus optional visualization libraries. |
| Multi-framework transpilation | Ivy plus the selected TensorFlow/JAX/NumPy runtime. |
| Model/application extras | May need `transformers`, `diffusers`, Pillow, or cached pretrained weights depending on the model. |
| Benchmarks | OpenCV, torchvision, albumentations, Pillow, and other comparison libraries when running cross-library benchmark scripts. |

Do not install every extra by default. Choose the smallest set required by the selected task and backend.

## Backend policy

- CPU is the baseline correctness backend.
- CUDA and MPS are accelerators; verify them with a tensor allocation and a selected Kornia operation before claiming support.
- Half precision is partial. Keep low-precision validation separate from standard float32/float64 checks, especially on CUDA.
- MPS has known gaps around float64, complex dtypes, some `grid_sample` modes, and autocast behavior.
- CUDA TF32 can affect geometry/camera numerical tests; use documented test flags rather than silently relaxing tolerances.

## Suggested verification commands

Use targeted checks before broad suites:

```bash
python scripts/kornia_environment_probe.py --check-optional
python scripts/kornia_api_smoke.py --device auto
python sub-skills/image-processing/scripts/processing_smoke.py --device auto
python sub-skills/augmentation-pipelines/scripts/augmentation_smoke.py --device auto
python sub-skills/geometry-vision/scripts/geometry_smoke.py --device auto
python sub-skills/features-and-matching/scripts/matching_smoke.py --device auto
python sub-skills/losses-and-metrics/scripts/loss_metric_smoke.py --device auto
python sub-skills/models-and-deployment/scripts/optional_dependency_probe.py
```

For repository maintenance, use focused native tests after the generated guidance is understood, for example `pixi run test` or a target-specific test invocation chosen for the module under repair. Avoid full slow/pretrained/network or benchmark runs unless the task requires them.
