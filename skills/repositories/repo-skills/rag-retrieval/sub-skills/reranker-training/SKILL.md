---
name: reranker-training
description: "Set up and validate BERT or LLM reranker training, dataset
  formats, ranking losses, and LLM-to-BERT distillation for RAG-Retrieval."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Reranker Training

Use this sub-skill when a user wants to train or fine-tune a RAG-Retrieval reranker, choose between pointwise and grouped training data, configure BERT or LLM reranker models, debug ranking-loss behavior, or distill an LLM reranker teacher into BERT reranker data.

Natural triggers include: “train reranker”, “fine-tune bge/bce reranker”, “pointwise vs grouped reranker data”, “RankNet/listwise CE”, “Qwen LLM decoder reranker”, and “distill LLM reranker to BERT”.

## Route By Task

- For JSONL training-data shape, labels, `label_key`, `max_label`, `min_label`, group sizes, and skipped samples, read [references/data-formats.md](references/data-formats.md).
- For `training_bert.yaml`, `training_llm.yaml`, model/loss compatibility, LLM prompt formatting fields, mixed precision, distributed configs, and logging, read [references/configuration.md](references/configuration.md).
- For bundled command building, BERT and LLM training flow, validation order, saved checkpoints, and handoff to inference, read [references/workflows.md](references/workflows.md).
- For LLM teacher scoring and converting teacher outputs into BERT pointwise data, read [references/distillation.md](references/distillation.md).
- For common failures such as missing labels, disappearing grouped samples, incompatible loss/data choices, LLM formatting, DeepSpeed save issues, and memory pressure, read [references/troubleshooting.md](references/troubleshooting.md).

## Bundled Helper

Run the bundled validator before launching training:

```bash
python skills/rag-retrieval/sub-skills/reranker-training/scripts/validate_reranker_training_config.py \
  --config <training-config.yaml> \
  --data <train-data.jsonl>
```

The helper only reads YAML and JSONL. It does not import model code, instantiate tokenizers, download checkpoints, or allocate GPU memory.

## Scope Boundaries

- This sub-skill covers `train_reranker.py`, `PointwiseRankerDataset`, `GroupedRankerDataset`, `ranking_loss.py`, BERT encoder training, LLM decoder training, training configs, LLM-to-BERT distillation planning, and `scripts/build_reranker_training_command.py` for path-checked launch commands.
- It intentionally excludes embedding and ColBERT data formats except for shared Accelerate, DeepSpeed, and mixed-precision concepts.
- It intentionally excludes inference API details except for handing saved reranker checkpoints to the sibling reranker inference guidance.
