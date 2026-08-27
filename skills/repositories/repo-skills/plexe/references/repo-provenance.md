# Plexe Repo Provenance

- Schema: `disco.repo-provenance.v1`

This skill was distilled from a clean checkout of the Plexe repository.
It is intended to stay aligned with the public repository snapshot below.

## Source snapshot

- Repository: Plexe
- Remote URL: https://github.com/plexe-ai/plexe
- Commit: `a1e05f6dc4c0875e0075f3b6f020fbecef57a699`
- Branch: `main`
- Tag: `v1.4.4`
- Working tree: clean at extraction time
- Package version: `1.4.4`
- Extraction mode: `agent-decide`
- Import after verification: not requested

## Evidence paths used

- `README.md`
- `AGENTS.md`
- `pyproject.toml`
- `setup.py`
- `Makefile`
- `Dockerfile`
- `config.yaml.template`
- `examples/local/spaceship_titanic.py`
- `plexe/main.py`
- `plexe/workflow.py`
- `plexe/retrain.py`
- `plexe/config.py`
- `plexe/models.py`
- `plexe/helpers.py`
- `plexe/integrations/base.py`
- `plexe/integrations/standalone.py`
- `plexe/integrations/storage/*.py`
- `plexe/execution/dataproc/*.py`
- `plexe/execution/training/*.py`
- `plexe/search/*.py`
- `plexe/templates/training/*.py`
- `plexe/templates/inference/*.py`
- `plexe/templates/packaging/model_card_template.py`
- `plexe/utils/dashboard/*.py`
- `plexe/utils/parquet_dataset.py`
- `plexe/utils/reporting.py`
- `plexe/utils/s3.py`
- `plexe/utils/tracing.py`
- `plexe/validation/validators.py`
- `tests/unit/*`
- `tests/integration/*`

## Staleness notes

- This generated skill should be refreshed if the public API, CLI flags, supported
  model families, package layout, or dashboard workdir assumptions change.
- The dashboard and model-building references assume the same artifact layout that
  existed at the snapshot above.

