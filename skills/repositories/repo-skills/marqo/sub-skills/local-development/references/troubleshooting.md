# Local development troubleshooting

This guide covers local environment, service, build, and test failures. Route API payload semantics, index/search internals, and model payload semantics to their owning sub-skills.

## Python 3.11 and package installation

Symptoms:

- `ModuleNotFoundError` for `marqo`, `marqo_common`, `inference_orchestrator`, or `model_management`.
- `uv sync` installs but imports still resolve to a different environment.
- Tests fail during collection because dependencies are missing.

Checks:

```bash
python --version
which python
which uv
```

Fix pattern:

```bash
# choose the component root that matches the task
cd components/marqo          # or components/inference_orchestrator or components/model_management
uv sync --group dev
. .venv/bin/activate
export PYTHONPATH=./src
python -c "import sys; print(sys.version)"
python -c "import marqo; print('marqo ok')"  # for components/marqo only
```

If using conda instead of `uv`, create/activate a Python 3.11 environment, install the component in editable or local mode, and still set `PYTHONPATH=./src` for source-tree test runs.

For Docker builds, build from `components/`, not from a component subdirectory. A wrong build context can make `common/` unavailable and break image builds.

## `.env`, `uv`, conda, and environment variables

Symptoms:

- Compose uses unexpected images or profiles.
- Marqo API cannot reach Vespa or remote inference.
- Tests pass in one shell and fail in another.

Fix pattern:

```bash
# from repository root
test -f .env && set -a && . ./.env && set +a
env | grep -E '^(MARQO|VESPA|TRITON|COMPOSE|ZOOKEEPER)_' | sort
```

Prefer setting variables explicitly in the command or test when the value affects assertions. Do not rely on ambient shell state for reproducible tests.

## Docker and compose

Symptoms:

- `docker compose up` fails before services start.
- GPU profile fails with NVIDIA device errors.
- Ports are already in use.
- Model cache volume behaves unexpectedly.

Checks:

```bash
docker version
docker compose version
docker ps
lsof -i :8882 -i :8883 -i :8884 -i :8000 -i :8001 -i :8002 -i :8080 -i :19071 -i :2181
```

Fix pattern:

1. Run `docker compose ... config` first and inspect resolved services/profiles.
2. Use `--profile cpu` unless the task explicitly requires CUDA and the host has NVIDIA drivers plus container toolkit.
3. Confirm no other local task is using ports `8882`, `8883`, `8884`, `8000`, `8001`, `8002`, `8080`, `19071`, or `2181`.
4. Build component images from the `components/` context.
5. Stop/remove containers only after confirming they are not needed by another task.

## Vespa and Zookeeper

Symptoms:

- Marqo API reports Vespa connection failures.
- Index creation or deployment lock operations hang/fail.
- Integration tests cannot create/search indexes.

Checks:

```bash
curl -s http://localhost:19071/state/v1/health
curl -s http://localhost:8080/state/v1/health
docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
```

Fix pattern:

```bash
cd components/marqo
PYTHONPATH=./src python scripts/vespa_local/vespa_local.py full-start
```

Then set:

```bash
export VESPA_CONFIG_URL=http://localhost:19071
export VESPA_DOCUMENT_URL=http://localhost:8080
export VESPA_QUERY_URL=http://localhost:8080
export ZOOKEEPER_HOSTS=localhost:2181
```

For multi-node Vespa, verify every printed API/config URL before running tests. Watch memory use: config and API nodes are heavier than content nodes.

## Triton, MMC, and MIOC

Symptoms:

- `/vectorise` cannot load a model.
- Model-management calls fail to contact Triton.
- Triton starts but no models can be loaded.

Checks:

```bash
curl -s http://localhost:8000/v2/health/ready
curl -s http://localhost:8883/v1/healthz
curl -s http://localhost:8884/healthz
```

Fix pattern:

