---
name: evaluation-benchmarks
description: "Model selection, benchmark interpretation, Spearman/Pearson/QPS
  analysis, and bounded evaluation planning for text2vec."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# evaluation-benchmarks

Use this sub-skill when you need to choose among text2vec release models, interpret benchmark metrics, summarize existing pair-score files, or plan bounded MTEB / C-MTEB runs.

## Use for
- choosing Chinese CoSENT defaults, multilingual, BGE, or Word2Vec fallback;
- reading Spearman, Pearson, and QPS results;
- summarizing local label/score files;
- planning benchmark runs with explicit download and skip conditions.

## Route elsewhere
- Training command details or fine-tuning recipes -> `training-finetuning`
- Embedding generation / batching / CLI vectorization -> `embeddings`
- Pairwise search / retrieval implementation -> `similarity-search`
- Serving or deployment wrappers -> `serving-deployment`

## Quick model choice
- Chinese question-question matching: `shibing624/text2vec-base-chinese`
- Chinese sentence-to-sentence or short semantic matching: `shibing624/text2vec-base-chinese-sentence`
- Chinese sentence-to-paraphrase / longer text matching: `shibing624/text2vec-base-chinese-paraphrase`
- Multilingual Chinese-English matching: `shibing624/text2vec-base-multilingual`
- Stronger short-text discrimination, slower throughput: `shibing624/text2vec-bge-large-chinese`
- Cold-start or lexical fallback on CPU: `w2v-light-tencent-chinese`

For large-scale retrieval/search or dedup, hand off to the separate `similarities` package after choosing a model.

## Bundled references
- `references/model-overview.md`
- `references/evaluation-workflows.md`
- `references/troubleshooting.md`

## Bundled script
- `scripts/summarize_scores.py` — summarize CSV/JSONL label/score files into a JSON report.

Example:
```bash
python scripts/summarize_scores.py \
  --input-file scores.csv \
  --label-column label \
  --score-column score \
  --output-file summary.json
```

## Guardrails
- Use the source tables and report findings only; do not claim a universal leaderboard winner.
- Treat QPS as hardware-specific throughput, not a portable ranking.
- If benchmark data or model files are unavailable, prefer a bounded summary or mark the run blocked instead of guessing.
