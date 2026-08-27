# Cross-cutting troubleshooting

## Install/import failures

| Symptom | Likely cause | Recovery |
|---|---|---|
| `ImportError: cannot import name 'cached_path' from transformers` | Transformers too new for Fengshen ZEN imports. | Use an isolated compatible stack; Transformers 4.20.1 satisfied construction-time imports. |
| `ImportError: cannot import name 'softmax_backward_data' from transformers.pytorch_utils` | Transformers too old or incompatible for DeBERTa-v2 imports. | Use a version that provides both `cached_path` and `softmax_backward_data`. |
| `Trainer.add_argparse_args` missing | PyTorch Lightning 2.x changed/removed the parser API used by this code. | Use Lightning 1.x for parser/training compatibility, or patch code in a separate repo-maintenance task. |
| `torchmetrics.Accuracy` requires `task` | Torchmetrics API changed. | Use an older compatible Torchmetrics or update the pipeline code deliberately. |
| `No module named pkg_resources` | New Setuptools removed legacy packaging API expected by Lightning Fabric. | Use a Setuptools version that still includes `pkg_resources`. |
| NumPy ABI warnings or `numpy.BUFSIZE` missing | NumPy 2.x with older compiled/Deepspeed stack. | Use NumPy 1.x for this repo's older dependency stack. |
| `datasets`/`pyarrow` extension errors | New PyArrow with older Datasets. | Pin PyArrow to a version compatible with the selected Datasets release. |

## CLI and pipeline errors

- `fengshen-pipeline` requires at least two positional arguments: pipeline module and method.
- The source CLI only supports `predict` and `train`.
- Console-compatible pipeline names are Python module names under `fengshen.pipelines`; `text_classification` is the main documented CLI route.
- Real `predict` calls may download model weights; real `train` calls may download datasets.
- Some pipeline examples in the source checkout contain maintainer-local absolute paths. Do not copy those paths; replace them with user-provided local model/data paths.

Use `sub-skills/pipelines-cli/scripts/inspect_pipeline_cli.py` to distinguish unsupported names from dependency-stack import errors.

## Backend and resource failures

CPU import checks do not verify:

- CUDA memory fit;
- Deepspeed optimizer runtime;
- Megatron fused CUDA kernels;
- Stable Diffusion FP16 CUDA execution;
- Ziya/LLaMA large-model quantization or tensor-parallel conversion;
- full training convergence.

When the user needs one of those claims, prepare and verify a backend-specific environment before running the workflow. Capture GPU type, VRAM, driver/CUDA, Torch build tag, Deepspeed version, model size, precision, batch size, and output/checkpoint paths.

## Data and submodule issues

- The repo declares `fengshen/data/fs_datasets` as a submodule using an SSH URL. If it is absent or inaccessible, do not assume its datasets exist. Switch to an authorized HTTPS/SSH submodule checkout only when a workflow explicitly needs it.
- Classification defaults use `sentence`, `sentence2`, and `label`; pass explicit field flags or transform data when names differ.
- Sequence tagging expects consistent labels and split files; validate with the data-training helper before training.
- Pretraining/Megatron workflows often require `.idx`/`.bin` indexed files and large corpora; verify data generation before distributed launch.

## Checkpoint/conversion safety

- Treat conversion utilities as mutating and large-output operations.
- Never use the same directory as both source and output.
- Ask for overwrite permission and backup/rollback plan before actual conversion.
- Prefer dry-run planners in `sub-skills/examples-conversion/scripts/` until inputs, outputs, backend, and dependency stack are explicit.
