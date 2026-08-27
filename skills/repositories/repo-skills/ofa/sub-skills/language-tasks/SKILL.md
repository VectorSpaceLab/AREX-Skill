---
name: language-tasks
description: "Guides OFA Gigaword summarization and GLUE-style language
  understanding workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# language-tasks

Use this sub-skill when a user wants to run OFA's language-only or mostly language workflows: Gigaword summarization or GLUE-style classification framed as seq2seq generation.

## Trigger phrases

- "Run Gigaword"
- "ROUGE evaluation for OFA"
- "Train CoLA / MNLI / QQP / RTE / SST-2 with OFA"
- "Why does `datasets.load_metric` fail?"
- "What selected columns do the GLUE tasks use?"

## What this sub-skill owns

- Gigaword training and ROUGE evaluation,
- GLUE task families (CoLA, MNLI, MRPC, QNLI, QQP, RTE, SST-2),
- prompt-type guidance for classification-as-generation,
- ROUGE JSON helper usage,
- task-specific selected columns and label mappings.

## What it excludes

- visual entailment -> `vision-language-tasks`,
- pretraining -> `pretraining`,
- image-generation workflows -> `image-generation`,
- speech workflows -> `mmspeech`.

## Read these files

- [references/workflows.md](references/workflows.md) for the Gigaword and GLUE workflow shapes.
- [references/troubleshooting.md](references/troubleshooting.md) for metric and data-layout failures.
- [scripts/eval_rouge_json.py](scripts/eval_rouge_json.py) for offline ROUGE evaluation from prediction JSON.

## Typical workflow

1. Identify the GLUE task or summarization task.
2. Confirm the selected columns and split names.
3. Decide whether the task is evaluation-only or includes finetuning.
4. Use the bundled ROUGE helper when you need a standalone metric check.

## Notes

- Gigaword uses a plain source/target pair.
- GLUE tasks are represented as seq2seq classification with yes/no/maybe style outputs.
- The same base OFA architecture is reused across these tasks; the data layout is what changes most.
