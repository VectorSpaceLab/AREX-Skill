---
name: model-api-components
description: "Use and extend MMOCR registries, model components, data samples,
  transforms, metrics, visualizers, dictionaries, and OpenMMLab project
  extensions."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# MMOCR model API components

Use this sub-skill when the task is to inspect, build, register, customize, or troubleshoot MMOCR internals rather than to run an end-to-end OCR prediction or a full training job.

## Best-fit tasks

- Register or build MMOCR model, transform, metric, visualizer, dictionary, or project-extension components through OpenMMLab registries.
- Decide which `DataSample` fields a custom head, postprocessor, metric, or visualizer should read and write.
- Add a custom backbone, head, postprocessor, metric, transform, or visualizer through a project module without editing the core MMOCR package.
- Diagnose registry/default-scope issues, dictionary token mismatches, transform pipeline type lookup failures, visualization/font/headless problems, and metric output-shape surprises.

Route these instead:

- End-to-end OCR/KIE inference, pretrained inferencers, or prediction result schemas: `../ocr-inference/`.
- Train/test CLIs, config inheritance, work directories, checkpoints, and evaluator placement in full experiments: `../training-evaluation-configs/`.
- Dataset conversion/preparation CLIs and dataset-zoo acquisition: `../data-preparation/`.

## Read this sub-skill

1. Start with [component-api-reference](references/component-api-reference.md) for registry names, data structures, model families, dictionaries, transforms, metrics, visualizers, and utility entry points.
2. Use [extension-patterns](references/extension-patterns.md) when adding custom modules through OpenMMLab project-style registration.
3. Use [troubleshooting](references/troubleshooting.md) when a component cannot be built, registered, visualized, evaluated, or connected to the expected `DataSample` fields.
4. Use the bundled [`mmocr_component_registry_probe.py`](scripts/mmocr_component_registry_probe.py) to inspect registry availability and dictionary files in the active Python environment.

## Operating rules

- Prefer registry/config-based extension over direct edits to MMOCR core modules.
- Initialize or preserve the `mmocr` default scope before building components from config dicts.
- Import custom extension modules before building configs that name their registered classes.
- Treat `TextDetDataSample`, `TextSpottingDataSample`, `TextRecogDataSample`, and `KIEDataSample` as the contract between models, postprocessors, metrics, and visualizers.
- Keep dictionary files, token settings, postprocessor ignore characters, and recognition label fields synchronized.
- For component-level debugging, verify imports, registry membership, sample field presence, and small synthetic inputs before using full datasets or checkpoints.
