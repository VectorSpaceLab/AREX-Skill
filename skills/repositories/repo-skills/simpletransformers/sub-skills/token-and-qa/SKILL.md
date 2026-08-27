---
name: token-and-qa
description: "Use Simple Transformers NER/token-classification and extractive
  question-answering APIs, schemas, validators, and troubleshooting routes."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Simple Transformers Token and QA Sub-skill

Use this sub-skill when a task asks for named entity recognition, token
classification, CoNLL data, LayoutLM token boxes, SQuAD-style extractive QA,
answer-span validation, or QA lazy loading with `simpletransformers.ner` or
`simpletransformers.question_answering`.

## Owns

- `NERModel` / `NERArgs` train, eval, and predict workflows.
- NER DataFrame and CoNLL data preparation.
- NER prediction on raw strings or manually tokenized lists.
- LayoutLM token-level bounding-box schemas.
- `QuestionAnsweringModel` / `QuestionAnsweringArgs` train, eval, and predict workflows.
- SQuAD-style list/JSON/JSONL QA records, impossible questions, and answer-span checks.

## Route elsewhere

- Discriminative document/sentence classification: [classification](../classification/SKILL.md).
- T5/generative question answering or question generation: [generative-workflows](../generative-workflows/SKILL.md).
- Dense retrieval before QA or passage indexing: [retrieval-representation](../retrieval-representation/SKILL.md).
- Shared install, CUDA policy, output/cache, and model-arg conventions: root references.

## Read first

1. [API reference](references/api-reference.md) for constructors, common methods, and return shapes.
2. [Data formats](references/data-formats.md) before creating NER or QA inputs.
3. [Workflows](references/workflows.md) for CPU-safe train/eval/predict recipes.
4. [Troubleshooting](references/troubleshooting.md) for answer spans, CoNLL formatting, lazy JSONL, token splitting, model downloads, and dependency compatibility.

## Validation helper

Run the bundled validator before invoking model code:

```bash
python scripts/validate_token_qa_data.py --task ner-csv --input ner.csv
python scripts/validate_token_qa_data.py --task ner-conll --input train.conll
python scripts/validate_token_qa_data.py --task qa-json --input train.json
python scripts/validate_token_qa_data.py --task qa-jsonl --input train.jsonl
python scripts/validate_token_qa_data.py --task qa-predict-json --input predict.json
```

The helper performs deterministic schema and answer-span checks. It does not
import Simple Transformers, download checkpoints, or train models.

## Safe defaults

- Pass `use_cuda=False` for CPU smoke tests.
- Set `no_save=True`, `overwrite_output_dir=True`, and `reprocess_input_data=True` for temporary checks.
- Keep NER sentence ids stable and contiguous enough for debugging, but uniqueness is more important than zero-based numbering.
- For QA, every training answer text must be a substring of `context` and `answer_start` must point to that exact substring.

## Verification status

The NER and QA public constructors were inspected for Simple Transformers 0.70.8. Repo-native tests contain useful tiny data but train/download Hugging Face models, so they are treated as optional final native cases unless network/cache/compute budget is approved.
