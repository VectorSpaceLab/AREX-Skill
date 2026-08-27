---
name: machine-learning-and-ai
description: "Use geemap machine learning conversion helpers and optional AI
  dataset discovery interfaces."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# geemap Machine Learning and AI

Use this sub-skill when a task involves geemap's Earth Engine classification workflows, local scikit-learn decision-tree/random-forest conversion into Earth Engine classifier strings, classifier CSV or FeatureCollection persistence, or optional AI-assisted Earth Engine dataset discovery.

## Start here

1. Confirm basic geemap, Earth Engine, and optional dependency setup with [../../references/installation-and-auth.md](../../references/installation-and-auth.md).
2. For local model conversion, use [references/workflows.md](references/workflows.md#local-scikit-learn-forest-to-earth-engine-classifier) and the bundled [scripts/rf_tree_smoke.py](scripts/rf_tree_smoke.py).
3. For exact function signatures, inputs, outputs, and gotchas, use [references/api-reference.md](references/api-reference.md).
4. For error handling, use [references/troubleshooting.md](references/troubleshooting.md).

## What this sub-skill owns

- `geemap.ml.tree_to_string` for one fitted scikit-learn decision tree.
- `geemap.ml.rf_to_strings` for fitted scikit-learn random-forest or ExtraTrees-style ensembles.
- `geemap.ml.strings_to_classifier` for in-memory Earth Engine classifier construction from tree strings.
- `geemap.ml.trees_to_csv` and `geemap.ml.csv_to_classifier` for local CSV persistence and reload.
- `geemap.ml.export_trees_to_fc` and `geemap.ml.fc_to_classifier` for Earth Engine asset FeatureCollection persistence and reload.
- Earth Engine supervised/unsupervised classification workflow structure: sample training data, train or import a classifier/clusterer, classify an image, then route display or accuracy work to the sibling sub-skills.
- Optional `geemap.ai` dataset catalog, Gemini/Genie, embedding, and dataset explorer surfaces when the `ai` extra, Google credentials, network access, and notebook UI are available.

## Route elsewhere

- Generic file conversion, Earth Engine export tasks, shapefile/GeoJSON/CSV data movement, or non-classifier table export: [../conversion-and-io/SKILL.md](../conversion-and-io/SKILL.md).
- Adding classified images or vector layers to an interactive map: [../interactive-earth-engine-maps/SKILL.md](../interactive-earth-engine-maps/SKILL.md).
- Accuracy matrices, charts, legends, palettes, static cartography, or chart rendering: [../visualization-and-charts/SKILL.md](../visualization-and-charts/SKILL.md).
- Timelapse, GIF, app, or publication workflows: [../timelapse-and-apps/SKILL.md](../timelapse-and-apps/SKILL.md).

## Operating constraints

- Local tree conversion is concrete and deterministic, but it requires scikit-learn, numpy, pandas, and a fitted compatible estimator.
- Earth Engine classifier objects can be constructed locally from strings, CSV, or FeatureCollections, but using them to classify images or export assets requires Earth Engine initialization, credentials, a project when required by the Earth Engine client, and network access.
- AI helpers are optional, credentialed, and networked. Treat them as convenience interfaces, not required geemap ML functionality.
- Do not rely on source notebooks or repository checkout files at runtime; the self-contained recipes and script in this sub-skill are the supported reference.
