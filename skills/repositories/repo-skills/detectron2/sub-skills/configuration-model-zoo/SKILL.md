---
name: configuration-model-zoo
description: "Choose, load, inspect, modify, and validate Detectron2 Yacs,
  LazyConfig, and model-zoo configurations without relying on the source
  checkout."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Configuration and Model Zoo

Use this sub-skill when a request mentions Detectron2 configs, `_BASE_`, Yacs/YAML, `CfgNode`, `get_cfg`, LazyConfig Python files, `LazyCall`, `instantiate`, model-zoo config names, checkpoint URLs, `MODEL.WEIGHTS`, `train.init_checkpoint`, or CPU/GPU config overrides.

## Fast Routing

- For Yacs/YAML workflows, read [references/configuration.md](references/configuration.md#yacs-yaml-configs) and use `get_cfg()`, `merge_from_file()`, and `merge_from_list()`.
- For LazyConfig workflows, read [references/configuration.md](references/configuration.md#lazyconfig-python-configs) and use `LazyConfig.load()`, `LazyConfig.apply_overrides()`, `LazyConfig.to_py()`, `LazyCall`, and `instantiate()`.
- For official model-zoo paths, checkpoint URLs, and no-download inspection, read [references/model-zoo.md](references/model-zoo.md).
- For symptoms such as wrong paths, mixed override syntax, unresolved relative imports, serialization failures, or CPU/GPU confusion, read [references/troubleshooting.md](references/troubleshooting.md).
- To safely inspect a config without building a model or downloading weights, run [scripts/inspect_config.py](scripts/inspect_config.py) with `--help` first.

## Boundary Notes

This sub-skill owns configuration loading, config mutation, static inspection, and official model-zoo path/checkpoint selection. Route dataset registration, dataset dictionaries, COCO JSON schemas, and mappers to ../data-datasets/. Route training launch flags, evaluation commands, and distributed execution to ../training-evaluation/. Route custom component registries and project extensions to ../extension-projects/. Route TorchScript, tracing, Caffe2, and deployment format questions to ../deployment-export/.

## Safe Defaults

- Prefer `model_zoo.get_config()` or `model_zoo.get_config_file()` for config inspection; reserve `model_zoo.get()` for cases that intentionally build a model and may load checkpoint files.
- Set device explicitly for CPU-only work: Yacs uses `MODEL.DEVICE cpu`; LazyConfig model-zoo configs typically require editing `cfg.model.device = "cpu"` or passing `device="cpu"` to `model_zoo.get()` when building.
- Avoid `trained=True` and `model_zoo.get()` when validating config syntax only; use `get_checkpoint_url()` to print a URL without downloading.
- Keep Yacs CLI overrides as alternating `KEY VALUE` tokens, and LazyConfig overrides as `key=value` strings.
