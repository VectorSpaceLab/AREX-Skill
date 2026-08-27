---
name: models-and-configs
description: "Navigate OpenPCDet YAML configs, detector/model registries, model
  families, cfg overrides, and extension points."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# OpenPCDet Models and Configs

Use this sub-skill for YAML config interpretation, model-family selection, detector registry names, `--set` overrides, module extension, and advanced configs.

## Fast route

1. Read `references/config-and-model-map.md` for config semantics and registry names.
2. Inventory a checkout with `scripts/inventory_openpcdet_configs.py --repo <checkout>`.
3. Summarize a target config with `../../scripts/summarize_openpcdet_config.py --cfg <config.yaml>`.
4. Route data/product problems to `../data-preparation/SKILL.md` and train/test command construction to `../training-and-evaluation/SKILL.md`.

## High-risk model/config tasks

- Matching checkpoint, config, class names, point feature schema, and detector family.
- Selecting spconv-heavy vs point-based vs image-fusion models based on runtime and dataset availability.
- Extending registries without forgetting `__all__` mappings or config `NAME` fields.
- Applying `--set` overrides without violating OpenPCDet's type checks.
