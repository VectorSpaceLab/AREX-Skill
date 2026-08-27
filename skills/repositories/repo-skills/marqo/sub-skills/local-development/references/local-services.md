# Local services and development topology

This reference distills Marqo's local development and service-operation facts. Commands are written relative to a repository checkout and must be reviewed before execution. They are intentionally separated from API payload details and model/index internals, which belong to other sub-skills.

## Environment baseline

- Marqo service components target Python 3.11. The main API package requires Python `>=3.11,<3.12`; the inference orchestrator and model-management service use the same Python range; the shared common package requires Python `>=3.11`.
- Use an activated virtual environment before running commands. `uv sync --group dev` is the component-native way to prepare test dependencies for Marqo API, inference orchestrator, and model management.
- Load the repository `.env` when using compose or local services. The distilled defaults are:
  - `TRITON_VERSION=25.08-py3`
  - `VESPA_VERSION=8.513.17`
  - `COMPOSE_PROFILES=cpu`
  - `VESPA_DISK_USAGE_LIMIT=0.75`
- Always set `PYTHONPATH=./src` when running Python commands from a component root.
- The installed package identities observed during construction were `marqo-api 0.0.1`, `marqo-common 0.1.0`, `marqo-inference-orchestrator 0.0.1`, and `marqo-model-management 0.0.1`.

Safe preparation sketch:

```bash
# from repository root
test -f .env && set -a && . ./.env && set +a
python --version

# main Marqo API component
cd components/marqo
uv sync --group dev
. .venv/bin/activate
PYTHONPATH=./src python -c "import marqo; print('marqo import ok')"
```

For the shared `marqo-common`, Docker builds require the `components/` directory as the build context so the component Dockerfiles can copy `common/` and install it as a local dependency.

## Service map

| Service | Component/package | Typical port(s) | Primary local role | Required backing services |
|---|---:|---:|---|---|
| Marqo API | `components/marqo`, `marqo-api` | `8882` | Public API, index/document/search/typeahead routes | Vespa for persistent index/search; optional remote inference; optional Redis throttling |
| Vespa | local Vespa app package | `8080`, `19071`, `2181` | Document/query/config endpoints and Zookeeper lock coordination | Docker; Java/Maven build if custom searcher changes |
| Triton | NVIDIA Triton | `8000`, `8001`, `8002` | Model execution backend | Docker; GPU profile optionally reserves NVIDIA device |
| Model management container (MMC) | `components/model_management` | `8883` | Load/unload models into Triton | Triton REST URL and model cache volume |
| Inference orchestrator (MIOC) | `components/inference_orchestrator` | `8884` | `/vectorise`, preprocessing, cache, model-management client | Triton gRPC URL and MMC URL |
| Redis | external/local package | default Redis port | Optional concurrency throttling | Only needed when throttling must work without warnings |

## Docker compose topologies

All compose commands are service-mutating. First run `docker compose ... config` to inspect resolved settings.

### Full split-component stack

`compose.yaml` defines a complete Marqo environment with Triton, Marqo API, MMC, MIOC, and Vespa-facing API configuration. It uses compose profiles `cpu` and `gpu` for Triton variants.

Key facts:

- Compose project name: `marqo-all-components`.
- API port: `8882`; MIOC: `8884`; MMC: `8883`; Triton: `8000` HTTP, `8001` gRPC, `8002` metrics.
- API service uses `MARQO_REMOTE_INFERENCE_URL=http://mioc:8884`.
- API service expects Vespa/Zookeeper on host-gateway URLs: config `19071`, document/query `8080`, Zookeeper `2181`.
- MMC and MIOC share the `modelrepo` volume with Triton.
- GPU profile reserves one NVIDIA GPU for Triton.

Plan:

```bash
# from repository root
test -f .env && set -a && . ./.env && set +a
docker compose --profile cpu -f compose.yaml config
# after review and explicit approval:
docker compose --profile cpu -f compose.yaml up --build
```

Use `--profile gpu` only after verifying NVIDIA drivers and container toolkit availability.

### Inference-only stack

`compose-inference.yaml` starts Triton + MMC + MIOC and exposes MIOC `/vectorise` on port `8884`. Use it for inference-orchestrator integration checks that do not require the Marqo API.

```bash
docker compose --profile cpu -f compose-inference.yaml config
# after review and explicit approval:
docker compose --profile cpu -f compose-inference.yaml up --build
```

### Model-management + Triton stack

`compose-model-management.yaml` starts Triton + MMC and exposes MMC on port `8883`. Use it for model-management integration checks without MIOC or the Marqo API.

```bash
docker compose --profile cpu -f compose-model-management.yaml config
# after review and explicit approval:
docker compose --profile cpu -f compose-model-management.yaml up --build
```

### Triton-only stack

`compose-triton.yaml` starts only Triton and mounts the model cache into `/models`. It supports `cpu` and `gpu` profiles.

```bash
docker compose --profile cpu -f compose-triton.yaml config
# after review and explicit approval:
docker compose --profile cpu -f compose-triton.yaml up
```

## Local Vespa plan

Marqo integration and API tests require a running Vespa instance. The local Vespa helper is destructive because it starts/stops containers and deploys the local application package.

Single-node plan:

