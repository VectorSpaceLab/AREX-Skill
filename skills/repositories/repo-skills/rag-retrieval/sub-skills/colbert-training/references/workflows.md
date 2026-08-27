# ColBERT Training Workflows

## Source-Checkout Training Launch

Use the bundled ColBERT training snapshot by default. After validating data, build a path-checked launch command with the bundled command builder:

```bash
python skills/rag-retrieval/sub-skills/colbert-training/scripts/build_colbert_training_command.py \
  --dataset <triplet-train.jsonl> \
  --output-dir <output-dir> \
  --model-name-or-path hfl/chinese-roberta-wwm-ext \
  --colbert-dim 768 \
  --neg-nums 15 \
  --devices 0,1
```

Pass `--checkout <rag-retrieval-checkout>` only when the user explicitly wants to run a current external checkout instead of this skill's bundled snapshot.

For `BAAI/bge-m3`, switch to an XLM-RoBERTa FSDP config and use `--colbert_dim 1024` unless the user is intentionally training a fresh projection dimension.

## Preflight Validation Sequence

Before launching a multi-GPU job:

1. Run the bundled validator against the triplet JSONL and intended ColBERT arguments.
2. Inspect warnings about rows with fewer negatives than `neg_nums`; decide whether to mine more negatives or accept resampling.
3. Confirm the backbone family and FSDP layer class match: `BertLayer` for BERT-style models, `XLMRobertaLayer` for `BAAI/bge-m3`/XLM-RoBERTa-style models.
4. Confirm `CUDA_VISIBLE_DEVICES` count matches the accelerate config `num_processes`.
5. Run a tiny smoke job first when changing data format, tokenizer family, or `colbert_dim`.

Example validation command:

```bash
python sub-skills/colbert-training/scripts/validate_colbert_training_args.py \
  --data train.jsonl \
  --neg-nums 15 \
  --colbert-dim 1024 \
  --model-name-or-path BAAI/bge-m3 \
  --query-max-len 128 \
  --passage-max-len 512
```

## Saved Model Scoring

After training, the final saved model is under `output_dir/model`. Current packaged `Reranker` does not provide a registered ColBERT inference route, so saved ColBERT checkpoints require the bundled/source-code model class or a custom registered ranker.

When the training snapshot or equivalent checkout code is importable, the scoring pattern is:

```python
from rag_retrieval.train.colbert.model import ColBERT

model_dir = "output/my_colbert_run/model"
colbert = ColBERT.from_pretrained(model_dir, colbert_dim=1024, cuda_device="cuda:0")
colbert.eval().to("cuda:0")

pairs = [
    ["What is BGE M3?", "BGE M3 supports dense retrieval, lexical matching, and multi-vector interaction."],
    ["What is BGE M3?", "BM25 is a sparse bag-of-words ranking function."],
]
scores = colbert.compute_score(pairs, query_max_len=128, passage_max_len=512)
```

`compute_score` returns one late-interaction relevance score per query-document pair. Higher scores are more relevant within the same model/run. Keep scoring batch size, query length, and passage length consistent with the hardware and training assumptions.

## Inference Limitation Cross-Link

Do not route saved ColBERT checkpoints through installed package `Reranker(..., model_type="colbert")` unless the current source explicitly registers a working `ColBERTRanker`. The source may map `model_type="colbert"` to `ColBERTRanker`, while the ranker registry omits that class, causing the packaged route to return `None` or report missing dependencies.

For packaged reranking questions, direct the user to the repo skill’s inference guidance and explain that ColBERT scoring currently requires bundled/source-code `ColBERT.from_pretrained` access or a custom registered ranker.
