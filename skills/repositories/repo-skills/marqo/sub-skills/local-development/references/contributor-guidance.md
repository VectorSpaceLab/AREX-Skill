# Contributor guidance

Use this reference for repository-maintenance constraints. It intentionally does not cover detailed API payloads, search ranking, index internals, or model internals.

## Code style and imports

- Keep imports at the top of the file whenever possible.
- Avoid inline imports unless they are necessary for circular-dependency avoidance or another explicit reason.
- When calling functions, prefer explicit argument names where practical: `func(a=1, b=2)` is easier to refactor than positional calls.
- Follow the existing package structure for new modules.
- Component tests should mirror the source package hierarchy.

## Semi-structured index maintenance rule

`structured_vespa_index` is being deprecated. Make changes directly in `semi_structured_vespa_index` even when the current implementation appears to inherit from or share behavior with structured index code.

Practical implications:

- Do not fix only the structured index path when the intended runtime path is semi-structured.
- Add or update tests under the semi-structured package test hierarchy when semi-structured behavior changes.
- If a compatibility shim still touches structured code, document why but keep the primary behavior and validation in the semi-structured path.

## Exceptions and API layering

- Core classes must raise `marqo.core.exceptions` or `marqo.exceptions`, not `marqo.api.exceptions`.
- API-layer mapping is responsible for converting core/service errors into API responses.
- Non-user-facing internal errors should use internal error classes or appropriate subclasses.
- Errors from inference/API-backed model calls should preserve the service-specific error boundary rather than leaking unrelated exception types.

## Test-writing rules

- If existing tests cover the target area, prefer updating them over creating a new test file.
- Unit tests must follow the same package hierarchy as the source package.
- Use subtests for groups of related cases with shared setup.
- For `unittest` assertions, put expected values before actual values.
- Prefer specific assertions over broad `assertTrue`, `assertFalse`, `assertIsNone`, or `assertIsNotNone` when the expected shape can be checked directly.
- Avoid sleeps in unit tests; mock delays/timeouts instead.
- Set environment variables explicitly inside tests that depend on them, because root `.env` or shell state can affect behavior.
- Avoid testing private methods unless the behavior cannot be reached through a public method.
- Run changed/new tests and verify they pass before reporting completion.

## Service/test safety

- Unit tests are usually safe to run locally.
- Integration and API tests can start services, rely on Vespa/Triton/model downloads, and create/delete indexes. Treat them as service-mutating and potentially destructive.
- Never point API tests at a production or shared Marqo instance.
- Prefer CPU/random-model coverage for local verification unless the task requires CUDA or real model downloads.
- When service tests are required, record which local ports, containers, and environment variables are in use.

## Release and branch expectations

- Main branch is `mainline`; feature branches usually follow a contributor/feature-name pattern.
- Releases follow semantic-versioning principles, with special care because 0.x releases may include breaking changes on minor-version bumps.
- Release work should update release notes and related client packages when API behavior changes.

## Docker/build constraints

- Build Docker images from the `components/` directory so each component can copy and install the shared `common/` package.
- The Marqo API Docker build includes a Maven stage for the Vespa custom searcher jar.
- If `HybridSearcher.java` changes, run Maven packaging and redeploy the Vespa application package before validating runtime behavior.
