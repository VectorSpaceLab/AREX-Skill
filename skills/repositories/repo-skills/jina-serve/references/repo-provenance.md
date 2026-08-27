# Repo Provenance

schema: disco.repo-provenance.v1

## Source snapshot

- Source project: Jina-serve / `jina`
- Public remote URL: `https://github.com/jina-ai/serve.git`
- Git commit: `0f32b2aaac71d31d55de5b074196938033aaff7e`
- Branch: `master`
- Exact tag: none found for this checkout
- Working tree state during generation: dirty because generated skill/review artifacts were untracked under `skills/`; no source-code changes were used as package evidence.
- Package distribution: `jina`
- Import package: `jina`
- CLI entry point: `jina=jina_cli:main`
- Package version: `3.34.1`
- Python version used for private inspection: Python 3.10 (do not treat this as the only supported user runtime)

## Relative evidence paths consulted

- Package metadata: `setup.py`, `pyproject.toml`, `MANIFEST.in`, `extra-requirements.txt`, `requirements.txt`, `pytest.ini`
- Public source roots: `jina/`, `jina_cli/`
- Templates/resources: `jina/resources/project-template/`, `jina/resources/health_check/`, `jina/resources/base-gateway/`, `jina/resources/completions/`
- Documentation: `README.md`, `docs/get-started/`, `docs/concepts/serving/`, `docs/concepts/orchestration/`, `docs/concepts/client/`, `docs/cloud-nativeness/`, `docs/concepts/jcloud/`, `docs/envs/index.md`, `docs/telemetry.md`, `docs/tutorials/`
- Behavior evidence: `tests/unit/test_cli.py`, `tests/unit/test_yamlparser.py`, `tests/unit/test_importer.py`, `tests/unit/test_gateway.py`, `tests/integration/flow_dry_run/`, `tests/integration/deployments/`, `tests/integration/gateway_clients/`, `tests/integration/streaming/`, `tests/integration/v2_api/`, `tests/integration/monitoring/`, `tests/integration/rr_cuda/`
- Operational evidence: `Dockerfiles/`, `conda/meta.yaml`, `.github/workflows/ci.yml`, `.github/workflows/cd.yml`, `.github/workflows/nightly-tests.yml`

## Refresh triggers

Refresh this skill if any of these change materially:

- Public imports from `jina.__init__`, especially `Executor`, `Flow`, `Deployment`, `Client`, `requests`, `dynamic_batching`, or `monitor`.
- CLI command layout in `jina.parsers` or `jina_cli`.
- Dependency extras or default dependency set in `extra-requirements.txt` and `setup.py`.
- DocArray/Pydantic/Protobuf/GRPC compatibility guidance.
- Flow/Gateway protocol configuration, export formats, or observability APIs.
- JCloud/Hub command behavior, credential requirements, or package names.
