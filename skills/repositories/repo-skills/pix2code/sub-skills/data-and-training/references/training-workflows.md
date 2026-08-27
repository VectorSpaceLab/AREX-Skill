# pix2code Training Workflows

## Purpose

Read this for the legacy training command patterns, memory tradeoffs, and expected output artifacts.

## Training modes

The historical `model/train.py` supports two paths:

- in-memory training on resized images and sparse contexts,
- generator-based training when the dataset is too large to fit comfortably in memory.

The generator mode is controlled by the third command-line argument set to `1`.

## Legacy command pattern

The historical training script expected an input-path argument, an output-path argument, an optional `is_memory_intensive` flag (`1` for generator mode), and an optional pretrained-weight path. It saved model metadata and vocabulary into the output directory and wrote trained weights named `pix2code.h5` and `pix2code.json`.

## Runtime expectations

- Training is expensive and historically ran for hours on a GPU.
- The exact dependency pins are old and may not install cleanly on modern Python versions.
- The old code assumes the `model/` source directory is on `sys.path` when launched directly.
- Generator training depends on `Dataset.load_paths_only`, `Vocabulary.retrieve`, and `Generator.data_generator`.

## When to use the bundled helper

Use the bundled dataset helper for validation, splitting, and image conversion. Use this reference only for planning training commands, not for reproducing the full paper-scale training run.
