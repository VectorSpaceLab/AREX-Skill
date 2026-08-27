# Troubleshooting

## `nx`, `npm`, or `uv` is missing

- Install the workspace Node dependencies first so Nx is available.
- Use `npx nx ...` from the repo root for workspace targets.
- Use `uv run ...` for Python commands inside a package.
- If package targets fail immediately with a missing `uv`, the package environment has not been synced yet.

## A package cannot resolve local sources

Symptoms:
- `uv sync` resolves a published package instead of a sibling checkout package.
- A local package import fails after adding a new instrumentation package.

Likely fix:
- Check `tool.uv.sources` in the package `pyproject.toml`.
- Keep each path relative to the package directory.
- Use `editable = true` for checkout-local development.
- Make sure the sibling package name matches the dependency key.

## A new instrumentation package is missing semconv, an entry point, or a local source path

Use this order:

1. Confirm the package has the right `project.name` and `project.json.name`.
2. Add the semantic-convention dependency if the package imports semconv symbols.
3. Add the `opentelemetry_instrumentor` entry-point mapping if discovery cannot find the instrumentor.
4. Add or fix the relative `tool.uv.sources` path when the package should link to another checkout-local package.
5. Re-run the narrowest install or import check before broad tests.

Typical signals:
- `ModuleNotFoundError` for `opentelemetry.semconv_ai` usually means the semconv dependency is missing or the local source mapping is stale.
- `No entry points found` usually means the entry-point table is missing or misnamed.
- `uv sync` choosing the wrong version usually means the local source path is absent or not editable.

## VCR cassette errors

- `--record-mode=none` fails if the cassette is missing; that is expected.
- If the cassette exists but the test still fails, inspect whether the recorded traffic changed.
- Use `once`, `new_episodes`, or `all` only when the change genuinely affects the recorded traffic and you have the required credentials.
- Scrub secrets before recording.

## Credentials or live-service failures

- Cloud provider tests, hosted vector DB tests, and API-backed examples require the correct service credentials or local services.
- Do not treat a missing credential as a package bug until the safe replay or offline candidates have been tried.
- If a live test is not essential, switch to the safe candidate categories in the testing reference.

## Release and codegen hazards

### Release build

- `scripts/build-release.sh` mutates the current package `pyproject.toml` by stripping `tool.uv.sources`.
- That is expected for release packaging, but it is not a safe routine maintenance command.
- If you need checkout-local development against sibling packages, use the normal build/test/install targets instead.

### Evaluator model generation

- `scripts/generate-models.sh` expects a Swagger file and writes generated evaluator models.
- `scripts/codegen/generate_evaluator_models.py` depends on `datamodel-code-generator` and rewrites generated files.
- If code generation fails, verify the Swagger input and the codegen toolchain before touching the generated output.

## When the change is really about runtime behavior

If the issue is actually about SDK initialization, tracing semantics, or instrumentor behavior rather than repo maintenance, route to the sibling sub-skill instead of debugging the workspace layer here.
