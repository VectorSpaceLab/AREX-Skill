# Test And Validation

These commands are for a live NVIDIA NeMo Guardrails source checkout after development dependencies are installed. Do not imply that an installed package alone can run repository tests, pre-commit hooks, or Fern docs checks.

## Setup for source development

NeMo Guardrails supports Python `>=3.10,<3.14`. Use `uv` and the checkout's locked dependency metadata.

```bash
make install
```

Use temporary local investigation packages through the uv-managed environment without changing project dependencies:

```bash
uv pip install <package-name>
```

Do not edit `pyproject.toml` or `uv.lock` unless the task requires a dependency change. When a dependency change is required, keep it in the narrowest appropriate dependency group or optional extra, read both files before editing, and regenerate the lock with project tooling.

## Canonical commands

Run Python tooling through `uv` or through repository `make` targets.

| Purpose | Checkout-scoped command | Notes |
| --- | --- | --- |
| Install development dependencies | `make install` | Uses locked development dependencies. |
| Focused tests | `make test TEST=path/to/test_file.py::test_name` | Add `ARGS="-q --tb=short"` or `ARGS="-k <expr> -q"` when useful. |
| Full tests | `make test` | Runs `pytest.ini` testpaths with xdist and unsets live-provider keys. Includes `tests` and `benchmark/tests`. |
| Serial deterministic diagnosis | `make test WORKERS=1` | Same live-key safety as `make test`, without xdist. |
| Coverage | `make test-coverage` | Use when coverage is requested or package-wide impact is meaningful. |
| Pre-commit | `make pre-commit` | Authoritative lint, format, license-header, and type-checking path for PR-ready changes. |
| Docs check | `make docs-fern` | Required when rendering, links, examples, docs navigation, or docs config may be affected. |
| Ruff diagnosis | `uv run --locked ruff check path/to/file.py` | Diagnosis only; still run pre-commit before handoff when practical. |
| Ruff format diagnosis | `uv run --locked ruff format path/to/file.py` | Diagnosis only; avoid isolated formatting churn. |
| ty diagnosis | `uv run --locked ty check` | Diagnosis only; use pre-commit as the final gate. |
| Docs-only pre-commit | `uv run --locked pre-commit run --files <changed files>` | Minimum for docs or metadata-only edits when full pre-commit is not practical. |

Avoid `make test-serial` and bare `uv run --locked pytest` as default validation because they do not unset live-provider keys. Prefer `make test` or `make test WORKERS=1` so unit tests cannot reach live services.

## Select tests by change type

Start with the smallest meaningful regression test and broaden when shared behavior is touched.

| Change type | Minimum validation |
| --- | --- |
| Docs or repository metadata only | `uv run --locked pre-commit run --files <changed files>`; also run `make docs-fern` when rendering, links, examples, navigation, or docs configuration may be affected. |
| Runtime bug fix | A focused regression test plus pre-commit on changed files; broaden when shared behavior is touched. |
| Public API, config, or Colang behavior | Focused tests plus related docs/examples review; add broader package tests when compatibility risk is meaningful. |
| Provider integration, server, streaming, tracing, actions, or generation | Targeted tests for changed path, fallback path, and unsupported/error path; include no-live mock coverage. |
| Packaging, dependencies, or lockfiles | Relevant install/package checks plus pre-commit; keep dependency diffs separate from unrelated changes. |
| Docs source plus generated docs output | Full target page read, docs edit, generated-output handling through documented targets only, `make docs-fern` when rendering or links may change. |

## Focused native candidates for later verification

Choose from these checkout tests after a relevant code change. Do not run them merely because this skill was loaded.

```bash
make test TEST=tests/test_imports.py WORKERS=1 ARGS="-q"
make test TEST="tests/test_config_loading.py tests/test_config_validation.py" WORKERS=1 ARGS="-q"
make test TEST=tests/guardrails/test_guardrails.py WORKERS=1 ARGS="-q"
make test TEST=tests/cli/test_cli_main.py WORKERS=1 ARGS="-q"
make test TEST=tests/server/test_api.py WORKERS=1 ARGS="-q"
make test TEST="tests/eval/test_eval_cli.py tests/evaluate/test_evaluate_cli_and_data.py" WORKERS=1 ARGS="-q"
```

For LangChain, provider, streaming, telemetry, or recorded-cassette changes, select the narrowest concrete test file or test node that covers the modified path, then broaden only if shared behavior is affected.

## No-live-provider unit-test policy

- Unit tests must not call live LLM or provider services.
- `make test` and `make test WORKERS=1` unset live-provider variables such as OpenAI/NVIDIA live-test signals before pytest starts.
- `pytest.ini` marks live, recorded, serial, slow, perf, vcr, fake-cassette, and real-embedding cases. The default addopts exclude perf tests.
- The default suite swaps the default FastEmbed provider to a deterministic provider unless a test is marked `real_embeddings` or live-test environment signals are set.
- Keep real-network tests behind explicit skips; there is no global live-test mode that makes unit tests safe to hit providers by default.

## Preferred test doubles

Use the project's public testing utilities and fixtures rather than ad hoc live calls:

- `nemoguardrails.testing.FakeLLMModel` for deterministic completions, token usage, and streaming chunks.
- `nemoguardrails.testing.TestChat` for end-to-end rail conversations with `>>`/`<<` style assertions.
- `nemoguardrails.testing.RecordingHTTPClient` when the public helper is a good fit for deterministic HTTP behavior.
- `pytest-httpx` (`httpx_mock`) for provider HTTP calls and external guardrail/scanning APIs.
- `monkeypatch` for secrets and environment variables.

When adding config-driven behavior, test against a real `RailsConfig` loaded with `RailsConfig.from_content` or `RailsConfig.from_path`, not a `SimpleNamespace` or arbitrary attribute stub.

## Recorded and credentialed workflows

Recorded-cassette targets are maintainer workflows, not default validation:

```bash
make replay-cassettes
make record-cassettes
make rewrite-cassettes
make snapshot-cassettes
```

`record-cassettes` and `rewrite-cassettes` require explicit provider keys and can refresh snapshots; do not run them unless the task explicitly requires cassette maintenance and the operator authorizes the credentials and network use. For ordinary source changes, prefer deterministic fakes and `pytest-httpx`.

## Validation reporting

At handoff, report:

- Exact commands run and whether they passed, failed, or were skipped.
- Any live, credentialed, or hardware-specific path intentionally not exercised.
- Whether `make test` was broadened beyond focused tests and why.
- Whether `make pre-commit` or a file-scoped pre-commit command was run.
- Whether docs validation was required and run.
- Residual risk for unrun checks.
