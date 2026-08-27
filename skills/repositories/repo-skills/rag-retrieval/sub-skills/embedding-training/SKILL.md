---
name: embedding-training
description: "Prepare and validate bundled RAG-Retrieval embedding fine-tuning,
  MRL, and teacher-embedding distillation workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Embedding Training

Use this sub-skill when a user asks to fine-tune a RAG-Retrieval embedding model, train BGE/GTE-style embeddings, validate `training_embedding.yaml` or `distill_embedding.yaml`, configure MRL dimensions, create or merge teacher embeddings, or prepare teacher-embedding distillation.

This is a source-code training workflow, not an installed-package API. This skill bundles selected training scripts/configs under `scripts/training_bundle/` and command builders under `scripts/`; use an external checkout only when the user explicitly wants a current repository checkout. Keep generated configs/data in user-controlled work directories.

## Route by Task

- **Validate config/data first**: Run `scripts/validate_embedding_training_config.py` before launching Accelerate. It checks YAML keys, `train_type`, JSONL schemas, `neg_nums`, `prompt_for_query`, teacher dimensions, and optional teacher array size.
- **Normal fine-tuning**: Use `train_type: train`, a pair/triplet/pair-score JSONL, and the bundled `training_bundle/train_embedding.py` entrypoint via the command builder. See `references/workflows.md` and `references/data-formats.md`.
- **Teacher distillation**: Use `train_type: distill`, a text JSONL containing one `query` row per teacher embedding row, `train_dataset_vec`, `teacher_embedding_dim`, `use_mrl: true`, and compatible `mrl_dims`. See `references/distillation.md`.
- **Merge teacher arrays**: Use `scripts/merge_teacher_embeddings.py` to concatenate two float32 teacher embedding arrays with explicit row counts and dimensions; then set `teacher_embedding_dim` to the summed dimension.
- **Distributed launch choice**: Prefer bundled FSDP Accelerate config for BERT-like embedding models and bundled DeepSpeed ZeRO config for LLM-like embedding models. Use `scripts/build_embedding_training_command.py` to build a path-checked command, then see `references/configuration.md`.
- **Reranker or ColBERT training**: Do not cover those details here. Route to sibling training sub-skills such as `../reranker-training/SKILL.md` or `../colbert-training/SKILL.md` if present; only the Accelerate/config validation pattern is shared.

## Safe Default Sequence

1. Confirm the user has an environment with training dependencies already installed; an external checkout is optional because the skill bundles the selected training code snapshot.
2. Copy or create a working YAML from the embedding training examples; replace source-relative sample paths with the user's actual dataset/output paths.
3. Validate the YAML and JSONL without downloading models:
   ```bash
   python skills/rag-retrieval/sub-skills/embedding-training/scripts/validate_embedding_training_config.py \
     --config /path/to/working_training_embedding.yaml \
     --data /path/to/train.jsonl
   ```
4. For distillation, also validate the teacher array:
   ```bash
   python skills/rag-retrieval/sub-skills/embedding-training/scripts/validate_embedding_training_config.py \
     --config /path/to/working_distill_embedding.yaml \
     --data /path/to/distill_text.jsonl \
     --teacher-embeddings /path/to/teacher_embeddings.mmap
   ```
5. Only after validation, build a launch command with `scripts/build_embedding_training_command.py`, review it, and run a small foreground smoke job before long training.

## Reference Map

- `references/data-formats.md`: Supported JSONL shapes, pair-score expansion, `prompt_for_query`, teacher memmap shape, and validation expectations.
- `references/configuration.md`: YAML keys, MRL options, logging, distributed config choice, bundled training snapshot, and optional checkout caveats.
- `references/workflows.md`: Normal fine-tuning, distillation fine-tuning, bundled launch-command building, validation sequence, and saved-model usage.
- `scripts/build_embedding_training_command.py`: Builds a path-checked `accelerate launch` command for embedding training without copying source scripts.
- `references/distillation.md`: Stella-style teacher embedding creation, safe teacher-array merge, optional synthetic data generation, and expensive/GPU caveats.
- `references/troubleshooting.md`: Common schema, memmap, MRL, download, distributed, and logging failures.
