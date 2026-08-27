---
name: repo-development
description: "Contributor guidance for SimpleTuner planning, tests, docs,
  frontend verification, and privacy-safe public text."
disable-model-invocation: true
metadata:
  disco-role: operating
license: AGPL 3.0
---

# Repo Development

Use this sub-skill when the task is to modify SimpleTuner source, tests, docs, WebUI code, cloud/server code, packaging, or contributor-facing guidance. It is not for ordinary user-facing training, dataset preparation, model selection, WebUI operation, API operation, or cloud job execution; route those to the task-specific SimpleTuner sub-skill unless the user is editing that code path.

## Start Here

1. Read [testing-guide.md](references/testing-guide.md) before selecting validation commands.
2. Read [frontend-docs-and-privacy.md](references/frontend-docs-and-privacy.md) for WebUI event-flow changes, docs/translations, or any public text.
3. Use [codebase-map.md](references/codebase-map.md) to map changed files to focused tests.
4. Use [troubleshooting.md](references/troubleshooting.md) when a plan is vague, pytest appears, E2E is missing, docs/templates are incomplete, privacy scanning blocks text, or untracked files were touched.

## Non-Negotiable Contributor Rules

- SimpleTuner uses `unittest`; do not use pytest for validation commands.
- Preferred local full command: `.venv/bin/python -m unittest -v -f`.
- The full test suite averages about 300 seconds. Use focused tests while iterating, then run the broader command when the touched area warrants it.
- Never commit or push unless the user explicitly asks.
- Preserve untracked files. Do not remove untracked files unless the user explicitly instructs you to do so.
- Plans must include a verifiable root cause, affected file paths, line/function targets, proposed minimal changes, pitfalls, and edge cases.
- Keep code changes minimal. Do not add fallback paths or defensive masking unless the requirement makes that behavior necessary and user-expected.
- Do not hide import failures, and use `type: ignore` only when unavoidable.
- If changing a dataloader/dataset configuration option, update the corresponding WebUI Dataset template and dataloader documentation/translations.
- Before any public text is published, scan the exact title/body/comment/model-card/release text with the bundled privacy scanner.

## Useful Helpers

- `scripts/select_unittest_targets.py`: maps changed repo-relative paths to focused `unittest`, Jest, and Selenium E2E suggestions. It never suggests pytest.
- `scripts/scan_public_text_privacy.py`: scans public text from files or stdin and reports only `Blocked: local machine identity was found in public text.` when a forbidden local-identity pattern appears.

## Quick Routing

- Config, CLI parser, environment, option, or config-template change: follow the config rows in [codebase-map.md](references/codebase-map.md) and [testing-guide.md](references/testing-guide.md).
- Dataloader/data-backend change: include data-backend unit tests, WebUI Dataset template checks, and docs/translations.
- Model registry, model family, adapter, LoRA, or checkpoint tooling change: use model/adapter tests and consider transformer or pipeline tests only when runtime behavior changes.
- WebUI template, Alpine store, JavaScript, event, or form-state change: run relevant Jest tests and Selenium E2E when event flow, form dirty state, or Alpine reactivity is involved.
- Cloud/server/API/queue change: use mocked CLI/API/server tests; do not submit cloud jobs or rely on credentials by default.
- Public publishing, PR text, Hub model cards, comments, release notes, or validation summaries: use the privacy scanner first.

## Handoff Expectations

When you finish a repo-development task, report repo-relative files changed, focused and broad tests run, docs/translations touched, whether Selenium E2E was required, whether public text was scanned, and any intentional omissions or unresolved uncertainty. Do not include local absolute paths or raw terminal output in public-facing text.
