# Contribution Guidelines

Use this reference to review the shape of a Pydantic AI repository change before writing or accepting code.

## Project-First Standard

Every change should serve the project, its users, and maintainers rather than only the immediate requester. Public APIs, docs, examples, errors, abstractions, tests, and generated agent skills are part of the product.

Default expectations:

- Prefer modern, concise, idiomatic Python with strict type safety.
- Keep PRs focused on the stated problem; do not include drive-by refactors or speculative sibling fixes.
- Design public surfaces thoughtfully because wrong abstractions are expensive to change later.
- Preserve backward compatibility according to the V1 version policy unless editing beta surfaces or explicitly preparing a major-version migration.
- Update docs, tests, examples, and generated skills together when behavior or mechanics change.
- Use maintainer-quality error messages: user-facing messages should wrap code identifiers in backticks and be actionable.

## Before Implementing

For non-trivial work, gather and test context first:

1. Read the issue or PR discussion and any linked issues.
2. Ask clarifying questions when scope, intended behavior, or maintainers’ preferred design is unclear.
3. Search nearby code, docs, tests, and prior issues/PRs for existing patterns.
4. For public API or feature work, verify the feature belongs in this repo rather than an external capability package or harness.
5. For a bug fix, reproduce the defect and choose the narrowest fix that resolves the reproduced behavior.

If there is no issue, no maintainer alignment, and the change is not trivial, help produce a concise issue, proposal comment, or temporary `PLAN.md` instead of rushing a large implementation.

## Scope and API Design

Pydantic AI favors strong primitives and general extension points over narrow one-off features.

When designing or reviewing APIs:

- Prefer capabilities, toolsets, model settings, provider/profile facts, or typed settings over adding new `Agent` constructor flags.
- Keep provider-specific behavior in providers, model adapters, profiles, or provider-native tool classes; do not scatter provider-name checks through core graph/tool/output code.
- Use keyword-only optional/config parameters and dataclass `KW_ONLY` markers where future optional fields may be added.
- Keep public API exports deliberate; prefix internal implementation details with `_` and avoid expanding `__all__` accidentally.
- Keep old names as deprecated aliases when renaming public API in a backward-compatible release.
- Use `Literal`, `TypedDict`, dataclasses, `Protocol`, or precise unions instead of `Any` when structure is known.
- Fix type errors with better annotations, narrowing, generics, or well-justified casts; do not hide them with broad ignores.

For package-specific edits, apply the nearest directory rules:

- `pydantic_ai_slim/pydantic_ai/`: read the slim architecture guide for non-trivial changes.
- `models/`: keep provider adapter behavior in provider-specific modules and apply response processing consistently to streaming and non-streaming paths.
- `providers/`: own authentication, clients, base URLs, HTTP lifecycle, and provider-level profile inference.
- `profiles/`: own intrinsic model-family capability facts and schema/request quirks.
- `capabilities/`: own cross-cutting instructions, settings, tools, wrappers, hooks, and event/history processing.
- `toolsets/`: preserve tool identity, lifecycle, instructions, and `call_tool` semantics across wrappers.
- `native_tools/`: pair user-facing native tools with capabilities and document provider support where users discover it.
- `durable_exec/`: treat durable runtimes as compatibility checks for core semantics, not peripheral adapters.
- `ui/`: keep adapter behavior backward compatible with the lower supported protocol/library version.

## Documentation Policy

Docs are product surface, not an afterthought.

When editing docs or docstrings:

- Write the project name as `Pydantic AI`.
- Use Markdown headings for sections and MkDocs admonitions for callouts.
- Use reference-style API links such as `[Agent][pydantic_ai.Agent]` in docs where API elements should be discoverable.
- Show the recommended approach first, then alternatives with explicit trade-offs.
- Keep provider-specific config and support notes in provider docs rather than duplicating long lists in general docs.
- Document current behavior, not historical implementation details.
- Register new `docs/` pages in `mkdocs.yml` navigation.
- Avoid `test="skip"` in docs examples unless external services, credentials, or nondeterminism make it unavoidable.
- For docs examples, use current/frontier model names and provider-prefixed identifiers where live models are intentional.

Doc examples are tested through `tests/test_examples.py`, which mocks models, HTTP clients, MCP servers, randomness, and many provider env vars. If docs fail, inspect the example prefix settings, missing `requires`, import ordering, skipped/linted flags, and mocked behavior before changing production code.

## Testing Policy

