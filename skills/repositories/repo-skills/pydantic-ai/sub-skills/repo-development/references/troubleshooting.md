# Repo Development Troubleshooting

Use this when a maintainer workflow fails or the right validation path is unclear.

## Full Validation Is Too Slow

Symptoms:

- `make test`, `make typecheck`, or `make` takes too long for the current edit loop.
- Test workers spend time collecting unrelated optional-provider tests.
- A small fix triggers broad unrelated failures.

Fix:

- Use targeted tests first: `uv run pytest path/to/test.py::test_name -q`.
- Use targeted typecheck: `PYRIGHT_PYTHON_IGNORE_WARNINGS=1 uv run pyright path/to/file.py`.
- Use targeted lint/format: `uv run ruff format path/to/file.py` and `uv run ruff check path/to/file.py`.
- Broaden only to adjacent tests for the changed feature, then to package-level or full commands when the change crosses package boundaries.
- Do not fix unrelated failures unless they block validation of the current change; record them separately in the handoff.

## Provider Recording Fails Because Credentials Are Missing

Symptoms:

- Recording with `--record-mode=rewrite` fails before a request with missing API-key errors.
- A provider fixture uses a mock key in playback but real credentials are required for recording.
- `.env` is missing or not sourced.

Fix:

- Confirm recording is actually necessary; deterministic `TestModel`, `FunctionModel`, or mocked HTTP clients may be enough for non-provider behavior.
- Ask for explicit approval before sourcing credentials or making live paid requests.
- Use `source .env && uv run pytest path/to/test.py::test_name --record-mode=rewrite` only after credentials are available.
- Re-run the same test without `--record-mode` to prove playback.
- Never copy credential values, local `.env` contents, or private environment details into docs, skills, commits, or public logs.

## VCR Playback or Cassette Usage Fails

Symptoms:

- VCR cannot match a request even though a cassette exists.
- A successful test fails teardown with unused interactions.
- `scripts/check_cassettes.py` reports orphaned cassettes.
- xAI tests do not use normal HTTP cassette behavior.

Fix:

- Confirm the test name, parameter IDs, and cassette file path match the project’s cassette naming convention.
- Inspect request method, path, host, and body changes; path and host matching are customized for AWS-related normalization but request-shape changes can still break playback.
- If the expected request changed, rewrite only the targeted cassette and review the diff.
- If the test no longer needs an interaction, remove or update the cassette and run `uv run python scripts/check_cassettes.py`.
- For xAI provider tests, inspect `.xai.yaml` behavior through the custom xAI cassette fixture instead of assuming standard VCR YAML.
- For URL-download VCR tests, add or use `disable_ssrf_protection_for_vcr` so recorded hostnames can replay.

## Cassette Contains Sensitive or Noisy Data

Symptoms:

- A cassette diff includes credentials, tokens, account identifiers, dates, compressed blobs, unstable headers, or smart quotes.
- A reviewer flags cassette contents as unsafe or noisy.

Fix:

- Rely on the project serializer for normal JSON/header/token redaction, then manually review the cassette diff.
- Use the one-time scrubber only when intentionally mutating a cassette through the serializer.
- Remove or redact any residual sensitive value before committing.
- If a provider returns new sensitive fields, update the serializer or fixture redaction path and add a focused test for the scrub behavior.
- Keep cassette diffs separate from source diffs during review when possible.

## Snapshot Updates Are Confusing

Symptoms:

- A test warns that a snapshot mismatched.
- `snapshot()` without a value raises an error.
- Provider output churn causes large inline snapshot diffs.

Fix:

- For new snapshots, run with `--inline-snapshot=create`.
- For intentional updates, run with `--inline-snapshot=fix`, `--snap`, or `--snap-fix`.
- Review semantic changes; do not blindly accept provider text drift.
- Replace expected-varying fields with matchers such as `IsStr`, `IsDatetime`, `IsBytes`, or `IsSameStr`.
- For schemas, consider helpers that remove docstring-derived descriptions when the test is about structure rather than prose.

## Optional Dependency or Backend Tests Skip

Symptoms:

- Tests skip because optional extras such as provider SDKs, MCP/FastMCP, durable backends, UI packages, or local model packages are not installed.
- A provider fixture skips with an import error.
- A durable/backend integration test cannot reach its service.

Fix:

- Decide whether the skip is acceptable for the current change. Optional extras are intentionally optional.
- For package metadata changes, install the smallest relevant extra rather than all heavyweight extras.
- Prefer no-network import/config diagnostics before live provider or service tests.
- For durable execution changes, validate core semantics with deterministic tests first, then run backend-specific tests only when the backend is available.
- Record skipped optional checks in the handoff instead of claiming they passed.

## Docs Example Tests Fail

Symptoms:

- `tests/test_examples.py` fails on a docs or docstring snippet.
- Ruff failures appear inside docs code blocks.
- An example requires another example file or a provider mock does not match the snippet.

