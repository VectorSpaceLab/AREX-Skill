---
name: integrations-and-plugins
description: "Route SwanLab framework callback adapters, notification plugins,
  CSV writer, and callback protocol questions."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Integrations and Plugins

Use this sub-skill for SwanLab adapter and plugin questions that are **not** about base experiment tracking, media objects, or settings/credentials.

## Route here for
- Framework callback adapters: Transformers, PyTorch Lightning, Keras, LightGBM, XGBoost, CatBoost, Ray, Accelerate, MMEngine, Ultralytics, FastAI, Stable-Baselines3, PaddleNLP, and Torchtune.
- Plugin callbacks: notifications and CSV writer behavior.
- Custom `Callback` subclasses, callback dedupe, merge order, and lifecycle hooks.
- Optional dependency import errors for framework adapters.

## Use these references
- [Framework integrations](references/framework-integrations.md)
- [Plugins](references/plugins.md)
- [Troubleshooting](references/troubleshooting.md)
- [Validation script](scripts/check_plugin_callback.py)

## Route away from here
- Base tracking APIs and run lifecycle → experiment-tracking.
- Media object details and custom charts → media-and-custom-charts.
- Settings, hosts, login, and credential storage → settings-and-modes.

## Working rule
Keep the answer focused on the adapter or plugin hook path, then call out the exact callback name, required package, and any single-process or merge-order caveat.
