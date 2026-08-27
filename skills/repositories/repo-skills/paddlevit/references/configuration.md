# Shared configuration and source-root conventions

Read when constructing a PaddleViT command, changing YAML, choosing a model
folder, or diagnosing an unexpected option value.

## Configuration precedence

Most folders use `yacs.config.CfgNode`:

1. Python defaults in that folder's `config.py`.
2. Recursive YAML `BASE` files, then the requested YAML file.
3. Selected CLI overrides applied by `update_config`.

CLI values therefore win over YAML for fields the entry script exposes. Record
the effective config after merges; do not infer it from a filename. Common
fields include `DATA.DATA_PATH`, `DATA.DATASET`, batch/image/crop sizes,
`MODEL.NAME`, `MODEL.NUM_CLASSES`, optimizer/scheduler values, `SAVE_DIR` or
`SAVE`, `EVAL`, `AMP`, `NGPUS`, `PRETRAINED`, and `RESUME`. Exact names vary by
folder, so inspect the selected `config.py` and parser.

## Path and import rules

PaddleViT does not provide one stable package namespace. Run the selected
workflow from its documented source directory or pass only that directory as
the first `PYTHONPATH` entry. Bare imports such as `from config import
get_config` and `from utils import ...` are intentionally local. Start a fresh
Python process when switching model families; otherwise an earlier `config`
module can remain cached.

A generic command shape is:

```bash
cd <selected-model-directory>
PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}" python <entrypoint>.py \
  -cfg <config.yaml> -data_path <data-root>
```

Treat `<selected-model-directory>`, `<config.yaml>`, `<data-root>`, checkpoint
prefixes, and output directories as user-owned values to validate before
execution. Do not paste a source checkout path into a public handoff as if it
were universal.

## Config validation checklist

- YAML exists and every `BASE` path resolves relative to the YAML file.
- Image/crop sizes are compatible with patch size, window size, feature stride,
  and the selected decoder/head.
- Number of classes matches labels and checkpoint head dimensions.
- Dataset name and root agree; do not point a COCO/segmentation entrypoint at an
  ImageNet list or at a split directory when it expects the dataset root.
- Batch size is understood as per-GPU where the source uses distributed loaders.
- `PRETRAINED` and `RESUME` are different: a pretrained model state is not
  necessarily an exact optimizer/teacher/loss resume.
- Output paths are new or explicitly approved, especially segmentation demo
  results and training `SAVE_DIR`.

## Installation facts

The source documents PaddlePaddle >=2.1, Python 3.6/3.7-era examples, `yacs`,
and PyYAML. The inspection environment proved PaddlePaddle GPU 2.6.2,
yacs 0.1.8, PyYAML, OpenCV, SciPy, LMDB, pycocotools, and Cityscapes tooling.
Use a compatible current Paddle build rather than assuming all 2021 scripts
are forward-compatible. A dependency import is weaker evidence than a model
forward on the requested backend.
