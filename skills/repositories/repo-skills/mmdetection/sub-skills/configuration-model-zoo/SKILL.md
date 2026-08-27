---
name: configuration-model-zoo
description: "Choose, inspect, modify, and validate MMDetection 3.3.0 configs
  and model-zoo entries without training or inference side effects."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Configuration Model Zoo

Use this sub-skill when an agent needs to select an MMDetection model family, inspect a config, resolve `_base_` inheritance, apply safe config overrides, or decide between MIM model names and config paths.

## Route Here

- Choose a model family/config from MMDetection's model zoo or metafile-style entries.
- Inspect `model`, dataloaders, pipelines, evaluator, runtime hooks, `default_scope`, or `auto_scale_lr` settings before running anything expensive.
- Modify config values with `--cfg-options` or equivalent `Config.merge_from_dict` semantics.
- Debug invalid `_base_`, config import/registry-scope, checkpoint/config pairing, or missing `auto_scale_lr.base_batch_size` failures.
- Migrate or review 2.x-style configs for MMDetection 3.x structure.

## Reroute

- Training, validation, testing commands, dataset execution, and launcher details: use `training-testing`.
- `DetInferencer`, `init_detector`, `inference_detector`, visualization outputs, and CPU/GPU inference execution: use `inference-visualization`.
- New detectors, registries, custom transforms, custom datasets, or plugin modules: use `customization-extension`.

## References and Script

- Read [configuration.md](references/configuration.md) for config inheritance, override, validation, and migration workflows.
- Read [model-zoo.md](references/model-zoo.md) for model-index/metafile navigation, MIM names, and config-path decisions.
- Read [troubleshooting.md](references/troubleshooting.md) for common config/model-zoo failures and fixes.
- Run [inspect_config.py](scripts/inspect_config.py) to flatten and summarize a config safely:

```bash
python sub-skills/configuration-model-zoo/scripts/inspect_config.py CONFIG.py --summary --cfg-options model.test_cfg.rcnn.score_thr=0.3
```

The script reads configs with MMEngine, supports `--cfg-options`, prints a concise summary by default, and can dump the merged config to `.py`, `.json`, or `.yml`.
