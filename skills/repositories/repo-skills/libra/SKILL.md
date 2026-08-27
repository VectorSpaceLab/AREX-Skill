---
name: libra
description: "Use the Libra ergonomic machine-learning client for query-driven
  tabular, NLP, vision, recommendation, dashboard, and analysis workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Libra Repo Skill

Use this skill when a task involves the Palashio/libra Python package, especially `from libra import client`. Libra builds ML workflows from natural-language-ish query strings, stores trained models and artifacts in `client.models`, and exposes helper methods for model inspection, plots, prediction, analysis, tuning, recommendations, Streamlit dashboards, NLP generation, image classification, and GANs.

Always read `references/environment-and-compatibility.md` before running code. The repository is a legacy TensorFlow/Keras/pandas project: modern Python stacks need compatibility shims, while the original pins are internally inconsistent. Use the bundled `scripts/libra_compat.py` before importing `libra` on modern pandas, and reapply it after import if you are going to run query methods, because `queries.py` resets `FutureWarning` handling during import. Do not assume CUDA is usable just because GPUs are present.

If the checkout or package version has changed, compare it with `references/repo-provenance.md` before trusting the generated skill or before running refresh work.

## Setup
- Do not install `requirements.txt` blindly. It mixes old TensorFlow/Keras pins with imports that only work on older pandas/scikit-learn releases.
- Preferred modern path for inspection and smoke tests:
  1. Prepare a compatible Python environment using the package notes in `references/environment-and-compatibility.md`.
  2. From the repository root, run `python -m pip install -e . --no-deps` so the local checkout is importable without pulling the legacy dependency list verbatim.
  3. Run `python skills/disco/libra/scripts/inspect_client_surface.py --methods-only` for a minimal import/surface check.
  4. Run `python skills/disco/libra/scripts/smoke_tabular_decision_tree.py` for a tiny CPU smoke test.
- For stricter legacy fidelity, use the older Python 3.8 stack described in `references/environment-and-compatibility.md`.

## Fast routing
- For `client(...)`, dataset reading, `models`, `info()`, `model()`, `predict()`, `plots()`, `accuracy()`, `losses()`, `target()`, `vocab()`, `recommend()`, `dashboard()`, tuning, or package/runtime setup, start with this root skill plus `references/api-surface.md` and `references/troubleshooting.md`.
- For tabular regression, classification, clustering, recommendation, model inspection, tuning, or dashboard launch on CSV/XLSX/JSON data, load `sub-skills/tabular-modeling/SKILL.md`.
- For text classification, summarization, named entities, GPT-2 text generation, image captioning, or NLP preprocessing and corpora setup, load `sub-skills/nlp-and-generation/SKILL.md`.
- For image classification, image preprocessing read modes, TFJS/TFLite export, feature maps, GAN generation, or image-layout troubleshooting, load `sub-skills/vision-and-generative/SKILL.md`.

## Core operating pattern
```python
from libra import client

c = client("path/to/data.csv")
c.decision_tree_query("predict target column")
print(c.models.keys())
print(c.info())
```

Key behavior to keep in mind:

1. A `client` instance represents one dataset path. Most queries read `self.dataset` each time.
2. Query methods store a dictionary under a fixed key such as `decision_tree`, `svm`, `regression_ANN`, `classification_ANN`, `convolutional_NN`, `text_classification`, `summarization`, `image_caption`, `text_generation`, `named_entity_recognition`, `content_recommender`, or `DCGAN`.
3. `latest_model` is updated after most query methods; many helper methods default to that value.
4. Target-column inference goes through `get_value_instruction()` plus Levenshtein matching, so user instructions should contain words close to the target column name. If target detection is wrong, make the instruction closer to the exact column name or pass explicit parameters like `label_column`, `drop`, `text`, `image_column`, or `read_mode` where available.
5. Training methods can write files: model save flags, TFJS/TFLite export, CNN image preprocessing, GAN output images, Keras Tuner directories, plot saving, and Streamlit dashboard launches. Choose output directories deliberately.

## Self-contained helper scripts
- `scripts/libra_compat.py` applies pandas/private-warning compatibility shims before importing legacy Libra code on modern stacks.
- `scripts/inspect_client_surface.py` prints public `client` methods and signatures.
- `scripts/smoke_tabular_decision_tree.py` creates a tiny synthetic CSV and runs a CPU decision-tree smoke test without using the original checkout datasets.

These scripts are intentionally generic; they avoid absolute source-checkout paths and do not depend on original-repo example files or notebooks at runtime.
