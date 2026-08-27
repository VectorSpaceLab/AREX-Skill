---
name: evaluation-and-fusion
description: "Evaluate Pyserini run files, convert run formats, fuse retrieval
  runs, and use reproducibility matrices safely."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Evaluation And Fusion

Use this sub-skill when the task involves `trec_eval`, qrels, TREC/MS MARCO/KILT/DPR/QA retrieval evaluation, run-file validation, run conversion, reciprocal-rank fusion, interpolation, score normalization, or Pyserini two-click reproducibility matrices.

Do not use this sub-skill to generate search runs from an index. Route Lucene indexing/search/fetch workflows to `../index-search-fetch/SKILL.md`, dense encoding/Faiss/hybrid retrieval generation to `../dense-encoding/SKILL.md`, and Java/eval-jar/source-checkout build failures to `../install-and-runtime/SKILL.md` or `../repo-development/SKILL.md`.

## Quick Routing

- **TREC evaluation:** Validate a six-column TREC run and qrels, then run `python -m pyserini.eval.trec_eval` with explicit metrics.
- **MS MARCO evaluation:** Keep three-column MS MARCO runs for `msmarco_passage_eval`/`msmarco_doc_eval`, or convert to six-column TREC before `trec_eval`.
- **KILT, DPR, and QA retrieval:** Use the dedicated JSON/JSONL evaluators only after checking the expected schema and avoiding implicit annotation downloads.
- **Run filtering:** Use `pyserini.trectools.TrecRun` and `Qrels` to inspect topics, retain or discard judged documents, normalize scores, or write a clean TREC run.
- **Fusion:** Use `python -m pyserini.fusion` for `rrf`, `interpolation`, `average`, and `normalize` on valid TREC runs with compatible query/document identifiers.
- **Reproducibility matrices:** Prefer `--display-commands --dry-run` first; treat full two-click commands as opt-in because they may download indexes, models, topics, qrels, or runs.

## Default Safe Workflow

1. Validate the candidate run before evaluation or fusion:

   ```bash
   python scripts/validate_trec_run.py run.trec --qrels qrels.txt --strict-ranks --summary
   ```

2. If the run is MS MARCO format, convert it before using `trec_eval`:

   ```bash
   python -m pyserini.eval.convert_msmarco_run_to_trec_run --input run.msmarco.tsv --output run.trec
   ```

3. Evaluate with explicit metrics and a qrels key or qrels path:

   ```bash
   python -m pyserini.eval.trec_eval -c -m ndcg_cut.10 -m recall.100 qrels.txt run.trec
   ```

4. Build a fusion command without executing it:

   ```bash
   python scripts/fusion_recipe_builder.py --method rrf --runs bm25.trec dense.trec --output fused.trec --runtag demo --k 100 --depth 1000
   ```

5. Validate the fused run and evaluate it with the same qrels and metrics as the input runs.

## References

- `references/run-evaluation.md` covers TREC, MS MARCO, KILT, DPR, QA, `TrecRun`, `Qrels`, qrels aliases, and common metrics.
- `references/reproducibility.md` explains two-click reproduction modules, dry-run/display-command safety, nondeterminism, and matrix triage.
- `references/troubleshooting.md` maps malformed runs, run/qrels mismatches, missing eval jars, unjudged documents, and expensive reproduction failures to fixes.
- `scripts/validate_trec_run.py --help` validates TREC runs and qrels without importing Pyserini or starting Java.
- `scripts/fusion_recipe_builder.py --help` generates reproducible Pyserini fusion commands with method-specific checks.

## Acceptance Checklist

- Confirm whether the run is six-column TREC or three-column MS MARCO before choosing an evaluator.
- Keep query IDs and document IDs as strings; do not coerce them to integers unless a specific evaluator requires it.
- Use the same qrels/topic split and metric definitions for baseline, candidate, and fused runs.
- Validate every input run before fusion and validate the fused output before evaluation.
- Treat prebuilt-index reproduction and neural retrieval commands as network/model/cache-sensitive unless the user has explicitly approved them.
