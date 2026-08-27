---
name: deep-learning
description: "Route arcgis.learn geospatial deep-learning workflows, model
  selection, deployment, and optional dependency checks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Deep Learning

Use this sub-skill for `arcgis.learn` work only.

## Start here
- Read [learn-workflows](references/learn-workflows.md) for the workflow shapes, training loop, and deployment patterns.
- Read [model-catalog](references/model-catalog.md) to choose a model family by data shape and task.
- Read [troubleshooting](references/troubleshooting.md) when imports, GPU readiness, data prep, or deployment fail.
- Run `python scripts/check_learn_optional_deps.py` to probe `arcgis.learn`, `torch`, `torchvision`, and CUDA support without training or downloads.

## Use when
- The task is about imagery deep learning, text/NLP deep learning, tabular/time-series ML, point-cloud models, custom model extensibility, or model publishing/inference in `arcgis.learn`.
- The user needs help deciding between `prepare_data`, `prepare_tabulardata`, `prepare_textdata`, `MLModel`, `ModelExtension`, or a specific model family.
- The user wants a safe import/dependency triage for `arcgis.learn` on a machine that may not have `torchvision` or GPU support.

## Route away when
- Raster analytics without learned models -> imagery-raster-analysis
- Feature/SEDF analysis -> features-dataframes-analysis
- GIS content/admin/auth -> gis-admin-content
- AI utility services, dashboards, knowledge graphs, or app automation -> apps-knowledge-ai-services

## Operating rules
- Treat `arcgis.learn` as optional. If `torchvision` is missing, stop at the dependency gate and report that the deep-learning stack is incomplete.
- Do not claim GPU training, model downloads, or notebook execution success unless the user provided the required runtime and data.
- Prefer notebook-independent guidance that survives outside the original checkout.
- Do not call ArcGIS services or publish models unless the user explicitly asks and has the required credentials and service access.
- Use the workflow references for all detailed API, model, and troubleshooting steps; keep this router terse.
