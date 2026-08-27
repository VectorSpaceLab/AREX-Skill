# Cross-cutting Troubleshooting

Read this first when Marqo import, service, backend, or test setup fails and the owning sub-skill is not yet obvious.

## Import or package installation fails

Symptoms:

- `ModuleNotFoundError` for `marqo`, `marqo_common`, `inference_orchestrator`, or `model_management`.
- `Requires-Python` or resolver errors around Python versions.
- FastAPI, Pydantic, torch, Triton, or Vespa client imports fail.

Recovery:

1. Use Python 3.11 for these components.
2. Install only the component needed for the current task. The full inference orchestrator pulls torch/OpenCLIP/Triton dependencies; avoid it when only API request shaping is needed.
3. Run the safe environment probe:

   ```bash
   python scripts/check_marqo_environment.py --json
   ```

4. If only main API payload work is needed, route to `sub-skills/documents-and-api/` or `sub-skills/search-and-ranking/` before installing inference/model-management dependencies.
5. If the import failure is torch/OpenCLIP/transformers/tritonclient-specific, route to `sub-skills/inference-and-models/`.

## Service is unreachable

Symptoms:

- HTTP connection refused to `localhost:8882`, `8883`, or `8884`.
- Vespa endpoint failures on ports `8080` or `19071`.
- Health endpoints do not return success.

Recovery:

1. Identify the service: Marqo API (`8882`), model-management (`8883`), inference orchestrator (`8884`), Vespa (`8080`/`19071`), Triton (`8000`/`8001`), Redis, or Zookeeper.
2. Use `sub-skills/local-development/scripts/print_service_commands.py` to print a service plan before running anything mutating.
3. Use `sub-skills/documents-and-api/scripts/marqo_http_smoke.py --print-only` to preview API requests without network calls.
4. Do not delete indexes, stop containers, deploy Vespa apps, or load/unload models unless the user explicitly requests a live operation.

## Vespa schema, index deployment, or searcher build fails

Symptoms:

- Index create/delete hangs or returns lock/convergence errors.
- Vespa app deployment fails.
- Custom Java searcher changes do not affect hybrid search.
- Maven/JDK missing or `mvn clean package` fails.

Recovery:

1. Open `sub-skills/index-and-vespa/` for schema/index reasoning.
2. Run the read-only inspector before attempting deployment:

   ```bash
   python sub-skills/index-and-vespa/scripts/inspect_vespa_local.py --repo-root <checkout> --json
   ```

3. If `HybridSearcher.java` changed, build the Vespa package with Maven and redeploy the application package before retesting.
4. If lock/convergence problems involve Zookeeper or Vespa endpoints, fix service configuration and restart Marqo; do not treat a Python import check as proof that Vespa deployment works.

## Search request is valid JSON but invalid Marqo

Symptoms:

- `q` shape is rejected for the selected `searchMethod`.
- Filters parse unexpectedly or field restrictions fail.
- Hybrid requests ignore intended searchable attributes or ranking knobs.
- Score modifiers, collapse, sort, recency, or relevance cutoff conflict.

Recovery:

1. Open `sub-skills/search-and-ranking/references/troubleshooting.md`.
2. Generate minimal offline payload examples:

   ```bash
   python sub-skills/search-and-ranking/scripts/search_payload_examples.py --case hybrid
   ```

3. Add ranking features one at a time. Distinguish route mechanics from ranking semantics: HTTP route errors belong in `documents-and-api`; ranking parameter repair belongs in `search-and-ranking`.

## Model or inference backend fails

Symptoms:

- Unsupported model name or missing `modelProperties`.
- HF/OpenCLIP download or auth errors.
- CUDA unavailable or out of memory.
- Triton gRPC/HTTP unreachable.
- Model load/unload cache-key mismatch.

Recovery:

1. Prefer `random/small`, `random/medium`, or `random/large` for no-download shape checks.
2. Run the backend probe without contacting Triton:

   ```bash
   python sub-skills/inference-and-models/scripts/check_model_backends.py --json
   ```

3. If probing a live Triton endpoint is required, pass an explicit URL and confirm the user wants a live network/service check.
4. For direct `/vectorise`, send full `embeddingModelConfig.modelProperties`; do not assume the direct inference service resolves registry names like the Marqo API layer.

## Tests fail or hang

Symptoms:

- `pytest` cannot import packages.
- Integration/API tests hang waiting for Vespa or API service.
- GPU/model tests download large artifacts unexpectedly.

Recovery:

1. Open `sub-skills/local-development/references/testing.md`.
2. Use the test selector to print a plan:

   ```bash
   python sub-skills/local-development/scripts/select_tests.py <changed-path> --json
   ```

3. Start with unit tests. Mark Vespa/API/Triton/model-download tests as service-backed or optional unless the user explicitly asks to run them.
4. Use `PYTHONPATH=./src` from the relevant component root for unit/integration tests.
5. For API tests, run the Marqo API in a separate process and terminate it after tests complete.

## When to stop and ask

Stop before:

- Installing or mutating a user-owned Python environment.
- Starting/stopping containers or deleting indexes/documents.
- Deploying Vespa applications or building/replacing Java searchers.
- Downloading large models/datasets or using credentials.
- Accepting a CUDA/Triton/service limitation as verified when the selected task truly requires that backend.
