# Evaluation troubleshooting

| Symptom | Likely cause | Safe action |
|:--|:--|:--|
| Benchmark wants to download a model or dataset | MTEB/C-MTEB and release-style benchmarks require model caches and task data. | Confirm network/cache budget first. If unavailable, skip the run and summarize existing local scores only. |
| SOHU, STS-B, ATEC, BQ, LCQMC, PAWSX, MTEB, or C-MTEB data is missing | The benchmark inputs are not present locally or the download did not complete. | Mark that dataset/task unavailable. Do not impute a score or average it silently. |
| Scores from two datasets look inconsistent | Different datasets have different domains, label scales, and main metrics. | Compare models within the same dataset/protocol. Report cross-dataset averages only when the included dataset list is explicit. |
| QPS is much lower than the release table | Hardware, device backend, batch size, precision, sequence length, or implementation differs. | Treat local QPS as environment-specific. Compare only under matched settings; the release GPU table used a Tesla V100 32GB setup. |
| `summarize_scores.py` skips rows | Label or score values are missing, nonnumeric, infinite, NaN, or in the wrong column. | Fix column names with `--label-column` / `--score-column`, normalize labels to numbers, then rerun. Keep skipped-row counts in the report. |
| Spearman or Pearson is `null` | Fewer than two valid rows, constant labels, constant scores, or metric backend returned undefined correlation. | Add valid variance to the test set or report the metric as unavailable. Do not replace undefined with zero. |
| Spearman is negative or unexpectedly low | Label polarity may be reversed, scores may be from the wrong pair order, data may be out-of-domain, or the model may rank pairs poorly. | Inspect a few high/low examples, check whether higher labels mean more similar, and verify that each score is aligned to the intended pair. |
| BGE retrieval results change after adding query prefixes | Retrieval/reranking tasks may use model-family-specific query instructions. | Keep instruction prefixes fixed across compared models, and state whether an instruction was used. |
| A recommendation seems too strong | Source release tables are evidence from specific datasets and hardware, not a universal leaderboard. | Phrase recommendations by task: Chinese general, s2s, s2p, multilingual, BGE short-text discrimination, or Word2Vec lexical fallback. |
| User asks for large-scale retrieval/search benchmarking | text2vec model selection is not the whole search system. | Evaluate the model here, then route retrieval/search implementation and scale concerns to `similarity-search` or the separate `similarities` package. |
