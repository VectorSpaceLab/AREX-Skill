# Maintainer workflows

Use this reference for broad Kiln checkout maintenance: where code belongs, which review standards apply, and which actions need human confirmation.

## Monorepo layout

Kiln is a multi-project workspace:

| Path | Responsibility | Maintenance notes |
| --- | --- | --- |
| `libs/core/` | Python library with core Kiln functionality: projects, tasks, runs, adapters, evals, synthetic data, fine-tuning, RAG, and shared datamodels. | This is public SDK/library surface. Avoid breaking existing APIs without explicit user confirmation. Public classes and visible SDK objects need docstrings written for third-party developers. |
| `libs/server/` | FastAPI REST server around core library behavior. | Route and schema changes must meet OpenAPI standards and be checked against the generated web client. |
| `app/web_ui/` | Svelte 4 frontend using TypeScript, Tailwind, DaisyUI, and generated OpenAPI types. | Use existing app controls and design conventions. Run web lint/type/test/build checks for UI changes. |
| `app/desktop/` | Python desktop app packaging a FastAPI studio server, precompiled web UI, and browser launch behavior. | Desktop APIs extend the server and often interact with provider credentials, local services, Git sync, and jobs. |
| `specs/` | Specs for work that spans the repo. | Cross-project specs belong under root project specs; single-subproject specs belong under that subproject. |

When a change spans projects, decide the owning behavior first. Keep shared primitives in `libs/core/`, HTTP/server behavior in `libs/server/` or `app/desktop/studio_server/`, and UI presentation/state in `app/web_ui/`. Avoid unrelated refactors while fixing a scoped issue.

## General maintenance checklist

1. Identify the touched subprojects and the user-visible behavior being changed.
2. Read the relevant implementation and nearest existing tests before editing.
3. Prefer extending existing files, fixtures, controls, and helpers over adding parallel abstractions.
4. Keep changes strongly typed and well tested.
5. Run targeted checks while iterating, then the appropriate broad check before final handoff.
6. If a change reaches a public API, outward-facing release channel, paid provider, licensing boundary, or breaking SDK surface, stop for user/human confirmation.

## Code quality rules

- Python should be idiomatic, strongly typed, and Pydantic v2-compatible.
- Prefer `asyncio` for concurrency. Use threads only when there is a clear reason async cannot work.
- Avoid unnecessary comments. Comments should explain non-obvious why, not restate what the code does.
- Use the repository's enforced temporary-work marker only for work that must be resolved before merge, and remove all such markers before final handoff.
- Avoid `typing.cast`; project lint bans it. Prefer narrowing, helper functions, or explicit validation.
- Do not set globals on external libraries unless the code is clearly application-level and intentionally owns that global state.
- Use `json.dumps(..., ensure_ascii=False)` in Python.
- Keep performance-critical adapter paths free of repeated file I/O, blocking I/O, and unnecessary per-call work.
- Treat copyleft/GPL dependency additions as a critical human/legal issue. Do not approve or add them on your own.

## Python test-writing standards

- Use pytest.
- Review the code under test before adding tests; do not assume the implementation is correct.
- Prefer adding to an existing appropriate test file. Create a new test file only after confirming no suitable file exists.
- Keep tests brief through fixtures, helper functions, and `pytest.mark.parametrize` where appropriate.
- Use `unittest.mock` / `patch` for mocks.
- Run the new or changed test directly before broad checks.
- If a likely bug is discovered, write a focused failing test, confirm the failure, and ask before fixing when the user's intent is uncertain.

## API and OpenAPI review boundaries

For FastAPI route and Pydantic API changes, route detailed behavior to `server-desktop-web-api`, then verify these repo-wide standards:

- Every route decorator needs `tags=[...]` and a short unique `summary=`.
- Route paths should use plural nouns, no trailing slash, and consistent prefixes for related resources.
- `GET` must be side-effect-free except browser-required SSE routes; mutating actions should use `POST`, `PATCH`, or `DELETE`.
- Every path parameter needs `Path(description=...)`; every query parameter needs `Query(description=...)`.
- Pydantic request/response models used in APIs should have useful class docstrings when the name alone is not obvious.
- Fields that are not self-evident need `Field(description=...)`.
- Pydantic string constraints that should appear in OpenAPI should use `Annotated[..., StringConstraints(...)]`, not only validators.
- Routes that write project `.kiln` data should live under `/api/projects/{project_id}/...` so Git sync can see the project context.
- SSE routes that must stream directly need the correct no-write-lock behavior and cancellable stream response pattern.
- After API or schema changes, run the OpenAPI schema check and regenerate the web client only when intentionally updating generated files.

## SDK and compatibility boundaries

`libs/core/` is a library. Changes there can affect third-party developers, server behavior, desktop behavior, and generated docs.

Before changing visible SDK signatures, exported datamodel fields, adapter contracts, or task/run config behavior:

- Search for all call sites across the monorepo.
- Prefer backward-compatible additions over breaking changes.
- If a break is unavoidable, call it out explicitly and ask for confirmation.
- Keep docstrings clear for external developers rather than internal implementation readers.
- Preserve model-provider flexibility: do not use shipped `ModelName` enums to validate user-provided model IDs because remote config can add models not present in the local enum.

## Release, prerelease, and deprecation boundaries

Maintenance workflows can cross cost, credential, or outward-facing boundaries:

- Full repo checks are safe and local by default: `uv run ./checks.sh --agent-mode`.
- Prerelease checks are a curated paid smoke set and require credentials. They should be read-only and report findings unless the user separately asks for code changes.
- General model deprecation audits use provider model-listing endpoints and should not remove models automatically. Marking `deprecated=True` still requires user confirmation.
- Fine-tune deprecation audits report stale/unsupported fine-tune base models and should not remove support without confirmation.
- Release digest work produces a Slack-ready recap and must be shown to the user before posting.
- Model-list additions may require paid integration tests and public announcements. Confirm cost, provider credentials, and outward-facing copy before execution/posting.

## Human and legal boundaries

Never make these decisions as an agent:

- Fill out or attest a CLA.
- Add or change a license file.
- Choose or set a license tag such as OSS/MIT/proprietary.
- Approve GPL/copyleft dependency introduction.
- Post public/team release announcements without approval.
- Spend money on paid provider tests without explicit user direction and available credentials.

When such a boundary appears, stop and ask the user or state that a human decision is required.

## Evidence notes

Layout and quality rules came from `AGENTS.md`, `specs/monorepo.md`, `.agents/code_review_guidelines.md`, `.agents/api_code_review.md`, `.agents/python_test_guide.md`, root `pyproject.toml`, and the repository check script. Local maintenance skill boundaries came from the frontmatter and workflow descriptions in `.agents/skills/*/SKILL.md`.
