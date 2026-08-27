---
name: model-zoo-and-configuration
description: "Handles PaddleDetection model-family selection, YAML inheritance
  and overrides, model-zoo lookup, registry APIs, and configuration preflight."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Model Zoo and Configuration

Use this route when the task is to choose a PaddleDetection model/config, inspect `_BASE_` inheritance, override a YAML value, list model families, load a config, or add a registry-backed component.

## Workflow

1. Identify the task family: detection, instance segmentation, keypoint, MOT, rotated/small-object detection, semi-supervised detection, slimming, or PP-Human/PP-Vehicle.
2. Select a representative config from the target checkout's `configs/` tree. Prefer a documented model family and verify the dataset block, metric, input shape, `num_classes`, and `save_dir`.
3. Load the YAML with `ppdet.core.workspace.load_config`. It recursively resolves `_BASE_` files and updates the global registry/config state.
4. Apply only deliberate overrides using `-o key=value` or `merge_config`; use dotted keys for nested values and validate the resulting object.
5. For model-zoo lookup, use `ppdet.model_zoo.list_model(filters)` and `get_weights_url(name)`. Treat `get_config_file(name)` and `get_model(name)` as network/cache operations; a source build reporting version `0.0.0` may request a nonexistent `configs/0.0.0/configs.tar`.
6. Run [`scripts/summarize_config.py`](scripts/summarize_config.py) before training or export. Read [`references/troubleshooting.md`](references/troubleshooting.md) for stale package/version and config errors.

## Registry customization

`ppdet.core.workspace.register` adds a class to the registry and `create(name, **kwargs)` constructs registered modules. Keep custom modules in the target project/package, register them before loading a config that names them, and test with `Trainer(cfg, mode="test")` before starting a training loop. Use the API details in [`references/api-reference.md`](references/api-reference.md); do not edit generated model-zoo metadata by hand.

## References and helper

- [`references/configuration.md`](references/configuration.md): YAML merge order, override syntax, and high-value fields.
- [`references/model-zoo.md`](references/model-zoo.md): model-family routing and local-vs-remote model-zoo behavior.
- [`references/api-reference.md`](references/api-reference.md): live signatures for workspace/model-zoo APIs.
- [`references/troubleshooting.md`](references/troubleshooting.md): config, registry, package-version, and weight lookup failures.
- [`scripts/summarize_config.py`](scripts/summarize_config.py): read-only YAML/config summary for a target checkout.