Pydantic AI prefers tests through public APIs and real provider behavior recorded as cassettes when provider behavior matters.

Use this hierarchy:

1. A targeted regression test that exercises the user-facing behavior.
2. A VCR-backed provider test when correctness depends on actual provider wire behavior or SDK behavior.
3. A unit test for internal behavior only when the condition is not reachable through public APIs or the cassette matcher would not protect the relevant payload shape.
4. A docs/example test when the change affects public examples or documentation snippets.

Each test should assert the core behavior introduced by the change. Do not add tests that only instantiate code without meaningful assertions.

## Validation Strategy

Use the narrowest validation that can catch mistakes in the changed area while iterating:

| Change type | First validation |
| --- | --- |
| Single test or bug fix | `uv run pytest path/to/test.py::test_name -q` |
| Source file type-sensitive change | `PYRIGHT_PYTHON_IGNORE_WARNINGS=1 uv run pyright path/to/file.py` |
| Python formatting/lint-sensitive change | `uv run ruff format path/to/file.py` then `uv run ruff check path/to/file.py` |
| Docs example or docstring change | `uv run pytest tests/test_examples.py -k "path_or_title" -q` or `make update-examples` when updating docs examples intentionally |
| Provider cassette change | Record with `--record-mode=rewrite`, verify playback without the flag, inspect cassette diffs, and run cassette checks. |
| CLI help change | Target the CLI test or help command, then update generated help docs/readmes if the repo requires it. |
| Dependency metadata change | Use the project install/sync flow to regenerate lock data; avoid manual lock edits. |

Full `make`, `make test`, and `make typecheck` are intentionally broad and slow. Use them only for final confidence or broad changes, not after every edit.

## Dependency and Workspace Changes

The project uses `uv`, multiple workspace packages, and dependency groups.

Rules:

- Use `make install` for local full setup and to regenerate lock files after dependency changes.
- Use `make sync` when updating local packages and `uv.lock` through the normal workspace sync path.
- Avoid adding heavyweight, GPU, cloud, or niche provider dependencies to core metadata unless the project’s model-integration policy supports it.
- Keep optional provider/backend dependencies optional and type-safe via deferred imports, `TYPE_CHECKING`, or explicit helpful errors.
- If a dependency change unexpectedly causes large lockfile churn, reset and regenerate from a clean base to isolate the intended change.

## Generated Skills and Agent Guidance

The root maintainer rules require generated skills to stay synchronized with user-facing mechanics.

When a change affects public APIs, docs, examples, config, tests, or maintainer workflows:

- Update the matching generated runtime sub-skill under `skills/pydantic-ai/sub-skills/`.
- Update the root skill’s provenance and refresh guidance when present.
- Update user-facing package skills under `pydantic_ai_slim/pydantic_ai/.agents/skills/building-pydantic-ai-agents/` when the installed package’s agent guidance changes.
- Update `.claude/skills/` only for repository workflow guidance used by maintainers, such as VCR testing or review workflows.
- Keep verification reports, usability cases, prompt samples, and review notes under `skills/tests/pydantic-ai/`, not under runtime skill directories.

## PR and Review Conventions

For PR-ready work:

- Include the project PR template and fill the linked issue number when applicable.
- PR titles feed the changelog; wrap code identifiers in backticks.
- The user should manually check any AI-generated-code checkbox in the UI.
- Do not add AI co-author trailers to commits.
- Prefer concise, actionable review feedback; avoid praise, noise, repeated nits, or comments that do not request a change or discussion.

For contribution triage:

- Trivial typos or obvious one-line fixes can go straight to PR.
- Non-trivial bugs should have a minimal reproducible example and ideally a trace link.
- Features and API changes need issue-level problem framing and maintainer alignment before a large implementation.
- Capabilities that do not require core/model-specific support may belong outside this repo.

## Area-Specific Quality Checks

Use these prompts when reviewing a change:

- Public API: Is the abstraction stable, typed, backward compatible, discoverable, and placed in the right layer?
- Provider behavior: Is provider-specific logic in providers/models/profiles, with cassettes or direct payload assertions where needed?
- Agent loop: Are tool/output ordering, retries, streaming, usage limits, durable execution, and message history preserved?
- Docs: Are examples current, tested, discoverable, and consistent with implementation and terminology?
- Tests: Does the test fail before the fix, exercise public behavior when possible, and avoid live credentials unless recording intentionally?
- Skills: Would a future agent using generated skills learn the correct new mechanics without reading the source repo?
