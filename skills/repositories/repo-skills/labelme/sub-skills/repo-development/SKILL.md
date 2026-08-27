---
name: repo-development
description: "Guides labelme repository maintenance, domain vocabulary,
  changelog policy, issue labels, tests, translation updates, release notes, and
  GUI test constraints."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# Repo Development

Use this route when the task is to modify, review, test, document, or release
the `wkentaro/labelme` repository rather than only operate the installed app.

## Start here

1. Read `references/contributor-guidance.md` for changelog, domain, issue-label,
   and AI Assist policy.
2. Read `references/testing-and-maintenance.md` before choosing commands.
3. Use `scripts/select_labelme_tests.py changed/path.py ...` to get focused test
   suggestions, then run the relevant command in a prepared checkout.
4. For GUI/e2e tests on Linux, prepare a display or Xvfb. Headless unit tests
   and example conversion checks are safer defaults.
5. If a change touches domain terminology or a decision recorded in an ADR,
   use the glossary/ADR vocabulary rather than inventing synonyms.

## High-value evidence by change area

- CLI/parser changes: `tests/unit/__main___test.py`, `labelme --help`,
  `labelme --version`.
- Config/Settings changes: `tests/unit/_config`, settings dialog tests, ADR-0001.
- Annotation File codec changes: `_label_file` tests, data-format docs, ADR-0002
  and ADR-0006.
- Shape/canvas geometry changes: `_shape` tests, canvas tests, ADR-0004.
- AI Assist/Text Prompt changes: `_automation` unit tests, fake OSAM sessions,
  selected e2e AI text tests only with display.
- Example converter changes: run the corresponding converter on tiny example
  inputs in a disposable output directory.
- Translation changes: `make check_translate` or `tools/update_translate.py --check`.

## Policies

- User-facing changes go in `CHANGELOG.md` under `## [Unreleased]`, in the
  proper Keep a Changelog subsection, with PR number links when available.
- Breaking changes should be prefixed with `**Breaking:**`.
- Issue triage roles map to labels named exactly `needs-triage`, `needs-info`,
  `ready-for-agent`, `ready-for-human`, and `wontfix`.
- Domain docs use a single-context layout: `CONTEXT.md` plus `docs/adr/`.
- Prompt Compatibility for AI Assist must be enforced before model download or
  inference.

## References and helper

- `references/contributor-guidance.md` captures repo-specific agent policies.
- `references/testing-and-maintenance.md` maps source areas to test commands and
  CI requirements.
- `references/troubleshooting.md` covers common maintainer blockers.
- `scripts/select_labelme_tests.py` suggests focused commands from changed paths.
