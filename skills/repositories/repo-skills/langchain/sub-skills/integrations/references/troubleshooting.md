# Integrations Troubleshooting

## Missing Provider SDK or Optional Dependency

Symptoms:

- `ModuleNotFoundError` or `ImportError` for a provider SDK such as `openai`, `anthropic`, `ollama`, `qdrant_client`, `chromadb`, `groq`, `huggingface_hub`, `tokenizers`, `nomic`, `perplexityai`, `openrouter`, or `exa_py`.
- Import checks fail for a partner source file.
- A unit test passes locally only because a global environment has extra packages installed.

Actions:

1. Confirm the current working directory is `libs/partners/<provider>`.
2. Inspect `pyproject.toml` for the runtime dependency and dependency groups.
3. Use `uv sync --group test` or the package-specific group needed for the target check when `uv` is available.
4. Do not install dependencies with `pip`, `poetry`, or `conda` directly in this monorepo.
5. If adding a dependency, keep it provider-scoped and update the lock with `uv` when available.
6. If `uv` is unavailable, record the skip and rely on static source review plus safe script syntax checks.

## API Key or Environment Variable Failures

Symptoms:

- Provider client initialization raises a missing credential error.
- Tests fail only in integration paths.
- Secret fields appear in string representations, serialized values, or traces.

Actions:

1. Check package-specific secret tests and client initialization code before changing environment-variable names.
2. Add or update no-network tests for explicit credentials and environment fallback.
3. Verify secret values use secure field handling and do not appear in repr or serialized output.
4. Skip live tests unless the user confirms credentials are configured outside chat.
5. For Azure-style providers, verify endpoint, deployment, API version, organization, token provider, and API-key paths independently.

## Recorded Cassette or Test Isolation Issues

Symptoms:

- VCR playback fails with missing cassette, stale request match, or attempted live network call.
- Cassette recording creates unexpected files.
- Secret scans find bearer tokens, JWTs, OAuth grant bodies, API keys, cookies, or account identifiers.
- Default unit tests unexpectedly require sockets or external services.

Actions:

1. Use playback mode first: `uv run --group test pytest --record-mode=none -m vcr tests/integration_tests/...`.
2. Do not record cassettes without explicit user permission and a safe credential source.
3. Narrow recording to one VCR-marked test or file.
4. Confirm cassette scrubbers cover request and response headers, URIs, body fields, urlencoded form bodies, JWT-like strings, cookies, and account IDs.
5. Inspect compressed cassette diffs before accepting them.
6. Keep unit tests socket-blocked when the package Makefile supports it.

## Model Profile Drift

Symptoms:

- `_profiles.py` changes after refresh without source-code edits.
- Tests fail because a model's context window, tool-call support, structured-output support, modalities, or alias changed.
- A provider model appears in source/tests but not in profile data, or vice versa.

Actions:

1. Refresh through `langchain-profiles` rather than hand-editing generated `_profiles.py`.
2. Compare generated data with `profile_augmentations.toml` and previous profile values.
3. Identify whether the change came from upstream models.dev data or a local augmentation.
4. Update tests to assert behavior that LangChain relies on, not every upstream data field.
5. Explain capability changes model-by-model in the handoff.
6. If `uv` is unavailable, do not claim refresh was run; describe the intended command and skip reason.

## Vector Store Service Availability

Symptoms:

- Qdrant or Chroma integration tests fail because no service, collection, or persistence directory is available.
- Tests hang or fail on connection refused.
- Collection cleanup deletes or mutates user data.
- Embedding dimension or distance-strategy errors appear only at query time.

Actions:

1. Prefer unit tests with fake embeddings, in-memory clients, temporary directories, or mocked service clients.
2. Ask before starting services, pulling images, pulling local models, or connecting to hosted databases.
3. Use isolated collection names and temporary persistence paths for integration tests.
4. Do not delete user collections or persistent data as cleanup.
5. Test embedding dimension, metadata filters, MMR, add/delete/update, sync/async, and collection reuse when the change touches those surfaces.
6. Skip service-backed tests with a clear reason when services are unavailable.

## Provider Response or Tool-Call Shape Mismatches

Symptoms:

- Tool calls are missing ids, names, arguments, or invalid-call metadata.
- Streaming chunks differ from non-streaming responses.
- Usage metadata or response metadata is absent or provider-specific fields are misplaced.
- Provider SDK upgrades change response object attributes or JSON shape.
- Structured output or JSON mode works for one provider path but fails for another.

Actions:

1. Capture the provider-native shape in a unit test fixture or mocked SDK response.
2. Test both invoke and stream paths when the integration supports both.
3. Verify conversion into LangChain message fields: `content`, `tool_calls`, `invalid_tool_calls`, `response_metadata`, `usage_metadata`, and finish reason.
4. Keep provider-specific conversion helpers in the partner package.
5. Do not broaden exception swallowing. Raise or surface precise provider errors where existing patterns do so.
6. Coordinate shared schema or core behavior changes with the core-primitives owner.

## Validation Command Fails Because Command Does Not Exist

Symptoms:

- `make integration_tests` or `make type` is missing or behaves differently for one package.
- Test filenames differ from the expected `test_chat_models.py` or `test_embeddings.py`.
- `uv` is unavailable in the host environment.

Actions:

1. Inspect the package Makefile and tests tree before running a command.
2. Run only existing files and targets.
3. Use the narrowest file or node for the changed area.
4. Record skipped commands honestly.
5. Do not infer success from commands that were not run.
