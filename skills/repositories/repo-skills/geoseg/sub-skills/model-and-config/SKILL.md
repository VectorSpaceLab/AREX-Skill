---
name: model-and-config
description: "Route GeoSeg model-family, dataset-label, loss, optimizer,
  checkpoint, and configuration-inspection questions to verified repository
  guidance."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# Model and configuration

Use this sub-skill when the question is about selecting a GeoSeg model, matching
an output head to a dataset, choosing losses or auxiliary supervision,
understanding optimizer/checkpoint fields, or inspecting a Python config
without accidentally requiring the dataset. Start with the relevant catalog
rather than importing a config blindly:

- [model-overview.md](references/model-overview.md) — model families, output
  behavior, dataset classes, palettes, and ignore-index conventions.
- [configuration.md](references/configuration.md) — the nine checked-in
  dataset/model configurations and their training-oriented settings.
- [api-reference.md](references/api-reference.md) — constructor, loss, config,
  optimizer, and metric API details.
- [troubleshooting.md](references/troubleshooting.md) — dependency, data,
  config, CLI, backend, and workflow failure diagnosis.
- [inspect_config.py](scripts/inspect_config.py) — a static, non-importing
  config report helper.

For actual training, hand off to [training](../training/SKILL.md). For model
checkpoint execution or tiled/large-image prediction, hand off to
[evaluation-inference](../evaluation-inference/SKILL.md). This sub-skill does
not prescribe a full training run or checkpoint-inference procedure.

## Safe decision sequence

1. Identify the dataset and read its class order, palette, and ignore index.
2. Select a model whose final head has exactly `num_classes` channels; enable
   auxiliary loss only when the model returns the expected training outputs.
3. Confirm whether `pretrained` means a timm download/cache or an explicit
   local checkpoint load, and check every referenced weight path.
4. Inspect a config statically first with `scripts/inspect_config.py`. Only
   execute `py2cfg` after data directories, optional dependencies, and weight
   files are intentionally available; several configs perform work at import.
5. Validate a synthetic batch's logits and label range before delegating the
   run to the training or evaluation-inference sibling.

The source snapshot used for this graph is commit `9453fe48209c4626b29e35e61bab93b61212c4b1`. The
inspection record confirms Python 3.8 documentation, the listed PyTorch/CUDA
stack, and an A100 CUDA smoke check. No dataset, checkpoint, native test, or
example is present in that checkout; treat unverified optional families and
external assets as explicit prerequisites, not as available capabilities.
