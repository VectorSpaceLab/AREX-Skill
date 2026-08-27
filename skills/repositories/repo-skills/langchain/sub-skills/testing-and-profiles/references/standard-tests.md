# Standard Tests

LangChain publishes `langchain-tests` as the shared conformance-test package for implementations. In this monorepo it lives in the standard-tests package and exposes reusable base classes under `langchain_tests.unit_tests` and `langchain_tests.integration_tests`.

## When To Use Standard Tests

Use standard tests when an integration package implements a LangChain interface such as chat models, embeddings, tools, retrievers, vector stores, stores, caches, indexers, or sandboxes. They are especially useful for provider packages because the same base tests assert consistent behavior across implementations.

Do not use this reference to design provider-specific runtime behavior. For implementation details, route to the integration-owning sub-skill and package code.

## Unit Vs Integration Classes

- Unit standard tests inherit from `langchain_tests.unit_tests.*` and should be deterministic, local, and safe for default CI. They check constructor behavior, interface shape, environment-variable initialization, tool-call metadata, and other behavior that can be tested without real provider calls.
- Integration standard tests inherit from `langchain_tests.integration_tests.*` and exercise real behavior such as embedding text, invoking chat models, touching stores, or running provider services. Treat these as credentialed or service-backed unless the concrete implementation is known to be local and deterministic.
- Both families commonly require a subclass to provide a class fixture/property such as `chat_model_class`, `embeddings_class`, or equivalent interface-specific fixtures, plus optional parameter fixtures such as `chat_model_params` or `embedding_model_params`.

## Embeddings Example Pattern

A new embeddings integration usually needs both files:

```python
from langchain_tests.unit_tests import EmbeddingsUnitTests

from my_package.embeddings import MyEmbeddings


class TestMyEmbeddingsUnit(EmbeddingsUnitTests):
    @property
    def embeddings_class(self) -> type[MyEmbeddings]:
        return MyEmbeddings

    @property
    def embedding_model_params(self) -> dict[str, object]:
        return {"model": "test-model"}
```

Integration tests use `EmbeddingsIntegrationTests` and should only run when the package has credentials, service access, cassettes, or a local fake implementation that makes them deterministic. The integration base checks that `.embed_query`, `.embed_documents`, `.aembed_query`, and `.aembed_documents` return non-empty same-width lists of floats.

## Safe Local Checks For New Standard Tests

From the owning integration package directory:

```bash
uv sync --group test
uv run --group test pytest tests/unit_tests/test_standard.py
```

If the package's test group already includes `langchain-tests`, this is the normal no-network starting point. If it does not, inspect the package metadata and add the dependency only as part of the implementation task, following package-local patterns.

For integration standard tests, require explicit user approval or a known-safe fake/local backend before running:

```bash
uv sync --group test --group test_integration
uv run --group test --group test_integration pytest tests/integration_tests/test_standard.py
```

## Markers And Plugins

LangChain packages commonly configure pytest with:

- `--strict-markers` and `--strict-config`, so unknown markers or invalid config fail collection.
- `--durations=5` and often `-vv` for timing and verbose output.
- `asyncio_mode = "auto"` for async tests.
- `requires` marker for optional packages; package conftests often skip tests when a required import is unavailable.
- `compile` marker for placeholder integration tests that verify import/collection without executing service-backed behavior.
- `scheduled` marker for tests intended for scheduled or broader CI rather than local default checks.

`langchain-tests` also declares a pytest plugin entry point for the LangSmith CI plugin. If plugin behavior changes collection or reporting, keep the check local to the package and avoid guessing cross-package implications.

## Snapshot And Recording Awareness

Some packages use `syrupy` snapshots and `pytest-recording`/VCR cassettes. Treat these as validation aids, not as permission to regenerate artifacts automatically.

- Run snapshot tests normally to detect behavior drift.
- Do not run snapshot update flags unless the user confirms the serialized output change is expected.
- Do not re-record cassettes without credentials, network approval, and explicit maintainer intent.

## Validation Signals

A safe standard-test change should show:

- Unit standard tests collect without unknown markers or strict-config errors.
- Required optional dependency skips are explicit and expected.
- Unit subclasses provide all required properties/fixtures for their base class.
- Integration subclasses are present only when there is a safe backend, cassette strategy, or documented credential requirement.
- Failures point to interface behavior, not missing environment setup.
