---
name: deeppavlov
description: "DeepPavlov package routing for config-driven NLP workflows,
  model-family selection, and serving."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# DeepPavlov

Use this repo skill when the task involves the DeepPavlov Python package, its
`deeppavlov.configs` tree, or the `python -m deeppavlov` command family.

## What this skill covers

- Installing and smoke-checking the package.
- Choosing the right CLI mode for a config-driven workflow.
- Routing to the right model family for text classification, tagging,
  retrieval/QA, or serving.
- Troubleshooting package-wide install/import and config issues.

## Start here

1. Read [`references/installation-and-cli.md`](references/installation-and-cli.md)
   for install, CLI modes, and the offline smoke helper.
2. Read [`references/model-overview.md`](references/model-overview.md) to route
   to the right sub-skill for the user’s task family.
3. Read [`references/troubleshooting.md`](references/troubleshooting.md) when
   the failure is package-wide rather than family-specific.
4. Read [`references/repo-provenance.md`](references/repo-provenance.md) if you
   need the source baseline used to create this skill.

## Route to a sub-skill

### [`sub-skills/pipelines/SKILL.md`](sub-skills/pipelines/SKILL.md)
Use this for config parsing, `build_model`, `train_model`, `evaluate_model`,
`train_evaluate_model_from_config`, `parse_config`, `deep_download`, nested
configs, registries, custom components, cross-validation, and parameter
search.

### [`sub-skills/text-models/SKILL.md`](sub-skills/text-models/SKILL.md)
Use this for classifiers, NER, entity extraction, spelling correction,
sentence segmentation, morpho-syntax parsing, relation extraction,
multitask models, and embedding extraction.

### [`sub-skills/retrieval-qa/SKILL.md`](sub-skills/retrieval-qa/SKILL.md)
Use this for document retrieval, ranking, FAQ, SQuAD, ODQA, and KBQA.

### [`sub-skills/serving/SKILL.md`](sub-skills/serving/SKILL.md)
Use this for `riseapi`, `risesocket`, `/probe`, `/api`, socket framing,
service settings, TLS flags, metrics, and runtime request validation.

## Minimal package smoke

After installing DeepPavlov in the target environment, run the offline smoke
script:

```bash
python scripts/smoke_deeppavlov_pipeline.py
```

Expected result: the tiny lowercasing/tokenization pipeline prints a tokenized
output for the default text.

## Common decisions

- If the user only gives a config stem, let DeepPavlov resolve it unless a
  deprecation alias warning appears.
- If the task is about the shape of a config or how to wire a pipeline,
  go to `pipelines`.
- If the task is about which built-in model family to use, go to
  `text-models` or `retrieval-qa`.
- If the task is about exposing a chosen model over HTTP or sockets, go to
  `serving`.
- If the task is about a broken install, import, or dependency conflict and
  does not depend on a specific family, use the root troubleshooting reference.

## What not to do here

- Do not re-open the original repository checkout for runtime guidance when the
  bundled references already answer the question.
- Do not bury model-family specifics in this root file; keep them in the owned
  sub-skill.
- Do not send serving questions to a model-family sub-skill just because the
  model family appears in the request.

## Useful commands

- `python -m deeppavlov --help`
- `python scripts/smoke_deeppavlov_pipeline.py`
- `python -m pip check`

## Provenance and selection metadata

- See `references/repo-provenance.md` for the source baseline.
- See `references/repo-routing-metadata.json` for router placement and usage
  signals.
