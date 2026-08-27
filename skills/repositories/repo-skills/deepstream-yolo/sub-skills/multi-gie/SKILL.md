---
name: multi-gie
description: "Routes DeepStream-Yolo tasks that run multiple detectors in one
  DeepStream pipeline or use secondary GIEs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Multi-GIE

Use this sub-skill when the user wants more than one YOLO detector in one DeepStream app, especially when the task involves duplicated `gieN` folders, secondary inference, or plugin-version collisions.

## Trigger phrases

- multiple GIEs
- two YOLO models in one app
- secondary GIE
- `operate-on-gie-id`
- `operate-on-class-ids`
- `YOLOLAYER_PLUGIN_VERSION`
- duplicate detector pipeline

## Include here

- Folder duplication for `gie1`, `gie2`, ...
- Changing the plugin version inside each copied `yoloPlugins.h`.
- Wiring `primary-gie` and `secondary-gieN` sections.
- Moving the generated engine file into the right `gieN/` folder.
- Troubleshooting collisions between the duplicated inference stacks.

## Exclude or route elsewhere

- Exporting the model to ONNX first: use `model-conversion`.
- Single-detector deployment: use `deployment`.
- INT8 calibration tuning: use `int8-benchmarking`.
- Skill maintenance or router import logic.

## How to use this route

1. Read `references/workflows.md` for the multi-GIE folder layout.
2. Read `references/configuration.md` before editing any duplicated config files.
3. Use `scripts/setup-multi-gie-tree.sh --count 2 --output-dir ./deepstream-yolo-multi-gie` to scaffold a self-contained multi-GIE runtime tree from the bundled assets.
4. Check `references/troubleshooting.md` if the app starts but the GIEs do not line up.

## What a future agent should be able to do here

- Explain why `deepstream-app` cannot use multiple primary GIEs without a custom code path.
- Scaffold the `gie1`, `gie2`, ... folder layout.
- Set unique plugin versions and GIE IDs consistently.
- Route secondary inference to a primary detector and/or class subset.

## Common failure signals

- `gie-unique-id` collisions
- `operate-on-gie-id` points at the wrong primary GIE
- `YOLOLAYER_PLUGIN_VERSION` was not incremented
- Engine files are left in the root folder instead of the owning `gieN/` folder

## Linked helpers

- `scripts/setup-multi-gie-tree.sh` — scaffold the duplicated folder structure from the bundled assets.
- `references/workflows.md` — step-by-step multi-GIE flow.
- `references/configuration.md` — config keys and meaning.
- `references/troubleshooting.md` — multi-GIE failure modes.
