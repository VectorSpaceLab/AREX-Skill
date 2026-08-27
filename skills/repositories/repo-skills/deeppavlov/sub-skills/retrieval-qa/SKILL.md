---
name: retrieval-qa
description: "Use DeepPavlov retrieval, ranking, FAQ, SQuAD, ODQA, and KBQA
  workflows with correct config, data, index, and input/output choices."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# retrieval-qa

Use this sub-skill when a DeepPavlov task involves questions, contexts, documents, document IDs, ranking scores, FAQ categories, answer spans, ODQA pipelines, or Wikidata-style KBQA queries.

## Route quickly

- Generic DeepPavlov config syntax, nested `config_path`, `overwrite`, registry, train/evaluate/predict modes, and component wiring: [../pipelines/SKILL.md](../pipelines/SKILL.md).
- Generic text classification, NER, entity extraction, spelling, syntax, morphology, embedders, or relation extraction outside retrieval/QA: [../text-models/SKILL.md](../text-models/SKILL.md).
- REST or socket deployment after a retrieval/QA config runs locally: [../serving/SKILL.md](../serving/SKILL.md).
- Shared install/import/cache/backend problems: [../../references/troubleshooting.md](../../references/troubleshooting.md).

## Start here

1. Choose the workflow family in [references/model-catalog.md](references/model-catalog.md): `doc_retrieval`, `ranking`, `squad`, `odqa`, `kbqa`, or `faq`.
2. Prepare the required local data/index layout with [references/data-and-indexing.md](references/data-and-indexing.md).
3. For a safe local document-retrieval template, generate a two-document config with [scripts/tiny_retrieval_config.py](scripts/tiny_retrieval_config.py).
4. Diagnose retrieval/QA-specific failures with [references/troubleshooting.md](references/troubleshooting.md) before escalating to root troubleshooting.

## Decision hints

- Use `squad` when every question has an explicit context batch.
- Use `odqa` when the user supplies only questions and expects retrieval plus answer extraction over a document collection.
- Use `doc_retrieval` when the deliverable is document IDs/titles/scores rather than answer spans.
- Use `ranking` for response ranking or KBQA relation/path ranking; route ordinary classifiers to `text-models`.
- Use `kbqa` for Wikidata-style entity/relation/query generation outputs.
- Use `faq` for fastText/logistic-regression FAQ intent/category lookup or simple CSV FAQ corpora.

Do not reopen the original repository checkout for runtime guidance; use the bundled references and scripts in this sub-skill tree.
