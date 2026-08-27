# Installation and compatibility

Fengshenbang-LM is an older ML package. Install it in an isolated environment and verify imports before running models or training.

## Minimal public install pattern

```bash
python -m pip install -e /path/to/Fengshenbang-LM
fengshen-pipeline text_classification predict --help
python -c "import fengshen; from fengshen import LongformerConfig, RoFormerConfig, T5Config; print('ok')"
```

For normal user environments, prefer a fresh Python 3.8-3.10 environment. Avoid repairing a shared or production environment until you know which versions will be changed.

## Compatibility stack observed during skill construction

The package metadata declares broad lower bounds, but live inspection found that unconstrained modern dependencies can break imports. A compatible inspection stack used:

| Package | Compatible example | Why |
|---|---:|---|
| Python | 3.10 | Old enough for the 2022-era ML stack, new enough for current wheels. |
| PyTorch | 2.0.1 CPU for inspection | CPU is enough for imports, CLI help, parser/signature checks. |
| Transformers | 4.20.1 | Provides both legacy `cached_path` and `pytorch_utils.softmax_backward_data`, used by Fengshen ZEN/DeBERTa paths. |
| Datasets | 2.0.0 | Matches the repo's lower bound and CLI import expectations. |
| PyTorch Lightning | 1.9.5 | Still exposes `Trainer.add_argparse_args` used by pipeline parsers. |
| Torchmetrics | 0.11.4 | Compatible with older `Accuracy()` usage. |
| Deepspeed | 0.9.5 for import inspection | Satisfies imports; optional CUDA/runtime ops still require backend verification. |
| NumPy | 1.x | Avoids older Deepspeed/Torch extension incompatibilities with NumPy 2. |
| Setuptools | `<81` | Provides legacy `pkg_resources` used by Lightning Fabric. |
| PyArrow | 10.x | Compatible with older `datasets` feature extension APIs. |

This is not a universal pin file; it is a tested starting point for package inspection. For real GPU training, reselect Torch/Deepspeed/CUDA versions based on hardware.

## Install decision rules

- If the task only needs API/CLI inspection, use CPU PyTorch and skip optional example dependencies.
- If the task needs real Deepspeed, fused kernels, Ziya/Taiyi GPU inference, or training, prepare a backend-specific environment and run a small approved backend smoke.
- Do not install every example `requirements.txt`; select only the recipe family needed.
- Do not rely on the uninitialized `fs_datasets` submodule unless a workflow explicitly requires it.
- Keep model/data downloads and cache use explicit; `from_pretrained` can trigger network access.

## Safe smoke commands

```bash
python scripts/check_fengshen_install.py --check-cli-help
python sub-skills/model-zoo/scripts/check_model_imports.py --required-only
python sub-skills/pipelines-cli/scripts/inspect_pipeline_cli.py --pipeline text_classification
python sub-skills/data-training/scripts/check_ner_labels.py --markup bio
```

If these fail, inspect the exact import error and read [troubleshooting.md](troubleshooting.md) plus the nearest sub-skill troubleshooting reference.
