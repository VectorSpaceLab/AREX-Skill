# Reproducibility Reference

Pyserini emphasizes reproducible first-stage retrieval. Its documentation and `pyserini.2cr` modules provide two-click reproduction matrices that pair run-generation commands with evaluation commands. Use them deliberately: they are excellent ground truth, but many full commands download prebuilt indexes, topics, qrels, model weights, or run files.

## Terminology

Pyserini follows ACM artifact terminology:

- **Repeatability:** Same team, same experimental setup.
- **Reproducibility:** Different team, same experimental setup.
- **Replicability:** Different team, different setup.

When a user says they want to reproduce a Pyserini result, first keep the same Pyserini workflow, index, topics, qrels, metrics, and run settings. Changing model checkpoints, encoders, indexing flags, inference hardware, or qrels versions turns the task into a replication or new experiment.

## Two-Click Reproduction Pattern

The reproducibility modules under `pyserini.2cr` share a practical shape:

1. List available collections, conditions, languages, or splits.
2. Display the underlying search/fusion/evaluation commands.
3. Optionally run a single condition or the full matrix.
4. Evaluate produced run files with `pyserini.eval.trec_eval` or task-specific evaluators.
5. Optionally generate an HTML report.

Safe discovery commands generally look like this:

```bash
python -m pyserini.2cr.beir --list-conditions
python -m pyserini.2cr.beir --condition bm25-flat --display-commands --dry-run
python -m pyserini.2cr.miracl --list-languages
python -m pyserini.2cr.miracl --language en --condition bm25 --display-commands --dry-run
```

Prefer discovery and dry-run modes before executing matrix commands. Full matrix execution can be expensive even when each printed command is correct.

## Matrix Families

Common two-click families include:

- MS MARCO V1/V2 passage and document retrieval.
- BEIR sparse, dense, and fused conditions.
- Mr.TyDi and MIRACL multilingual retrieval.
- CIRAL African-language retrieval.
- Open-domain QA retrieval with DPR-style JSON conversion and evaluation.
- Multimodal or newer benchmark families where optional dependencies and datasets may be larger.

Use the matrix only to select known-good command shapes. If the user asks for a small local validation, create or use a tiny run/qrels fixture instead of running a benchmark matrix.

## Nondeterminism Cautions

Sparse BM25 runs over fixed indexes and fixed topics should generally be stable. Learned sparse, dense, and neural retrieval workflows may vary because:

- On-the-fly query encoding can differ across CPU, GPU, OS, library versions, and precision settings.
- Document encoding and learned sparse weights can differ if corpus representations are regenerated.
- Model downloads may resolve to updated files unless revisions are pinned.
- Approximate nearest-neighbor indexes and GPU kernels may introduce score/rank differences.

For reproducibility claims, record the Pyserini version, index identifier, topics/qrels key, command, metric flags, and whether the run used pre-tokenized/pre-encoded inputs or on-the-fly neural inference.

## Fusion In Reproduction Matrices

Some matrices combine runs through RRF or score-based fusion. Treat the component runs as part of the provenance:

```bash
python -m pyserini.fusion --method rrf --runs sparse.trec dense.trec --output fused.trec --runtag rrf --k 1000 --depth 1000
python -m pyserini.eval.trec_eval -c -m ndcg_cut.10 -m recall.100 qrels.txt fused.trec
```

Before trusting a fused run:

- Validate every component run.
- Confirm all component runs use the same topic split and document-id namespace.
- Confirm the fusion method, `--rrf.k`, `--alpha`, `--depth`, and final `--k` match the matrix.
- Evaluate component runs and fused runs with identical qrels and metric flags.

## Execution Policy

Use this decision order:

1. **User wants command discovery:** Run `--list-*`, `--display-commands`, or `--dry-run` only.
2. **User wants local run evaluation:** Validate and evaluate the provided run/qrels files; do not fetch benchmark resources.
3. **User wants a one-condition reproduction:** Explain expected downloads and runtime, then run only that condition if approved.
4. **User wants full matrix reproduction:** Confirm disk, network, runtime, model/backend requirements, and output location first.
5. **User reports score mismatch:** Compare command flags, index/topic/qrels keys, run format, metric flags, Pyserini version, and neural nondeterminism before rerunning expensive commands.

## Evidence-Grounded Native Checks

Safe native candidates for verification are fixture-level evaluation and fusion checks, not full matrix execution. In particular:

- `trec_eval` tests validate aggregate, per-query, and `judged.k` behavior on small run/qrels resources.
- `TrecRun`/`Qrels` tests validate reading, topic enumeration, qrels filtering, and score normalization.
- Fusion tests include safe simple TREC run fixtures for `rrf`, `interpolation`, `average`, and `normalize`.
- Heavier fusion tests that instantiate prebuilt indexes, encoders, or Faiss should be skipped unless the user explicitly wants those downloads and dependencies.
