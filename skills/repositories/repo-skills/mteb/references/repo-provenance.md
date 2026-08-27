# Repo Provenance

schema: disco.repo-provenance.v1

## Source Snapshot

- Repository: `embeddings-benchmark/mteb`
- Remote URL: `https://github.com/embeddings-benchmark/mteb.git`
- Commit: `691f39211da598ca12fe3244fe4fac49e68892fd`
- Branch: `main`
- Exact tag: none detected
- Working tree state at generation: dirty because the generated `skills/` directory was added during skill creation
- Package distribution: `mteb`
- Package version: `2.15.6`
- Python support from package metadata: `>=3.10,<3.15`

## Evidence Paths

- `pyproject.toml`
- `README.md`
- `mteb/__init__.py`
- `mteb/evaluate.py`
- `mteb/get_tasks.py`
- `mteb/filter_tasks.py`
- `mteb/cli/`
- `mteb/abstasks/`
- `mteb/tasks/`
- `mteb/models/`
- `mteb/benchmarks/`
- `mteb/cache/`
- `mteb/results/`
- `mteb/leaderboard/`
- `docs/get_started/`
- `docs/api/`
- `docs/contributing/`
- Representative tests under `tests/test_cli.py`, `tests/test_evaluate.py`, `tests/test_get_tasks.py`, `tests/test_filter_tasks.py`, `tests/test_benchmarks/`, `tests/test_models/`, `tests/test_results/`, `tests/test_tasks/`, and `tests/test_validate_metadata/`

## Excluded Or Summarized Evidence

- `mteb/descriptive_stats/`: large generated task statistics; only formats and contribution implications were summarized.
- `docs/images/`, `docs/stylesheets/`, `docs/javascripts/`: static documentation assets not needed by runtime skill users.
- `tests/mock_mteb_cache/`, `tests/historic_results/`, and generated result fixtures: useful for native verification but not copied into runtime skill content.
- Bulk `scripts/data/**` and upload scripts: dataset-building or credential/network-heavy maintainer workflows; distilled only as contribution context.
- Optional model, audio, image, leaderboard, and provider extras: documented as workflow-specific optional dependencies instead of installed or assumed globally.

## Refresh Guidance

Refresh this skill when MTEB changes public API signatures, CLI subcommands, task/benchmark filtering defaults, result cache schemas, model protocol requirements, contribution metadata requirements, or optional dependency names. In particular, re-check `mteb --help`, `mteb.evaluate`, `mteb.get_tasks`, `mteb.get_model`, `ResultCache`, and model-card metadata commands after each MTEB release.