Fix:

- Inspect the code fence prefix settings: `test`, `lint`, `requires`, `py`, `max_py`, `title`, and `dunder_name`.
- Keep examples in context-before-code-after-caveats order and avoid inline suppressions where fence-level settings are more appropriate.
- Add required example dependencies through `requires` only when the docs harness can find them.
- Prefer mockable, deterministic examples over `test="skip"`.
- If a new docs page was added, register it in `mkdocs.yml`.
- Keep provider-specific details in provider docs and link there rather than duplicating long lists in general docs.

## Public API Compatibility Is Unclear

Symptoms:

- A proposed signature, class, setting, import path, message part, or event shape may break user code.
- A reviewer asks why a new kwarg belongs on `Agent` or another central class.
- A change removes or renames a public identifier.

Fix:

- Apply the version-policy summary: V1 minor releases should not intentionally break documented public behavior; deprecated functionality stays until V2, while beta surfaces may change faster.
- Check whether the behavior belongs in a capability, toolset, model setting, provider/profile fact, or wrapper instead of a central constructor kwarg.
- Keep old public names as deprecated aliases when renaming is necessary.
- Add tests for both new behavior and compatibility behavior.
- Update docs and generated skills so users and future agents learn the migration path.
- For serialized messages/events/specs, code defensively around optional new fields and new part/event variants.

## Generated Skills Are Stale

Symptoms:

- Public docs, API signatures, examples, package metadata, or maintainer workflows changed but `skills/pydantic-ai/` still teaches older behavior.
- A root router sends users to the wrong sub-skill.
- The user-facing installed package skill under `pydantic_ai_slim/pydantic_ai/.agents/skills/` no longer matches current mechanics.

Fix:

- Identify which sub-skill owns the changed surface using `repository-layout.md`.
- Update the runtime skill under `skills/pydantic-ai/sub-skills/...` with distilled, self-contained guidance.
- Keep review/test artifacts under `skills/tests/pydantic-ai/`, not in runtime skill directories.
- Update root provenance/refresh guidance when present, especially if commit, evidence paths, routing, or package metadata changed.
- Update `pydantic_ai_slim/pydantic_ai/.agents/skills/building-pydantic-ai-agents/` when installed user-facing agent guidance needs the change.
- Verify internal links and safe helper scripts after editing generated skills.

## Pre-commit or Hook Failures

Symptoms:

- `check-yaml`, `check-toml`, trailing whitespace, codespell, `zizmor`, no-RST-syntax, help-output, format, lint, typecheck, or cassette hooks fail.
- Generated GitHub workflow lock files or cassettes trigger hook exceptions.

Fix:

- Run the specific hook command locally if the error names one.
- For Python style failures, prefer `make format` or targeted `ruff format` and `ruff check --fix`.
- For no-RST-syntax failures, replace RST-only docstring syntax with Markdown code spans and fenced code blocks.
- For CLI help-output failures, run the targeted help/readme update test for the CLI package.
- For cassette hook failures, run `uv run python scripts/check_cassettes.py` and reconcile orphaned files or tests.
- Do not hand-edit generated workflow lock files unless the workflow compiler explicitly requires it.

## Dependency or Lockfile Churn Is Large

Symptoms:

- `uv.lock` changes far more than expected.
- Dependency updates pull in unrelated packages.
- Optional extras become required inadvertently.

Fix:

- Reset generated lock changes and regenerate from a clean base using the project’s normal install/sync target.
- Confirm the dependency belongs in the correct package and optional group.
- Prefer optional extras and deferred imports for provider/backend-specific packages.
- Check Python version markers and supported Python versions.
- Explain any unavoidable lock churn in the handoff.

## Review Context Scripts Fail

Symptoms:

- PR review context scripts fail because `gh`, `jq`, network access, PR metadata, or a base branch fetch is unavailable.
- The script writes context to a path that is not appropriate for the current workflow.

Fix:

- Treat the scripts as maintainer automation, not required runtime instructions.
- For local review, gather equivalent context with `git status`, `git diff --stat`, `git diff -W`, and the relevant `AGENTS.md` files.
- Do not copy temporary review context outputs into generated runtime skills.
- If modifying the scripts, keep changes scoped to the consumer that uses that script.

## Wrong Skill Boundary

Symptoms:

- Maintainer guidance drifts into public user workflow guidance.
- Provider cassette work is documented only under repo development.
- CLI help changes are tested but the CLI user skill is not updated.

Fix:

- Keep this sub-skill focused on editing the repository itself.
- Cross-link to public sub-skills for changed API behavior.
- Route provider cassette mechanics to this reference for validation workflow and to `../models-and-providers/` for provider semantics.
- Route CLI tests and command behavior to `../cli-and-apps/` when present.
- Route root provenance, refresh, and import readiness decisions to the generated skill root.
