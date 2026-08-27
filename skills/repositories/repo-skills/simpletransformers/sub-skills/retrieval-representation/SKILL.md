---
name: retrieval-representation
description: "Use Simple Transformers representation, dense retrieval, DPR,
  BEIR/MSMARCO, hard-negative, and retrieval-evaluation workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Simple Transformers Retrieval and Representation Sub-skill

Use this sub-skill when a task asks for sentence/word embeddings,
`RepresentationModel.encode_sentences`, dense retrieval with query/context
encoders, DPR-style training, hard negatives, BEIR/MSMARCO/TREC data, FAISS
indexes, or retrieval metrics.

## Owns

- `RepresentationModel` for hidden-state/token/word/sentence representations.
- `RetrievalModel` / `RetrievalArgs` for dense retrieval train/eval/predict.
- `PretrainRetrievalModel` as an advanced pretraining route.
- Retrieval data schemas: `query_text`, `gold_passage`, optional `title`, prediction queries, BEIR/MSMARCO/TREC conversion.
- Optional `faiss`, `pytrec_eval`, and `beir` branches.

## Route elsewhere

- Cross-encoder sentence-pair classification reranking: [classification](../classification/SKILL.md).
- T5/monoT5 text-to-text reranking: [generative-workflows](../generative-workflows/SKILL.md).
- Extractive QA after passage retrieval: [token-and-qa](../token-and-qa/SKILL.md).

## Read first

1. [API reference](references/api-reference.md) for constructors and method map.
2. [Data formats](references/data-formats.md) before preparing retrieval or representation inputs.
3. [Workflows](references/workflows.md) for encode, train/eval/predict, and optional evaluation routes.
4. [Troubleshooting](references/troubleshooting.md) for optional dependencies, cache/index files, hard-negative shapes, and dependency compatibility.

## Validation helper

```bash
python scripts/validate_retrieval_data.py --task retrieval-csv --input train.csv
python scripts/validate_retrieval_data.py --task query-lines --input queries.txt
python scripts/validate_retrieval_data.py --task beir-corpus-jsonl --input corpus.jsonl
python scripts/validate_retrieval_data.py --task beir-queries-jsonl --input queries.jsonl
python scripts/validate_retrieval_data.py --task tsv --input train.tsv
```

The helper checks file shape only. It does not import FAISS, build indexes,
download datasets, train encoders, or run BEIR evaluation.

## Key decisions

- Use `RepresentationModel` when the output is embeddings or token vectors.
- Use `RetrievalModel` when the task includes query/passage training, hard negatives, or retrieval prediction.
- Decide whether evaluation needs built-in metrics only, `pytrec_eval`, or full BEIR evaluation.
- Install FAISS only for workflows that actually build or load FAISS indexes.
- Keep CPU for small smoke checks; CUDA is performance acceleration, not required for schema validation.

## Verification status

Constructor signatures were inspected with compatibility warnings. Native representation/retrieval examples require checkpoint/dataset downloads and optional dependencies, so default verification uses validators and static/API evidence unless the user approves larger checks.
