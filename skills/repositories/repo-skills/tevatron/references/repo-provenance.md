# Repository Provenance

## Purpose

Read this before deciding whether this Tevatron skill is current for a checkout. If the current repository commit, dirty state, package version, major evidence paths, or public workflow layout differs from this snapshot, run `refresh-repo-skill`.

## Snapshot

| Field | Value |
| --- | --- |
| Repository | Tevatron |
| Skill id | `tevatron` |
| VCS | git |
| Commit | `f0fc1e8b73ecda0075e69bed66ab72611413979e` |
| Branch | `main` |
| Exact tag | none detected |
| Remote URL | https://github.com/texttron/tevatron |
| Package distribution | `tevatron` |
| Package version | `0.0.1` |
| Source layout | `src/tevatron` via `setup.py` |
| Generated from dirty checkout | yes, because this generated `skills/` tree is untracked during creation |

## Dirty State Notes

At the start of repository analysis, no tracked source modifications were reported. During skill generation, the new `skills/` directory became untracked. Treat the source commit above plus the evidence paths below as the baseline for Tevatron behavior.

## Evidence Paths

- `setup.py` for package name, version, source layout, and base dependencies.
- `README.md` for project purpose, installation variants, Tevatron 101, LoRA/DeepSpeed/JAX examples, data schema examples, and end-to-end retrieval flow.
- `docs/datasets.md`, `docs/training.md`, `docs/encoding.md`, and `docs/retrieval.md` for canonical public workflow guidance.
- `src/tevatron/retriever/` for retriever arguments, datasets, collators, training drivers, encoding drivers, FAISS search, model classes, GradCache, and Tevax/JAX routes.
- `src/tevatron/reranker/` for cross-encoder reranker arguments, datasets, collators, model/trainer classes, train driver, and rerank driver.
- `src/tevatron/utils/format/` for ranking and rerank input conversion behavior.
- `scripts/reduce_results.py`, `scripts/hn_mining.py`, `scripts/eval_beir.sh`, and `scripts/dataset_transform_scripts/` for useful helper workflows and source-script import decisions.
- `deepspeed/ds_zero0_config.json` and `deepspeed/ds_zero3_config.json` for public DeepSpeed configuration patterns.
- `examples/` for model- and dataset-specific workflows including reranker, SPLADE, UniCOIL, distillation, RepLLaMA, RankLLaMA, ColPali, DSE, Qwen, multimodal, BEIR, MS MARCO, DPR, MrTyDi, SciFact, ReasonIR, and BrowseComp-Plus examples.

## Installed Package Inspection Baseline

The package was installed in a private inspection environment and verified with:

- `python -m pip check`: passed.
- Distribution metadata for `tevatron`: version `0.0.1`, top-level import `tevatron`.
- Import `tevatron`: passed.
- Safe smoke checks for retriever/reranker argument dataclasses and FAISS searcher helpers: passed.

Optional execution stacks such as `torch`, `peft`, `deepspeed`, `jax`, `flax`, `optax`, `vllm`, and Qwen utilities were not treated as required for public skill creation. They remain workflow-specific dependencies documented in the relevant sub-skills.

## Refresh Triggers

Refresh this skill when any of these change:

- `setup.py` package name, version, source layout, base dependencies, or Python support.
- Public docs under `docs/` or `README.md` change training, encoding, retrieval, data, reranking, multimodal, or install behavior.
- Any driver module under `src/tevatron/retriever/driver/` or `src/tevatron/reranker/driver/` changes public arguments, output formats, or optional dependency behavior.
- Dataset schemas, collator behavior, media field handling, or reranker input/output formats change.
- Utility scripts for ranking conversion, rerank input preparation, result reduction, BEIR evaluation, hard-negative mining, or dataset transforms change.
- Examples introduce or remove major supported workflows, models, backends, or configuration patterns.
