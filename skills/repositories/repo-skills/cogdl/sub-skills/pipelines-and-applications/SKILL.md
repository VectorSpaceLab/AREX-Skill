---
name: pipelines-and-applications
description: "Routes CogDL pipeline apps, embedding generation, recommendation,
  and OAG-BERT workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# CogDL Pipelines and Applications

Use this sub-skill when the user wants a named CogDL application rather than
a raw model or training loop.

Typical triggers:
- "Show me CogDL dataset stats for a graph dataset"
- "How do I generate embeddings with CogDL?"
- "How do I use CogDL recommendation or OAG-BERT pipelines?"
- "Why did the OAG archive or cache step fail?"

Read `references/pipeline-recipes.md` for the supported app names, the main
input/output shapes, and the safe no-network examples.
Read `references/oagbert.md` for OAG-BERT variants, paper/entity input fields,
and the optional cache/network boundary.
Read `references/troubleshooting.md` for unknown apps, PNG output, generate-
emb feature requirements, recommendation data layout, and OAG cache issues.

Run `scripts/pipeline_smoke.py` to inspect the app registry and optionally run
a tiny no-download `generate-emb` smoke on a small edge list.

Route these elsewhere:
- `../experiments-and-cli/SKILL.md` for `experiment(...)`, CLI flags, and
  AutoML orchestration.
- `../graph-data-and-datasets/SKILL.md` for graph schemas, masks, and custom
  fixture creation.
- `../models-layers-and-operators/SKILL.md` for model/layer code and sparse
  operator details.
- `../training-wrappers-and-customization/SKILL.md` for wrappers and trainer
  settings used by the pipelines.

## What this sub-skill covers

- `pipeline(app: str, **kwargs)` and the `SUPPORTED_APPS` registry.
- Dataset stats and dataset-visual apps.
- Embedding generation apps, including the no-download ProNE smoke path.
- Recommendation pipelines and their data-shape expectations.
- OAG-BERT loading, model variants, and paper/entity input helpers.

## Decision rules

- If the user just needs a quick app name, use the registry and keep the answer
  brief.
- If the app is dataset-related, make the cache/download behavior explicit.
- If the app is OAG-BERT-related, label the model archive as optional and
  network/cache-dependent.
- Keep runnable helpers safe by default; no helper in this sub-skill should
  download a dataset unless the user explicitly asks for that side effect.