- Ensure Triton has a model repository mounted at `/models` or the configured model cache path.
- Ensure MMC uses the Triton REST URL (`http://localhost:8000` locally, `http://triton:8000` inside compose).
- Ensure MIOC uses the Triton gRPC URL (`http://localhost:8001` locally, `http://triton:8001` inside compose) and the MMC URL.
- Start with CPU/random-model tests before running HF/OpenCLIP/model-download scenarios.
- Use GPU compose profile only after `nvidia-smi` and Docker GPU support are confirmed.

## Redis and throttling

Symptoms:

- Local API logs warn about Redis connection problems.
- Concurrency throttling tests fail or skip.

Facts:

- Redis is optional for ordinary local API operation.
- Docker-based Marqo setups can provide Redis automatically, but outside-Docker runs may need a local Redis server.
- To intentionally run without throttling warnings, set:

```bash
export MARQO_ENABLE_THROTTLING=FALSE
```

Use Redis only when the task specifically validates throttling/concurrency behavior.

## API server process lifecycle

Symptoms:

- API tests fail with connection refused.
- API server starts but cannot create indexes.
- Uvicorn process remains after tests.

Fix checklist:

1. Start Vespa and verify health.
2. Start Marqo API on port `8882` with `PYTHONPATH=./src`, `MARQO_ENABLE_BATCH_APIS=true`, and Vespa URLs set.
3. Confirm `curl -s http://localhost:8882/` returns a Marqo response and `/health` is reachable.
4. Run API tests from the API-test component root.
5. Terminate the API server process after the tests.

If API startup fails, do not run API tests. Diagnose logs first.

## Maven/JDK custom searcher build

Symptoms:

- Hybrid/search/ranking behavior differs from Java expectations.
- Vespa app deployment fails after Java code changes.
- Maven compilation or Error Prone fails.

Checks:

```bash
cd components/marqo/vespa
java -version
mvn -version
mvn clean package
```

Requirements and facts:

- JDK source/target is 17.
- The Maven artifact is `marqo-custom-searchers` with `container-plugin` packaging.
- Spotless and Error Prone run during Maven build.
- If `HybridSearcher.java` changes, rebuild the jar and redeploy the Vespa application package before trying service tests again.

## Test `PYTHONPATH` and working directory

Symptoms:

- Tests cannot import the component under test.
- Test collection imports installed packages instead of source changes.

Fix pattern:

```bash
cd components/marqo
PYTHONPATH=./src pytest tests/unit_tests/path/to/test_file.py -q

cd components/inference_orchestrator
PYTHONPATH=./src pytest tests/unit_tests/path/to/test_file.py -q

cd components/model_management
PYTHONPATH=./src pytest tests/unit_tests/path/to/test_file.py -q
```

For API tests:

```bash
cd components/marqo
PYTHONPATH=./tests/api_tests/v1/tests/api_tests pytest tests/api_tests/v1/tests/api_tests/test_health.py -q
```

## API test server lifecycle and destructive data

API tests can create/delete indexes and documents. Before running them:

- Verify the target is local/disposable.
- Ensure no production credentials or URLs are exported.
- Use a unique test index prefix if manually constructing tests.
- Shut down only the process/container you started; do not remove shared containers without approval.

## Transient network/proxy failures

Symptoms:

- Docker pulls fail.
- `uv sync` or model downloads fail with timeouts, DNS errors, 5xx, overloaded, or capacity messages.

Fix pattern:

1. Do not delete partially generated artifacts or caches solely because of a transient network failure.
2. Re-enable the environment's proxy/network helper if one is available, then retry the same command.
3. Retry idempotent downloads/build dependency resolution after a short delay.
4. If quota or authentication is exhausted, stop and report the blocker rather than looping indefinitely.

## Maintainer rules to re-check during fixes

- Keep imports at the top.
- Make semi-structured index changes in `semi_structured_vespa_index`, not only in `structured_vespa_index`.
- Core code raises `marqo.core.exceptions` or `marqo.exceptions`, not `marqo.api.exceptions`.
- Unit tests mirror source package hierarchy.
- New or changed tests must be run before completion.
