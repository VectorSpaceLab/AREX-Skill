# Testing workflows

This reference focuses on selecting and running Marqo repository tests. Commands are relative to the repository checkout. API and integration tests can create, mutate, and delete indexes; do not point them at production or shared Marqo instances.

## General rules

- Activate the intended environment first; use Python 3.11 for service components.
- Load `.env` when a command depends on compose/service variables.
- For component unit and integration tests, run from the component root and set `PYTHONPATH=./src`.
- Use existing tests when possible. If a code change needs new coverage, prefer extending the existing package-parallel test file.
- Use subtests for related cases with shared setup.
- Run changed or newly added tests before reporting completion.
- Do not run service-backed tests unless Vespa/API/Triton prerequisites are prepared and the task explicitly allows service mutation.

## Marqo API component tests

Component root: `components/marqo`.

Unit tests:

```bash
cd components/marqo
PYTHONPATH=./src pytest tests/unit_tests -q
```

Integration tests:

```bash
cd components/marqo
# Requires Vespa and usually Zookeeper/Marqo config to be reachable.
PYTHONPATH=./src pytest tests/integ_tests -q
```

API tests:

```bash
# Terminal 1: start Vespa, then Marqo API from components/marqo.
cd components/marqo
export PYTHONPATH=./src
export MARQO_ENABLE_BATCH_APIS=true
export MARQO_MODE=COMBINED
export VESPA_CONFIG_URL=http://localhost:19071
export VESPA_DOCUMENT_URL=http://localhost:8080
export VESPA_QUERY_URL=http://localhost:8080
python src/marqo/tensor_search/api.py

# Terminal 2: run API tests from the Marqo component root.
cd components/marqo
PYTHONPATH=./tests/api_tests/v1/tests/api_tests pytest tests/api_tests/v1/tests/api_tests -q
```

Terminate the API process after API tests finish. If the API fails to start, stop and troubleshoot rather than continuing to run API tests.

API-test launch scripts in the repository build or start Docker containers. Treat them as reference-only unless explicitly authorized.

## Inference orchestrator tests

Component root: `components/inference_orchestrator`.

```bash
cd components/inference_orchestrator
PYTHONPATH=./src pytest tests/unit_tests -q
PYTHONPATH=./src pytest tests/integration_tests -q
```

Safe CPU candidates include text-splitting and random-model pipeline tests. HF/OpenCLIP/Triton-backed tests can require downloads, cache state, Docker, or CUDA; skip them unless the task explicitly includes those prerequisites.

## Model-management tests

Component root: `components/model_management`.

```bash
cd components/model_management
PYTHONPATH=./src pytest tests/unit_tests -q
PYTHONPATH=./src pytest tests/integration_tests -q
```

Unit tests for model-property schemas and URL parsing are safe CPU candidates. Integration tests require a prepared service/Triton environment.

## Minimal test selection by change area

Use the bundled selector first:

```bash
python scripts/select_tests.py CHANGED_FILE...
```

Manual map:

| Change area | Minimal safe unit plan | Optional service plan |
|---|---|---|
| `components/marqo/src/marqo/core/semi_structured_vespa_index/` | `test_semi_structured_vespa_index.py`, add-document/schema/filter/query unit tests, and `test_marqo_index.py` | Vespa-backed semi-structured integration tests and relevant API create/add/search tests |
| Vespa Java custom searchers | Maven `mvn clean package`; Java unit tests via Maven | Redeploy Vespa app package and rerun relevant integration/API scenario |
| `components/marqo/src/marqo/tensor_search/api.py` or API validation | `test_api.py`, `test_validation.py`, `test_api_typeahead.py` as applicable | API tests for health, create index, documents, typeahead, or changed route |
| Search/filter/ranking Python code | `test_hybrid_search.py`, `test_search_filter.py`, related tensor-search model tests | API hybrid/search tests if Marqo API and Vespa are running |
| Inference orchestrator preprocessing/cache/random pipeline | split-text/cache/random-model unit tests | MIOC integration tests with Triton/MMC only after services are healthy |
| Model-management schemas/services | schema and URL-parser unit tests | MMC/Triton integration tests after compose stack is healthy |
| Compose/Dockerfile/service scripts | Do not run containers by default; run `docker compose ... config` and script `--help` checks | Start compose only with explicit approval |

## Semi-structured Vespa index change: recommended minimal plan

For a Python change under `semi_structured_vespa_index`, start with CPU unit tests:

```bash
cd components/marqo
PYTHONPATH=./src pytest \
  tests/unit_tests/marqo/core/models/test_marqo_index.py \
  tests/unit_tests/marqo/core/semi_structured_vespa_index/test_semi_structured_vespa_index.py \
  tests/unit_tests/marqo/core/semi_structured_vespa_index/test_semi_structured_add_document_handler.py \
  tests/unit_tests/marqo/core/semi_structured_vespa_index/test_semi_structured_document.py \
  tests/unit_tests/marqo/core/semi_structured_vespa_index/test_semi_structured_vespa_index_to_vespa_query.py \
  tests/unit_tests/marqo/core/semi_structured_vespa_index/test_semi_structured_vespa_index_in_filter.py \
  -q
```

If behavior depends on a running Vespa app package, add only after service approval:

```bash
cd components/marqo
PYTHONPATH=./src pytest \
  tests/integ_tests/core/semi_structured_vespa_index/test_semi_structured_vespa_index.py \
  tests/integ_tests/core/semi_structured_vespa_index/test_semi_structured_vespa_schema.py \
  tests/integ_tests/tensor_search/integ_tests/test_search_semi_structured.py \
  -q
```

## API/Vespa local run plan for testing

Use this as a stop-before-mutation checklist:

1. Confirm the target Marqo instance is local and disposable.
2. Confirm Docker is running and ports `8080`, `19071`, `2181`, and `8882` are free.
3. Load `.env` and activate the Python environment.
4. Print, but do not run, local Vespa/API commands with `scripts/print_service_commands.py --plan local-api`.
5. If approved, start Vespa, wait for `19071`/`8080` health, start Marqo API on `8882`, then run only the selected API tests.
6. Terminate the API process after tests. Stop containers only after explicit confirmation that no other task uses them.

## Native candidates suitable for final verification

Safe CPU unit candidates:

```bash
cd components/marqo && PYTHONPATH=./src pytest tests/unit_tests/marqo/core/models/test_marqo_index.py -q
cd components/marqo && PYTHONPATH=./src pytest tests/unit_tests/marqo/core/semi_structured_vespa_index/test_semi_structured_vespa_index.py -q
cd components/marqo && PYTHONPATH=./src pytest tests/unit_tests/marqo/tensor_search/test_validation.py -q
cd components/inference_orchestrator && PYTHONPATH=./src pytest tests/unit_tests/services/media_download_and_preprocess/test_split_text.py -q
cd components/model_management && PYTHONPATH=./src pytest tests/unit_tests/schemas/test_triton_model_properties.py -q
```

Service-backed optional candidates:

```bash
cd components/marqo && PYTHONPATH=./src pytest tests/integ_tests/tensor_search/integ_tests/test_search_semi_structured.py -q
cd components/marqo && PYTHONPATH=./tests/api_tests/v1/tests/api_tests pytest tests/api_tests/v1/tests/api_tests/test_create_index.py -q
```
