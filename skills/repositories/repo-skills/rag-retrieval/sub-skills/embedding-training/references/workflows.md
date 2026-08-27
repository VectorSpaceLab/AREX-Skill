# Embedding Training Workflows

These workflows prepare RAG-Retrieval embedding training from the bundled training snapshot without launching expensive jobs until config and data are validated. Pass `--checkout` to the command builder only when the user explicitly wants a current external checkout.

## Normal Fine-Tuning

Use this path for pair, triplet, or pair-score JSONL.

1. Ask for the training data path and whether the user wants the bundled training snapshot or a specific external checkout.
2. Create a working YAML from the source `training_embedding.yaml` example.
3. Replace example dataset/output paths with user-controlled paths.
4. Choose FSDP or DeepSpeed according to model family and available hardware.
5. Validate YAML and data locally:
   ```bash
   python skills/rag-retrieval/sub-skills/embedding-training/scripts/validate_embedding_training_config.py \
     --config /path/to/training_embedding.yaml \
     --data /path/to/train.jsonl
   ```
6. If validation passes, use the bundled command builder to create a path-checked launch command:
   ```bash
   python skills/rag-retrieval/sub-skills/embedding-training/scripts/build_embedding_training_command.py \
     --config <working-training-embedding.yaml> \
     --backend fsdp \
     --devices 0,1
   ```
7. For LLM-like embedding models, switch the builder to DeepSpeed ZeRO-2:
   ```bash
   python skills/rag-retrieval/sub-skills/embedding-training/scripts/build_embedding_training_command.py \
     --config <working-training-embedding.yaml> \
     --backend deepspeed \
     --devices 0,1
   ```

Notes:

- The builder defaults to the skill-owned `scripts/training_bundle/` snapshot and shared `scripts/accelerate_configs/`; add `--checkout <rag-retrieval-checkout>` only for an explicit current checkout.
- The builder prints the command; review it and avoid `nohup` until a foreground dry run or short smoke run has proven the command resolves files.
- Pair-score JSONL uses `scores` in raw data; the dataset expands those values into singular `score` entries internally.

## Distillation Fine-Tuning

Use this path when teacher embeddings already exist or will be created first.

1. Build or obtain a text JSONL with one `query` row per teacher embedding row.
2. Confirm teacher array dtype is float32 and row order matches the text JSONL.
3. If two teacher arrays need to be combined, merge them first:
   ```bash
   python skills/rag-retrieval/sub-skills/embedding-training/scripts/merge_teacher_embeddings.py \
     --left /path/to/teacher_a.mmap --left-dim 1792 \
     --right /path/to/teacher_b.mmap --right-dim 1792 \
     --rows 2087 \
     --output /path/to/two_teacher.mmap \
     --output-format memmap
   ```
4. Set `teacher_embedding_dim` to the final teacher width, such as `3584` for two `1792`-wide teachers.
5. Create a working YAML from the source `distill_embedding.yaml` example.
6. Validate the YAML, text JSONL, and teacher array:
   ```bash
   python skills/rag-retrieval/sub-skills/embedding-training/scripts/validate_embedding_training_config.py \
     --config /path/to/distill_embedding.yaml \
     --data /path/to/distill_text.jsonl \
     --teacher-embeddings /path/to/two_teacher.mmap
   ```
7. Build the launch command with the checkout's FSDP config unless model size requires DeepSpeed:
   ```bash
   python skills/rag-retrieval/sub-skills/embedding-training/scripts/build_embedding_training_command.py \
     --config <working-distill-embedding.yaml> \
     --backend fsdp \
     --devices 0,1
   ```

## Validation Sequence

Run validation in layers:

- `--config` only: catches YAML syntax, missing required keys, unsupported `train_type`, malformed MRL dims, logging values, and teacher dimension key issues.
- `--config --data`: also checks JSONL shape, line counts, pair/triplet/pair-score compatibility, score alignment, and prompt usage.
- `--config --data --teacher-embeddings`: also checks distillation row/dimension shape against `.mmap` or `.npy` teacher arrays.

Validation is not a substitute for a small training smoke run because it does not instantiate the model/tokenizer or import distributed libraries.

## Saved Model Usage

The source trainer saves the final model under:

```text
output_dir/model
```

and epoch/step checkpoints under the run checkpoint directory. The saved final model uses sentence-transformers format, so downstream usage can be either the source `Embedding.from_pretrained(...)` wrapper or the `sentence_transformers.SentenceTransformer` API.

Minimal downstream pattern:

```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("/path/to/output/model")
embeddings = model.encode(["example query"])
```

When MRL is used, choose the embedding slice dimension consistently with the retrieval/indexing strategy. If an index is built at 768 dimensions, query embeddings should be sliced to the same dimension before search.

## Shared Setup Cross-Link

Reranker and ColBERT training workflows may share Accelerate, FSDP, DeepSpeed, logging, and environment setup concepts. Keep task-specific data/model details in their own sub-skills; this sub-skill owns only embedding and embedding-distillation training.
