---
name: installation-and-configs
description: "Install and statically inspect the legacy OpenMMLab BEVFormer and
  BEVFormerV2 config stack."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# installation-and-configs

Use this sub-skill when you need to:
- verify the legacy OpenMMLab BEVFormer import stack;
- inspect or customize BEVFormer or BEVFormerV2 configs;
- compare config inheritance, plugin settings, model family choices, or BEV and temporal knobs;
- run the safe config inspector.

Start here:
- [Configuration notes](references/configuration.md)
- [API reference](references/api-reference.md)
- [Troubleshooting](references/troubleshooting.md)
- [Config inspector](scripts/inspect_bevformer_config.py)

Route other work elsewhere:
- dataset tree or generated nuScenes files: dataset-preparation
- distributed train, eval, or FP16 launch: training-and-evaluation
- logs, plots, benchmark output, or visualization: analysis-and-utilities

Keep this sub-skill read-only. Do not mutate datasets, checkpoints, or training outputs here.
