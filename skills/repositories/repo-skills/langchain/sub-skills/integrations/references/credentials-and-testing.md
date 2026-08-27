# Credentials and Testing

## Default Safety Policy

Partner package work should be no-network by default. Unit tests should run without provider credentials, hosted services, or local model servers unless the package explicitly documents a safe exception. Treat integration tests, VCR recording, vector database services, and provider calls as opt-in checks that require user permission and the required environment.

Use these defaults:

- Prefer `tests/unit_tests/` and mocked provider clients for normal validation.
- Use `--disable-socket --allow-unix-socket` when the package Makefile uses it for unit tests.
- Run `tests/integration_tests/` only when credentials, local services, or cassettes are available and the user asked for that level of validation.
- Never print secrets, token files, request headers, cassettes, or provider payloads that may contain credentials.
- Do not create or mutate credential files as part of a routine coding task.

## Credential Sources

Credential names vary by provider and test. Do not guess a new environment variable into production code. Inspect the package tests, client initialization code, and existing secret tests before adding or changing credential behavior.

Common patterns include:

- API-key providers such as OpenAI, Anthropic, DeepSeek, Fireworks, Groq, Hugging Face endpoints, MistralAI, Nomic, Perplexity, OpenRouter, xAI, and Exa.
- Local service providers such as Ollama, Chroma, or Qdrant that may need a running local server or configured URL.
- Azure/OpenAI variants that may need endpoint, deployment, API version, organization, or token-provider fields.
- OAuth-backed experimental paths such as OpenAI Codex tests, which require a local token bundle and cassette safety review.

When adding credential support:

1. Check existing `test_secrets.py`, client utility tests, and Pydantic field aliases.
2. Verify the value is marked secret where appropriate and not exposed by `repr`, serialization, trace metadata, or test output.
3. Add tests for explicit constructor values and environment-variable fallback if both are supported.
4. Add tests for missing credentials that assert a clear error or skip behavior.
5. Do not make default unit tests require a real key.

## Unit Test Workflow

From `libs/partners/<provider>`, run only files that exist:

```bash
uv run --group test pytest tests/unit_tests/test_imports.py
uv run --group test pytest tests/unit_tests/test_secrets.py
uv run --group test pytest tests/unit_tests/test_chat_models.py
uv run --group test pytest tests/unit_tests/test_embeddings.py
uv run --group test pytest tests/unit_tests/test_vectorstores.py
```

Many package Makefiles expose:

```bash
make test TEST_FILE=tests/unit_tests/test_chat_models.py
make check_imports
make check_version
```

Use package Makefile targets when they encode package-specific flags such as socket blocking, token cache setup, retry policy, or typing tool differences.

## Integration Test Workflow

Integration tests belong under `tests/integration_tests/` and may require provider keys, live endpoints, cassettes, or services. Before running them:

1. Ask whether the user wants live or service-backed checks.
2. Confirm required credentials or services are available without asking the user to paste secrets into chat.
3. Read package `conftest.py`, integration-test fixtures, marks, and Makefile targets.
4. Prefer one file or one test node first.
5. Record skip reasons if credentials, network, service, or package dependencies are unavailable.

Typical command shape:

```bash
uv run --group test --group test_integration pytest -v --tb=short tests/integration_tests/test_chat_models.py
make integration_test TEST_FILE=tests/integration_tests/test_compile.py
```

Some packages add retries, timeouts, benchmark disables, xdist, or provider-specific environment variables in their Makefiles. Do not strip those flags casually.

## VCR and Cassette Guidance

VCR cassettes are test artifacts that allow selected integration paths to replay without live network. Treat recording as a credentialed side-effecting operation, not a default validation step.

For cassette-backed tests:

- Playback-only checks should use record mode `none` so missing cassettes fail instead of making a live call.
- Recording should be done only when the user explicitly requests it and has a safe test account or token source.
- Scrub request and response headers, URIs, OAuth fields, API keys, JWT-shaped strings, cookies, organization IDs, and account identifiers.
- Inspect cassette diffs before committing or handing off.
- Do not record broad integration suites when one targeted test is sufficient.

The OpenAI Codex cassette workflow is reference-only for this skill because it refreshes OAuth tokens, runs network-backed tests, writes cassettes, and scans for leaks. Use its distilled safety requirements instead of bundling or running the original script:

1. Preflight the local token bundle before pytest so token refresh exchanges are not captured.
2. Run only VCR-marked Codex tests with `--record-mode=once` when recording is authorized.
3. Use a placeholder API key only where the code path requires a non-empty value and the placeholder cannot match real-key leak patterns.
4. Scan compressed cassettes for bearer tokens, JWTs, OAuth fields, refresh grants, API keys, and account-id claims.
5. Fail hard on any leak and do not commit leaked cassettes.
6. Use playback mode `--record-mode=none` in CI or safe local validation.

## Local Service Checks

Ollama, Qdrant, Chroma, and some vector-store or local-model tests may need a local service. Do not start services, pull models, create Docker containers, or mutate persistent databases unless the user asks.

Before running service-backed tests:

- Confirm the service is already running or the user wants it started.
- Use temporary collections, test database names, or isolated persist directories.
- Avoid deleting user collections or persistent directories.
- Prefer compile/import tests when the service is unavailable.
- Record model names or service URLs as test assumptions, not public defaults.

## Standard Tests

Many partners include standard conformance tests such as `test_standard.py`, `test_chat_models_standard.py`, or `test_embeddings_standard.py`. These are important for provider interfaces, but changes to the standard test framework itself belong outside this sub-skill.

For partner-side work:

- Update the partner implementation and its partner-specific fixtures.
- Run the partner's standard unit tests when they are no-network.
- Run standard integration tests only when the provider/service requirements are satisfied.
- If the standard test expectation seems wrong, route the framework change to the sibling skill that owns testing and profiles.

## Skip Conditions to Report

Report a validation skip when:

- `uv` is not installed or dependencies are not synced.
- Required provider SDKs or optional extras are missing.
- API keys, OAuth token bundles, or endpoint settings are absent.
- A local service or model is not running.
- Cassette recording would mutate files or use credentials without explicit authorization.
- Integration tests would make live network calls and the user did not request them.
