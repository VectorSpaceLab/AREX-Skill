---
name: hf-training-reranking
description: "Build safe SPLADE HuggingFace Trainer, reranker-training, rerank,
  and post-training handoff commands."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# HF Training and Reranking

Use this sub-skill when a task asks for SPLADE HuggingFace Trainer training, DPR/dense-vs-sparse flags, multiple hard negatives, reranker training, or applying a reranker to a SPLADE run. The runtime entry points are `python -m splade.hf_train`, `python -m splade.hf_train_reranker`, and `python -m splade.rerank`.

## Route First

- For HF SPLADE/DPR training, read `references/hf-training.md` and use `scripts/splade_hf_command_builder.py hf-train`.
- For training or applying rerankers, read `references/reranking.md` and use `scripts/splade_hf_command_builder.py hf-train-reranker` or `rerank`.
- For accepted training-file layouts and hard-negative formats, read `references/data-formats.md` before forming overrides.
- For failures around data types, negatives, checkpoints, optional reranker dependencies, or distributed launch, read `references/troubleshooting.md`.
- For classic post-training indexing and retrieval commands, use this sub-skill only for the handoff template, then route details to `../hydra-pipelines/SKILL.md`.
- For model internals, tensor shapes, and broader SPLADE data APIs, route to `../model-data-api/SKILL.md`.
- For Anserini, PISA, BEIR, pruning, and external evaluation workflows, route to `../pruning-export-evaluation/SKILL.md`.

## Fast Command Builder

The bundled helper prints commands only; it does not train models, import SPLADE, or download checkpoints.

```bash
python skills/splade/sub-skills/hf-training-reranking/scripts/splade_hf_command_builder.py hf-train \
  --config-name config_hf_splade_sigir23_32neg_distil \
  --checkpoint-dir '<CHECKPOINT_DIR>' \
  --index-dir '<INDEX_DIR>' \
  --out-dir '<OUT_DIR>' \
  --training-data-type json \
  --training-data-path '<HARD_NEGATIVES_JSON>' \
  --document-path '<COLLECTION_RAW_TSV>' \
  --query-path '<QUERIES_RAW_TSV>' \
  --qrels-path '<QRELS_JSON>' \
  --n-negatives 4 \
  --nproc-per-node 2
```

## What Good Output Includes

- A launch command with `--config-name`, `config.checkpoint_dir`, and all required `hf.data.*` paths when overriding data.
- A data validation note naming the `training_data_type`, the needed path files, and whether `n_negatives` is valid.
- A model-mode note explaining `hf.model.dense`, `hf.model.shared_weights`, `hf.model.splade_doc`, and `init_dict.model_type_or_dir_q` when relevant.
- A post-training note that `splade.hf_train` saves the final model under `config.checkpoint_dir/model`, then classic `splade.index` and `splade.retrieve` consume that checkpoint via Hydra configs.
