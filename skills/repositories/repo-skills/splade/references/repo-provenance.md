# SPLADE Repo Provenance

## Source Snapshot

- Source repository: SPLADE
- Source remote: `https://github.com/naver/splade`
- Commit: `8dcd33a054d790e74aceda25b128c1b188c5d9c1`
- Branch: `main`
- Exact tag: none detected
- Package distribution: `SPLADE`
- Package version: `2.1`
- Working tree state at generation: dirty because DisCo generated `skills/` runtime and review artifacts in this checkout

## Dirty-State Summary

Generated runtime files were created under `skills/splade/`. Review/test artifacts were also created in the repository's DisCo artifact area.

No pre-existing source changes were detected before skill generation.

## Evidence Paths

Primary source evidence:

- `setup.py`
- `README.md`
- `conda_splade_env.yml`
- `splade/`
- `conf/`
- `main_config/`
- `data/toy_data/`
- `pruning/`
- `benchmarking_sigir23/README.md`
- `efficient_splade_pisa/README.md`
- `inference_splade.ipynb`

Generated skill evidence also used private inspection logs and review artifacts, but public runtime guidance is distilled here without local environment paths.

## Refresh Signals

Refresh this skill when any of these change materially:

- `setup.py` dependency pins or package version.
- Hydra entry points under `splade/*.py` or config layout under `conf/`.
- HuggingFace Trainer modules under `splade/hf/`.
- Data-loader schemas under `splade/datasets/` or `splade/hf/datasets.py`.
- Export/evaluation/pruning behavior under `splade/create_anserini.py`, `splade/beir_eval.py`, `splade/evaluation/`, or `pruning/`.
- README quick-start, model catalog, or external dependency guidance.
