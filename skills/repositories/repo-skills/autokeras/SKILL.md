---
name: autokeras
description: "Use AutoKeras for Keras-based AutoML task APIs, custom AutoModel
  graphs, tuner search, and model export workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# AutoKeras repo skill

Use this skill when a user asks how to operate AutoKeras: Keras-based AutoML for image, text, structured-data, custom search-space, tuner, and export workflows. This skill is self-contained; do not rely on the original repository checkout at runtime.

## Setup first

AutoKeras 3.0.0 uses Keras 3. Choose and install a Keras backend before importing Keras or AutoKeras. The repository's public install guidance and CI support a PyTorch backend path for ordinary CPU checks.

```bash
python -m pip install autokeras
python -m pip install torch --index-url https://download.pytorch.org/whl/cpu
KERAS_BACKEND=torch python -c "import keras, autokeras as ak; print(ak.__version__, keras.backend.backend())"
```

Run [scripts/check_autokeras_env.py](scripts/check_autokeras_env.py) when setup, backend, import, or public API visibility is uncertain.

## Route by task

- [sub-skills/task-apis/SKILL.md](sub-skills/task-apis/SKILL.md): high-level `ImageClassifier`, `ImageRegressor`, `TextClassifier`, `TextRegressor`, `StructuredDataClassifier`, and `StructuredDataRegressor` workflows, including data shapes and task-specific troubleshooting.
- [sub-skills/automodel-customization/SKILL.md](sub-skills/automodel-customization/SKILL.md): custom `AutoModel` graphs, nodes, blocks, heads, multimodal inputs, multitask outputs, and graph/data ordering failures.
- [sub-skills/search-and-export/SKILL.md](sub-skills/search-and-export/SKILL.md): tuner names/classes, `max_trials`, objectives, callbacks, search directories, `overwrite`, `export_model()`, and reloading saved `.keras` models.

## Shared references

- [references/setup-and-troubleshooting.md](references/setup-and-troubleshooting.md): installation/backend checks, common import failures, optional GPU notes, and cross-cutting recovery.
- [references/source-script-inventory.md](references/source-script-inventory.md): how repository examples/scripts were distilled into bundled helpers or excluded.
- [references/repo-provenance.md](references/repo-provenance.md): source snapshot used to build this skill; read it before deciding whether a checkout needs `refresh-repo-skill`.
- [references/repo-routing-metadata.json](references/repo-routing-metadata.json): structured metadata consumed by the repo-skills router importer.

## Operating constraints

- Keep first runs bounded: `max_trials=1`, `epochs=1`, small synthetic/local data, and an explicit scratch `directory`.
- Set `KERAS_BACKEND` before importing Keras or AutoKeras.
- Do not run original examples, notebooks, benchmark scripts, Docker scripts, or release tooling as runtime dependencies. Use bundled scripts and references instead.
- CUDA/GPU execution is optional for this skill. Do not claim GPU verification unless the user's own environment and backend framework have been checked.
