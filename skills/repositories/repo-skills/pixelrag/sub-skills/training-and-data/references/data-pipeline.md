# Synthetic Data Pipeline

PixelRAG's training data pipeline generates query -> screenshot chunk pairs with hard negatives from rendered Wikipedia tiles.

## Visual query pipeline

Order:

1. Generate query pairs from screenshot chunks with Gemini.
2. Filter non-self-contained queries with an LLM.
3. Mine hard negatives using a running PixelRAG search API.
4. Filter false negatives with VQA-style checks.
5. Score query naturalness and SimpleQA style fit.
6. Export rows with high naturalness/style fit.
7. Split train/eval/test.
8. Package image shards and JSONL files for Hugging Face.

Representative JSONL fields:

```json
{
  "query": "In what year did ...?",
  "answer": "1992",
  "source_sentence": "...",
  "source_type": "prose",
  "subject": "medicine",
  "chunk_path": "shard_400/.../chunk_0000_00.png",
  "url": "https://...",
  "title": "...",
  "chunk_index": 0,
  "tiles_dir": "...",
  "neg_chunk_paths": ["..."]
}
```

## Text warmup pipeline

Order:

1. Generate query pairs from text passages.
2. Filter self-contained queries.
3. Mine text hard negatives from a text search API.
4. Remove false negatives with LLM review.

Output is used for `--text-warmup-steps` in training.

## Script categories

- Query generation: `generate_query_pairs.py`, `generate_text_query_pairs.py`.
- Filtering: self-contained, hard-negative VQA, strict/naturalness filters.
- Mining: visual and text hard-negative mining against search APIs.
- Export/split/package: retained rows, splits, HF dataset packaging/upload.
- SFT variants: multi-image and reasoning trace preparation under `sft/`.

These scripts are reference-only in this generated skill because they require large tile stores, API keys, cloud/HF resources, and long-running jobs.

## Safe validation before expensive stages

Use the bundled checker on a sample JSONL:

```bash
python pixelrag_training_data_check.py sample.jsonl --max-rows 100 --no-check-paths
```

Check:

- `query` and `answer` are non-empty.
- `chunk_path` exists or is a valid relative path for the intended data root.
- `neg_chunk_paths` is a list when present.
- Train/eval/test splits do not accidentally mix incompatible schemas.

## Cost and credential gates

- Google Cloud ADC or API credentials are needed for Gemini generation/scoring.
- OpenAI key is needed for filtering/grading stages.
- HF token may be needed for large downloads/uploads.
- W&B key is optional if using offline logging.

Never run these stages without explicit budget and credential approval.
