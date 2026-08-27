# Run Evaluation Reference

This reference distills Pyserini's evaluation modules and tests into safe, reusable workflows for future agents. It assumes the run file already exists; route run generation to the search or dense sub-skills.

## File Formats

### TREC Run

A TREC run has six whitespace-separated columns:

```text
qid Q0 docid rank score tag
```

Rules that matter for Pyserini:

- `qid` and `docid` should be treated as strings, even if they look numeric.
- Column 2 is conventionally `Q0`; Pyserini's `TrecRun` reads it as the `q0` field.
- `rank` should be a positive integer within each query.
- `score` must parse as a number; higher scores should rank earlier unless the caller passes `--resort` to fusion.
- `tag` identifies the run and can be replaced by fusion through `--runtag`.

### Qrels

A TREC qrels file has four whitespace-separated columns:

```text
qid 0 docid relevance_grade
```

Pyserini's `Qrels` wrapper reads these as `topic`, `q0`, `docid`, and `relevance_grade`. Positive relevance thresholds depend on the metric and test collection; do not assume binary relevance for every collection.

### MS MARCO Run

MS MARCO passage-style runs often use three tab-separated columns:

```text
qid docid rank
```

Use this format with `python -m pyserini.eval.msmarco_passage_eval` or convert it before calling `trec_eval`:

```bash
python -m pyserini.eval.convert_msmarco_run_to_trec_run --input run.msmarco.tsv --output run.trec
```

The converter writes scores as `1 / rank` and uses a fixed run tag. Pyserini's `trec_eval` wrapper also detects some non-`Q0` run files and creates a temporary TREC conversion, but explicit conversion is easier to audit.

## TREC Evaluation

Use `pyserini.eval.trec_eval` when you have a TREC run and qrels path or a Pyserini qrels key:

```bash
python -m pyserini.eval.trec_eval -c -m ndcg_cut.10 -m recall.100 qrels.txt run.trec
python -m pyserini.eval.trec_eval -q -c -m ndcg_cut.10 qrels.txt run.trec
python -m pyserini.eval.trec_eval -c -m judged.20 qrels.txt run.trec
```

Important behavior:

- The wrapper shells out to the bundled Java `trec_eval` class through Pyserini package resources.
- If the qrels argument is not a local file, Pyserini tries to resolve it as a built-in qrels key.
- `-remove-unjudged` filters the run to judged `(qid, docid)` pairs before evaluation.
- `judged.k` is a Pyserini pseudo-metric computed in Python, not a native `trec_eval` metric.
- The Python `trec_eval(args)` helper returns only one aggregate value cleanly; when multiple metrics are requested, parse stdout instead of relying on the return value.

Common metric patterns:

```bash
python -m pyserini.eval.trec_eval -c -m map -m ndcg_cut.10 -m recall.1000 qrels.txt run.trec
python -m pyserini.eval.trec_eval -q -c -M 10 -m recip_rank qrels.txt run.trec
python -m pyserini.eval.trec_eval -c -l 2 -m ndcg_cut.10 -m recall.1000 qrels.txt run.trec
```

Use `-l 2` only when the collection's graded qrels define relevance level 2 as the positive cutoff.

## MS MARCO Evaluation

Pyserini provides wrappers around official MS MARCO evaluation scripts:

```bash
python -m pyserini.eval.msmarco_passage_eval msmarco-passage-dev-subset run.msmarco.tsv
python -m pyserini.eval.msmarco_doc_eval --judgments msmarco-doc-dev run.msmarco.tsv
```

These wrappers may download or locate official evaluation scripts and resolve built-in qrels keys. For offline or tightly controlled work, prefer local qrels/script availability or use TREC conversion plus `trec_eval` when the target metrics match.

## KILT, DPR, And QA Retrieval

Pyserini includes additional evaluators for retrieval result JSON/JSONL workflows:

- `python -m pyserini.eval.convert_trec_run_to_dpr_retrieval_run` converts a TREC run into DPR retrieval JSON by fetching raw passage text from a Lucene index. The index must store raw text.
- `python -m pyserini.eval.evaluate_dpr_retrieval --retrieval run.json --topk 20 100` evaluates answer presence in DPR-style retrieval JSON.
- `python -m pyserini.eval.evaluate_qa_overlap_retrieval --retrieval run.json --topk 20 100 --dataset_name nq` groups answer-overlap statistics, but its annotation resources may need downloads.
- `python -m pyserini.eval.evaluate_kilt_retrieval guess.jsonl gold.jsonl --ks 1,5,10,20 --rank_keys wikipedia_id` evaluates KILT provenance-style retrieval.

Safety checks before using these evaluators:

- Confirm the JSON/JSONL schema, especially `id`, `output`, `provenance`, `answers`, and `contexts` fields.
- Confirm a raw-storing Lucene index before converting a TREC run to DPR JSON.
- Do not trigger implicit annotation/model/data downloads unless the user approved network access.

## `TrecRun` And `Qrels` Helpers

For Python workflows, use `pyserini.trectools`:

```python
from pyserini.trectools import Qrels, RescoreMethod, TrecRun

run = TrecRun('run.trec')
qrels = Qrels('qrels.txt')
print(run.topics())
print(qrels.get_docids(topic='1', relevance_grades=[1, 2]))

judged_only = run.retain_qrels(qrels, clone=True)
judged_only.save_to_txt('run.judged-only.trec')

normalized = run.clone().rescore(RescoreMethod.NORMALIZE)
normalized.save_to_txt('run.normalized.trec')
```

`TrecRun.save_to_txt()` sorts by query and descending score. Use the bundled validator before and after transformations to catch schema, rank, and qrels-overlap problems early.

## Tiny Fixture Pattern

For a deterministic smoke test, create tiny files like these:

```text
# qrels.txt
1 0 D1 1
1 0 D2 0
2 0 D3 1

# run.trec
1 Q0 D1 1 10.0 demo
1 Q0 D2 2 9.0 demo
2 Q0 D4 1 8.0 demo
```

Then run:

```bash
python scripts/validate_trec_run.py run.trec --qrels qrels.txt --summary
python -m pyserini.eval.trec_eval -c -m recall.2 -m judged.2 qrels.txt run.trec
```

The validator should report one unjudged hit (`2/D4`), and `judged.2` should be less than 1.0.
