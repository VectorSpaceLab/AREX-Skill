# Teacher Embedding Distillation

RAG-Retrieval embedding distillation trains a student sentence-transformer model to match teacher embeddings. The source workflow uses `EmbeddingDistillDataset`, `DistillEmbedding`, and `train_type: distill` in YAML.

## Required Artifacts

Distillation requires:

- A text JSONL file with one `query` record per embedding row.
- A float32 teacher embedding array in the same row order.
- `teacher_embedding_dim` matching the array width.
- A distillation YAML with `train_type: distill` and `train_dataset_vec` pointing to the teacher array.

The source dataset opens raw memmap arrays as:

```python
np.memmap(train_dataset_vec, dtype="float32", mode="r", shape=(line_count, teacher_embedding_dim))
```

If a user has `.npy` arrays, convert or merge with a helper that writes raw memmap when the source trainer is expected to read the output directly.

## Stella-Style Teacher Creation Concept

The source examples include a Stella-style data creation flow:

1. Read original training JSONL.
2. Collect unique `query`, `pos`, and `neg` texts.
3. Encode those texts with a teacher sentence-transformer model.
4. Write a float32 memmap of teacher vectors.
5. Optionally write a `.text.jsonl` file containing the corresponding text rows.

Important caveats:

- Teacher creation can download large models and require GPUs.
- It can be expensive for large corpora because it embeds every unique text.
- If the teacher model needs an instruction prefix, apply the same prompt policy when creating teacher embeddings and when training/inferencing the student.
- Multi-process encoding and huge batch sizes should be tuned to the user's GPU memory.

This sub-skill does not bundle the full teacher-creation script because it depends on `sentence-transformers`, model downloads, CUDA placement, and user-specific model choices. Treat it as reference-only and adapt in the user's working repo when requested.

## Merging Two Teacher Embedding Files

When distilling from two teachers, concatenate embeddings along the last dimension. Both arrays must have the same row count and row order.

Use the bundled safe helper:

```bash
python skills/rag-retrieval/sub-skills/embedding-training/scripts/merge_teacher_embeddings.py \
  --left /path/to/teacher1.mmap --left-dim 1792 \
  --right /path/to/teacher2.mmap --right-dim 1792 \
  --rows 2087 \
  --output /path/to/two_teacher.mmap \
  --output-format memmap
```

Then set:

```yaml
train_dataset_vec: "/path/to/two_teacher.mmap"
teacher_embedding_dim: 3584
use_mrl: true
mrl_dims: "256,512,1024,1536,2048,2560,3072,3584"
```

For `.npy` output instead of source-trainer raw memmap:

```bash
python skills/rag-retrieval/sub-skills/embedding-training/scripts/merge_teacher_embeddings.py \
  --left /path/to/teacher1.npy \
  --right /path/to/teacher2.npy \
  --output /path/to/two_teacher.npy \
  --output-format npy
```

If using `.npy` directly with the source trainer, confirm or adapt the trainer because the source dataset expects raw memmap, not NumPy `.npy` headers.

## Optional Synthetic Pair-Score Data

The source examples also show a FlashRAG/REPLUG-inspired path for creating pair-score JSONL:

1. Retrieve top-k passages for each QA query.
2. Score each passage by the generator likelihood of the answer.
3. Softmax the scores.
4. Write JSONL records with `query`, `pos`, and `scores`.

Treat this as optional reference-only support because it can require:

- FlashRAG installation and configuration.
- A retrieval corpus and FAISS index.
- Local or downloaded LLM/generator weights.
- GPU access and substantial runtime.
- Dataset downloads that may be network-bound or license-sensitive.

For most users, first validate that their target JSONL matches the pair-score schema before attempting to recreate synthetic data generation.

## Distillation Launch Checklist

Before launching Accelerate:

- `train_type` is `distill`.
- `train_dataset` exists and has one valid `query` record per line.
- `train_dataset_vec` exists and has float32 element count `line_count * teacher_embedding_dim`.
- `teacher_embedding_dim` is present or the compatibility typo `teacher_emebedding_dim` is intentionally used.
- `max(mrl_dims) <= teacher_embedding_dim` when `use_mrl: true`.
- `output_dir` has enough storage for checkpoints and final sentence-transformers model.
- Logging backend is available or changed to a local/offline choice.
