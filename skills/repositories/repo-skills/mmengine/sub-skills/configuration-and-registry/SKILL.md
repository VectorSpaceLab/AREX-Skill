---
name: configuration-and-registry
description: "Create, validate, merge, dump, and debug MMEngine
  Config/ConfigDict files and registry-driven object construction."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Configuration and Registry

Use this sub-skill when the task mentions MMEngine config files, config inheritance, `Config` or `ConfigDict`, `custom_imports`, lazy import, CLI overrides, `Registry`, `build_from_cfg`, `DefaultScope`, registry scope, or cross-library registry routing.

## Runtime Map

- `references/configuration-workflows.md`: load, edit, merge, dump, validate, and inspect MMEngine configs safely.
- `references/registry-reference.md`: register classes/functions, build objects from config dictionaries, and reason about scopes.
- `references/troubleshooting.md`: map common config and registry symptoms to causes and fixes.
- `scripts/inspect_config.py`: safely parse a config file or inline config string, apply dotted overrides, and print top-level keys.

## Start Here

1. For config file syntax, inheritance, environment/predefined variables, `Config.fromfile`, `Config.fromstring`, `merge_from_dict`, and `dump`, read `references/configuration-workflows.md`.
2. For `Registry(...)`, `register_module`, `Registry.build`, `build_from_cfg`, `default_args`, `_scope_`, and `init_default_scope`, read `references/registry-reference.md`.
3. For failures such as missing `type`, unregistered modules, wrong default scope, list override errors, duplicate registration, or lazy/custom import confusion, read `references/troubleshooting.md`.
4. To validate a user-supplied config without training or building large objects, run `python scripts/inspect_config.py --help` from this sub-skill directory.

## Boundaries

- Keep this sub-skill focused on `mmengine.config`, `mmengine.registry`, `DefaultScope`, config merging/dumping, and registry-driven object construction.
- Route full `Runner` train/val/test placement to `../runner-and-training/SKILL.md`.
- Route dataset pipeline item semantics, data elements, and file IO backends to `../data-structures-and-io/SKILL.md`.
- Route model step contracts, metrics, evaluator behavior, and inference/TTA contracts to `../models-metrics-and-inference/SKILL.md`.
- Route logging, visualizer, distributed, device, and runtime utilities to `../runtime-utilities-and-visualization/SKILL.md`.

## Safe Operating Rules

- Prefer parsing and inspecting configs before building registry objects; building may import optional packages or instantiate user code.
- Treat `custom_imports`, pure-Python lazy imports, and registry `locations` as import triggers; review them before executing in an untrusted workspace.
- Do not depend on source checkout files; use the APIs and bundled helper script documented here.