```bash
cd components/marqo
PYTHONPATH=./src python scripts/vespa_local/vespa_local.py full-start
curl -s http://localhost:19071/state/v1/health
curl -s http://localhost:8080/state/v1/health
```

Separated start/deploy plan:

```bash
cd components/marqo
PYTHONPATH=./src python scripts/vespa_local/vespa_local.py start
PYTHONPATH=./src python scripts/vespa_local/vespa_local.py deploy-config
```

Multi-node plan, only if needed and enough memory is available:

```bash
cd components/marqo
PYTHONPATH=./src python scripts/vespa_local/vespa_local.py full-start --Shards 2 --Replicas 1
```

Important Vespa facts:

- Single-node Vespa maps config `19071`, document/query `8080`, Zookeeper `2181`, and debug `5005`.
- Multi-node runs three config nodes, content nodes equal to `shards * (1 + replicas)`, and API nodes equal to at least two or the content-node count.
- Local disk utilization is governed by `VESPA_DISK_USAGE_LIMIT`; default distilled value is `0.75`.
- If you changed the custom Java searcher, rebuild with Maven and redeploy the Vespa app package before service validation.

## Local Marqo API plan

For local API development outside Docker, run the API from the Marqo component root with Vespa already reachable.

```bash
cd components/marqo
export PYTHONPATH=./src
export MARQO_ENABLE_BATCH_APIS=true
export MARQO_LOG_LEVEL=debug
export MARQO_MODELS_TO_PRELOAD=[]
export VESPA_CONFIG_URL=http://localhost:19071
export VESPA_DOCUMENT_URL=http://localhost:8080
export VESPA_QUERY_URL=http://localhost:8080
export ZOOKEEPER_HOSTS=localhost:2181
uvicorn marqo.tensor_search.api:app --host 0.0.0.0 --port 8882 --reload
```

For API tests that exercise batch APIs, also set `MARQO_MODE=COMBINED` when the test plan requires it.

Health checks:

```bash
curl -s http://localhost:8882/
curl -s http://localhost:8882/health
curl -s http://localhost:8882/openapi.json > marqo-openapi.json
```

If Redis is not running, local API startup can still succeed but throttling may be disabled with warnings. To intentionally suppress throttling warnings during local runs:

```bash
export MARQO_ENABLE_THROTTLING=FALSE
```

## Inference orchestrator local plan

The inference orchestrator is a FastAPI service around preprocessing, caching, model loading, and Triton inference. It can be run directly for development, but model-backed integration requires Triton and model-management URLs.

```bash
cd components/inference_orchestrator
uv sync --group dev
. .venv/bin/activate
export PYTHONPATH=./src
export MARQO_TRITON_URL=http://localhost:8001
export MARQO_MODEL_MANAGEMENT_CONTAINER_URL=http://localhost:8883
uvicorn inference_orchestrator.main:app --host 0.0.0.0 --port 8884
```

Configuration names observed in docs and compose include `MARQO_TRITON_URL`, `TRITON_SERVER_URL`, `MARQO_MODEL_MANAGEMENT_CONTAINER_URL`, `CACHE_SIZE`, `CACHE_STRATEGY`, `LOG_LEVEL`, and `OTEL_ENABLED`. Prefer names already used by the code path under test.

## Model-management local plan

The model-management service runs on port `8883` and loads/unloads models into Triton. It needs a Triton REST URL and a model cache path.

```bash
cd components/model_management
uv sync --group dev
. .venv/bin/activate
export PYTHONPATH=./src
export MARQO_TRITON_REST_URL=http://localhost:8000
export MARQO_MODEL_CACHE_PATH=.cache/models
uvicorn model_management.main:app --host 0.0.0.0 --port 8883
```

## Java/Maven custom searcher build

The Marqo Dockerfile builds the Java Vespa custom searcher in a Maven stage. Local custom-searcher work must use Maven and JDK 17.

```bash
cd components/marqo/vespa
java -version
mvn -version
mvn clean package
```

Facts to preserve:

- Maven artifact: `ai.marqo:marqo-custom-searchers:1.0.0`.
- Packaging: `container-plugin`.
- Java source/target: `17`.
- Output jar name used by the Dockerfile: `marqo-custom-searchers-deploy.jar` under the Maven `target/` directory.
- The parent Vespa dependency is pinned to a Vespa Cloud tenant base version for compatibility, even though local `.env` may use a newer Vespa runtime.

If `HybridSearcher.java` changed, Maven build alone is not enough for runtime validation: redeploy the Vespa application package, then rerun the relevant integration/API scenario.

## Docker image build context

Build component images from the `components/` directory, not from individual component directories, because each Dockerfile expects `common/` in the build context.

```bash
cd components
DOCKER_BUILDKIT=1 docker build -f marqo/Dockerfile -t marqo-api-local .
DOCKER_BUILDKIT=1 docker build -f inference_orchestrator/Dockerfile -t marqo-mioc-local .
DOCKER_BUILDKIT=1 docker build -f model_management/Dockerfile -t marqo-mmc-local .
```

The Marqo API image runs `run_marqo.sh`, which starts uvicorn for `api:app` on port `8882`, sets default host `0.0.0.0`, default log level `info`, and default API workers `1`.
