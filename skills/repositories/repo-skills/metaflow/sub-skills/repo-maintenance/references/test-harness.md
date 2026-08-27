# Test Harness and Focused Commands

## Scope

This reference is for agents already operating inside a Metaflow repository checkout after the external-contributor gate is satisfied. The commands are repository-maintenance commands and are not required for using the public `metaflow` package.

## Unit tests

Most changes should start with the closest focused pytest file. From the repository root, run the affected unit test file with `python -m pytest -v <test-file>`. New tests should be pytest functions with plain asserts, fixtures for shared setup, `pytest.mark.parametrize` for case tables, and `pytest-mock`/`mocker` instead of raw `unittest.mock` patching.

## Core integration harness

The core harness generates synthetic flows from contexts, graphs, tests, and checkers. From the repository root, run the core harness with a local context first, for example a debug run using the `dev-local` context and, when possible, a single graph/test pair such as `linear` plus `BasicArtifactTest`.

Use the local context before service contexts because it avoids S3, metadata-service, and cloud dependencies.

## Data and UX tests

Data/S3 tests require a configured S3 or MinIO root and should be treated as service tests. UX tests cover CLI/deployment compilation behavior and may need provider-specific dependencies. Do not present service-test skips as passes.
