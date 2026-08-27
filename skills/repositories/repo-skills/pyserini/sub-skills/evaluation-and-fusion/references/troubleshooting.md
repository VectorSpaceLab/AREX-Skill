# Evaluation And Fusion Troubleshooting

## `trec_eval` Cannot Find A Jar Or Starts Java Incorrectly

Symptoms:

- Importing or running `python -m pyserini.eval.trec_eval` fails before reading the run.
- Errors mention missing package resources, no jar files, Java classpath, or Java/JVM setup.

Likely cause: the Pyserini runtime or source checkout is missing required bundled resources or Java is not configured. Route installation/runtime diagnosis to `../../install-and-runtime/SKILL.md`; route source-maintainer jar/submodule builds to `../../repo-development/SKILL.md`.

## Malformed TREC Run

Symptoms:

- `trec_eval` reports parse errors or silently returns surprising results.
- Fusion fails while reading a run.
- The bundled validator reports wrong column count, non-integer ranks, non-numeric scores, duplicate `(qid, docid)` pairs, or rank-order violations.

Fix:

```bash
python scripts/validate_trec_run.py run.trec --strict-ranks --summary
```

Repair the file to exactly six whitespace-separated columns: `qid Q0 docid rank score tag`. If the run came from MS MARCO output, convert it explicitly instead of hand-editing:

```bash
python -m pyserini.eval.convert_msmarco_run_to_trec_run --input run.msmarco.tsv --output run.trec
```

## MS MARCO And TREC Formats Are Mixed

Symptoms:

- A three-column run is passed to `python -m pyserini.fusion`.
- A six-column TREC run is passed to `msmarco_passage_eval`.
- Scores differ after conversion from MS MARCO format.

Fix: choose the evaluator first. Use MS MARCO evaluators for original three-column runs when the task requires official MS MARCO metrics. Convert to TREC only when using `trec_eval`, `TrecRun`, qrels filtering, or fusion. Remember that the standard converter assigns score `1 / rank`, so score-based interpolation after conversion may not preserve original score semantics.

## Qrels Do Not Match The Run

Symptoms:

- `judged.k` is low or zero.
- All metrics are zero despite plausible search results.
- Validator reports missing run topics, missing qrels topics, or many unjudged hits.

Fix:

```bash
python scripts/validate_trec_run.py run.trec --qrels qrels.txt --summary --max-unjudged-examples 20
```

Then check:

- Topic split names match exactly, such as dev vs test or passage vs document.
- Document IDs use the same namespace and segmentation scheme.
- Query IDs are not accidentally coerced, truncated, or prefixed differently.
- The qrels path/key is for the intended task and collection.

## Unjudged Documents Dominate Metrics

Symptoms:

- `judged.k` is low.
- Results look strong by recall but weak under judged-only metrics.
- The task asks to compare only judged hits.

Fix options:

- Report `judged.k` alongside effectiveness metrics.
- Use Pyserini's `-remove-unjudged` option when the analysis explicitly requires judged-only evaluation:

  ```bash
  python -m pyserini.eval.trec_eval -c -m ndcg_cut.10 -m judged.10 qrels.txt run.trec -remove-unjudged
  ```

- Use `TrecRun.retain_qrels(qrels)` to write a judged-only run for inspection, but do not confuse it with the original submitted run.

## Fusion Output Looks Wrong

Symptoms:

- Fused run has missing topics, duplicated documents, unexpected ranks, or scores much larger/smaller than expected.
- Interpolation fails or gives unintuitive results.

Fix:

1. Validate all input runs:

   ```bash
   python scripts/validate_trec_run.py sparse.trec --summary
   python scripts/validate_trec_run.py dense.trec --summary
   ```

2. Confirm all runs cover the same topic split and document-id namespace.
3. For interpolation, pass exactly two runs and choose `--alpha` intentionally; Pyserini computes `alpha * first_run_score + (1 - alpha) * second_run_score`.
4. For RRF, tune `--rrf.k` separately from output `--k`; `--rrf.k` is the rank damping constant and defaults to 60.
5. Use `--depth` to restrict how many documents from each input run participate, and final `--k` to restrict output per query.
6. Use `--resort` only when the input run ranks do not reflect descending scores and you want Pyserini to reorder by score before fusion.

## KILT, DPR, Or QA Evaluator Fails

Symptoms:

- JSON schema assertions fail.
- A converter cannot fetch passage text.
- Evaluation attempts to download annotations or topics unexpectedly.

Fix:

- Validate JSON/JSONL schema before evaluation.
- For DPR conversion, ensure the Lucene index stores raw text and contains the run's `docid` values.
- For KILT, ensure `guess` and `gold` contain unique IDs and matching order after validation.
- Avoid QA-overlap annotation downloads unless the user explicitly approves network access.

## Reproduction Matrix Is Too Slow Or Downloads Too Much

Symptoms:

- A two-click command starts downloading large prebuilt indexes, models, topics, qrels, or benchmark files.
- Full matrix execution takes much longer than expected.

Fix:

- Stop and switch to `--display-commands --dry-run` when available.
- Run a single condition/language/split before full matrices.
- Ask the user to approve network, disk, model, and runtime requirements for full reproduction.
- For score-debugging, compare printed commands and existing run files before rerunning retrieval.
