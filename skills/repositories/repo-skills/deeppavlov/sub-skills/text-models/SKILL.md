---
name: text-models
description: "DeepPavlov workflows for text classification, tagging, extraction,
  spelling, syntax, relation, multitask, regression, and embeddings."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Text Models

Use this sub-skill for DeepPavlov model families that operate on texts, tokens, spans, relations, labels, scores, or embeddings.

## Route Here

- Text classification, sentence-pair classification, multiple-choice classification, few-shot classification, benchmark classification, and scalar text scoring.
- NER, sentence segmentation, morpho-syntax parsing, and other token-level tagging workflows.
- Entity detection, entity linking, and relation extraction workflows.
- Spelling correction workflows.
- Multitask workflows that share one backbone across several text heads.
- BERT-style and sentence-level embedding workflows, including the standalone embedding configs.

## Reroute Elsewhere

- Core config syntax, nested configs, registry behavior, custom components, and train/evaluate plumbing -> [pipelines](../pipelines/SKILL.md).
- Document retrieval, ranking, FAQ, SQuAD, ODQA, and KBQA workflows -> [retrieval-qa](../retrieval-qa/SKILL.md).
- REST and socket deployment, ports, payloads, probes, and response framing -> [serving](../serving/SKILL.md).
- Cross-cutting install/import/backend/cache issues -> the [root troubleshooting reference](../../references/troubleshooting.md) once it is present in the generated skill tree.

## Fast Workflow

1. Run `scripts/list_config_categories.py` to confirm the live config inventory in the installed package.
2. Match the task shape to `references/model-catalog.md`.
3. Use `references/data-formats.md` for `chainer.in` / `chainer.out` shapes and safe batching rules.
4. If the task needs config surgery, reader changes, iterator changes, or custom components, switch to [pipelines](../pipelines/SKILL.md).
5. If the task is about exposing an already-selected model over HTTP or sockets, switch to [serving](../serving/SKILL.md).

## References

- [Model catalog](references/model-catalog.md)
- [Data formats](references/data-formats.md)
- [Troubleshooting](references/troubleshooting.md)
- [Config inventory script](scripts/list_config_categories.py)
