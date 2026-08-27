---
name: splade
description: "Route SPLADE sparse retrieval tasks across Hydra pipelines, HF
  training/reranking, model/data APIs, and export/pruning/evaluation workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# SPLADE Repo Skill

Use this skill when a user asks about the SPLADE Python repository: sparse lexical retrieval with masked-language-model expansion, classic Hydra train/index/retrieve workflows, HuggingFace Trainer variants, reranking, Anserini export, static pruning, BEIR/PISA evaluation planning, or SPLADE data/API troubleshooting.

## First Decision

- Choose `sub-skills/hydra-pipelines/SKILL.md` for classic `python -m splade.*` workflows: `all`, `train`, `index`, `retrieve`, `evaluate`, `flops`, and `create_anserini` command construction.
- Choose `sub-skills/hf-training-reranking/SKILL.md` for `python -m splade.hf_train`, `python -m splade.hf_train_reranker`, `python -m splade.rerank`, multiple hard negatives, dense/DPR variants, and reranker workflows.
- Choose `sub-skills/model-data-api/SKILL.md` for programmatic model/data/index APIs, SPLADE representation behavior, toy-data validation, and no-download API inspection.
- Choose `sub-skills/pruning-export-evaluation/SKILL.md` for Anserini export files, static pruning helpers, BEIR/PISA planning, Pyserini/Java/PISA prerequisites, and evaluation dependency troubleshooting.

## Public Install Baseline

- For a local SPLADE checkout, install the package with `python -m pip install -e .` from the checkout root.
- For a fresh public install, use `python -m pip install git+https://github.com/naver/splade.git` and then add workflow-specific dependencies such as PyTorch, Hydra/OmegaConf, `pytrec-eval`, Pyserini, Java, or PISA only when the selected route needs them.
- Prefer Python 3.8 or 3.9-era ML environments for historical SPLADE compatibility; newer environments may need Hydra/OmegaConf adjustments described in `references/troubleshooting.md`.

## Core Package Facts

- Distribution metadata uses package name `SPLADE` and import package `splade`; the repo version is `2.1`.
- The installed metadata declares `transformers==4.18.0` and `omegaconf==2.1.2`, but current source uses some Hydra decorators with `version_base="1.2"`; see `references/troubleshooting.md` before diagnosing Hydra import errors.
- Classic training/index/retrieval relies on Hydra config files under `conf/` and typically needs `config.checkpoint_dir`, `config.index_dir`, and `config.out_dir` overrides because defaults leave them as `???`.
- Evaluation and reranking paths import `pytrec_eval`; full metric execution may require building `pytrec-eval` and external `trec_eval` sources.
- Realistic training, indexing, BEIR, Anserini, and PISA runs may require GPUs, large model/data downloads, Java/Pyserini, PISA binaries, or long runtimes; do not launch them unless the user approves those costs.

## Safe Starting Checks

- Validate that SPLADE imports before deeper work: `python -c "import splade; print('ok')"`.
- Inspect command templates instead of running jobs: `python sub-skills/hydra-pipelines/scripts/splade_hydra_command_builder.py --help`.
- Inspect HF command templates: `python sub-skills/hf-training-reranking/scripts/splade_hf_command_builder.py --help`.
- Validate small SPLADE-style fixtures: `python sub-skills/model-data-api/scripts/validate_splade_toy_data.py <dataset-root>`.
- Prune self-contained Anserini-style JSONL fixtures with `sub-skills/pruning-export-evaluation/scripts/prune_doc_index.py` or `prune_quantile.py`.

## Shared References

- Read `references/repo-provenance.md` to check the source commit, dirty state, version, and evidence baseline before deciding whether this skill is stale.
- Read `references/troubleshooting.md` for cross-cutting install/import, Hydra/OmegaConf, optional dependency, data/download, and hardware failures.
- Read `references/repo-routing-metadata.json` only when updating DisCo routing metadata.

## Routing Patterns

| User asks for | Read |
| --- | --- |
| "Run SPLADE on toy data", "train/index/retrieve", "Hydra override", "checkpoint config missing" | `sub-skills/hydra-pipelines/SKILL.md` |
| "HF Trainer", "hard negatives", "DPR/dense", "rerank a run", "RankT5/monoT5" | `sub-skills/hf-training-reranking/SKILL.md` |
| "What are the model signatures?", "validate raw.tsv/qrels", "content_id KeyError", "offline inference API" | `sub-skills/model-data-api/SKILL.md` |
| "create Anserini docs", "prune SPLADE index", "BEIR", "PISA", "pyserini/trec_eval" | `sub-skills/pruning-export-evaluation/SKILL.md` |

## Workflow Guardrails

- Do not point users to original repo docs, notebooks, shell scripts, or source files as runtime dependencies; use this skill's bundled references and scripts.
- Command-builder scripts print commands only; review placeholders and resource requirements before running generated commands.
- Treat native SPLADE examples/tests as verification candidates, not automatic runtime steps.
- Prefer safe `--help`, schema validation, and tiny-fixture checks before GPU training, downloads, BEIR, Anserini, or PISA execution.
