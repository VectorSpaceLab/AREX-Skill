# Repo Development Troubleshooting

Use this reference when source-checkout contribution, validation, provider, docs, or PR-policy work gets blocked.

## Installed package versus source checkout confusion

Symptom: the user asks to run `make test`, `make pre-commit`, docs Fern checks, or repository scripts from an installed package environment.

Response:

- Explain that these commands require a live source checkout with development dependencies installed.
- For package usage checks with no source edit, route to `setup-and-basics`, `configure-rails`, `run-rails`, or `evaluate-and-observe` as appropriate.
- For source work, start from the checkout and run:

```bash
make install
```

Then choose focused validation from [test-and-validation](test-and-validation.md).

## Accidental live-provider calls in tests

Symptom: a test attempts to call OpenAI, NVIDIA, NIM, GCP, telemetry staging, Hugging Face/FastEmbed downloads, or another external service.

Response:

- Prefer `make test` or `make test WORKERS=1`; these unset live-provider keys before pytest starts.
- Avoid bare `uv run --locked pytest` and `make test-serial` unless there is a specific reason and the environment is controlled.
- Replace live LLM calls with `FakeLLMModel` or `TestChat`.
- Replace provider HTTP with `pytest-httpx` (`httpx_mock`) or another repository-approved fake.
- Set secrets with `monkeypatch`, not the developer's real shell environment.
- Keep real-network tests explicitly skipped unless the task is explicitly live-provider verification.
- If default embeddings try to download a model, use the repository's deterministic embedding test pattern or mark a real-embedding test only when explicitly intended.

## Focused tests fail only under xdist

Symptom: `make test` fails in parallel but the failure is hard to reproduce.

Response:

```bash
make test TEST=<same-selector> WORKERS=1 ARGS="-q --tb=short"
```

Then inspect for shared global state, framework registry state, context variables, temporary files, HTTP mocks, asynchronous task cleanup, or tests relying on order. `serial` and `slow` markers are advisory; they do not automatically disable xdist in the default target.

## Pre-commit failures

Symptom: Ruff, Ruff format, license-header insertion, ty, or another hook fails.

Response:

- Treat `make pre-commit` as the authoritative PR-ready path.
- Use diagnosis commands for a narrower loop:

```bash
uv run --locked ruff check path/to/file.py
uv run --locked ruff format path/to/file.py
uv run --locked ty check
uv run --locked pre-commit run --files <changed files>
```

- Do not add license headers manually unless the project tooling explicitly instructs it; pre-commit handles license insertion.
- Avoid broad formatting churn unrelated to the assigned change.
- If ty fails outside the touched area, report the scope and avoid hiding a real regression.

## Optional dependency or lockfile problems

Symptom: a new provider or integration breaks base imports, a dependency appears in the wrong group, or `uv.lock` is stale.

Response:

- Keep optional integrations optional and lazily imported.
- Put third-party provider dependencies in the narrowest extra or dependency group; do not move them into default runtime dependencies without explicit packaging direction.
- Read current dependency metadata and lockfile before editing.
- Regenerate the lock with repository tooling after dependency changes.
- If lock regeneration cannot be run or fails, stop and report that the dependency state is inconsistent rather than pretending the patch is ready.

## Provider HTTP or secret-handling regressions

Symptom: provider tests expose credentials, compare headers incorrectly, lose upstream error causes, or produce unstable network behavior.

Response:

- Treat HTTP header names as case-insensitive; compare values case-insensitively only when the relevant spec says so.
- Do not include API keys, bearer tokens, private endpoints, provider names tied to secrets, or sensitive request/response data in logs or response bodies.
- Wrap LLM provider failures in domain LLM exceptions with the original cause preserved.
- Use `pytest-httpx` or test doubles for all unit tests.
- Add focused tests for rate limit, retry, unsupported mode, missing optional dependency, redaction, and streaming metadata if those paths changed.

## Public API or sync/async mismatch

Symptom: a change affects `Guardrails`, `LLMRails`, `RailsConfig`, server schemas, Colang behavior, or exported names.

Response:

- Treat it as compatibility-sensitive.
- Preserve signatures and exports unless the task explicitly requests a public API change.
- Keep sync and async methods behaviorally aligned.
- Test both public surfaces when a shared behavior changes.
- If a compatibility break is necessary, draft a proposal or issue comment unless a linked triaged assigned issue already records maintainer agreement.

## Docs build or generated docs failures

Symptom: Fern validation fails, generated SDK references changed unexpectedly, or docs links/navigation break.

Response:

- Read the full target page before editing again.
- Fix source MDX or navigation rather than hand-editing generated SDK output.
- Use Node.js 22 and repository `make docs-fern*` targets.
- Run `make docs-fern` for ordinary docs checks; use strict or live variants only when appropriate.
- Do not run notebook conversion unless explicitly asked; if asked, use a clean worktree and expect broad staging/pre-commit side effects.
- Keep generated-file diffs separate in the handoff so maintainers can review them deliberately.

## Maintainer script uncertainty

Symptom: the task seems related to schema snapshots, telemetry staging, OpenAI API conformance, Kibana, docs conversion, Fern preview, or notebook generation.

Response:

- Check [docs-and-generated-files](docs-and-generated-files.md) before running any script.
- If the user did not explicitly request the maintenance workflow, do not run the script. Draft prerequisites, command, expected mutation, and risk instead.
- Never run staging, credentialed, network, or broad generated-file scripts as routine validation for a source change.

## PR blocked by policy

Symptom: the user asks to open a PR, push a branch, or mark a PR ready, but there is no triaged issue assigned to the authenticated user.

Response:

- Run only read-only checks if PR-shaped work is being considered.
- If the issue is missing, untriaged, or not assigned to the authenticated login, stop at draft issue text, draft issue comment, or draft PR text.
- Do not claim that labels, assignment, CI, CodeRabbit, Greptile, or maintainer approval exist unless verified.
- If an open PR already covers the same issue or area, do not prepare a duplicate; surface the difference in a draft issue comment.

## Review readiness blocked by comments

Symptom: automated or human review comments remain unresolved.

Response:

- Address each comment or reply with a concrete reason no change is needed.
- Wait for automated-review resolution confirmation when the tool provides it.
- Do not resolve human reviewer conversations unless you opened the thread or the reviewer explicitly asks.
- Do not self-apply ready-for-maintainer-review labels.
- Re-run validation after changes that affect code behavior, generated docs, or line locations.

## Telemetry, tracing, logging, and metrics confusion

Symptom: a change or docs text treats anonymous usage telemetry, tracing, metrics, and logs as one switch.

Response:

- Keep the contracts separate.
- Telemetry opt-out and audit behavior is not the same as user-configured tracing/exporters.
- Tracing and metrics should remain independently configurable.
- Use deterministic tests for local behavior. Telemetry staging smoke is a maintainer workflow requiring explicit authorization and network prerequisites.
