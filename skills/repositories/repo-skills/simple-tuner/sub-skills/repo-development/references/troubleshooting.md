# Repo Development Troubleshooting

## Pytest Was Used by Mistake

Symptom: a plan, command, or validation note uses pytest.

Action: stop and replace it with `unittest` commands. Use `.venv/bin/python -m unittest -v -f` for the full local suite or a focused `tests.<module>` command for iteration. Do not report pytest as accepted SimpleTuner validation.

## E2E Was Skipped for an Alpine/Form/Event Bug

Symptom: a WebUI change affects event propagation, form dirty state, Alpine reactivity, or direct-load/tab-switch behavior, but only Jest/JSDOM was run.

Action: add or run Selenium E2E. For dirty-form work, include `FormDirtyStateFlowTestCase` and `EasyModeFormDirtyTestCase`. Jest can support pure JS logic but cannot prove DOM bubbling, Alpine event modifiers, real rendering, or template/store integration.

## Docs Translations or Indexes Are Missing

Symptom: English docs changed but translations, mkDocs nav, or index pages were not updated.

Action: update matching translated files for existing docs. For new docs, add `zh`, `ja`, `pt-BR`, `es`, and `hi` translations. Update `mkdocs.yml` and section index pages when navigation or custom indexes change. Preserve Markdown formatting and code blocks.

## Dataloader Option Missing WebUI Template

Symptom: a dataloader/dataset setting is added to backend config but not surfaced in WebUI Dataset templates or dataset blueprints.

Action: require the WebUI update before accepting the plan. Check `simpletuner/templates/components/dataloader/`, dataset blueprint code, `documentation/DATALOADER*.md`, and `documentation/OPTIONS*.md` when applicable. Add focused tests for config validation and template/blueprint behavior; add Selenium E2E if the field changes dynamic form behavior.

## Public Text Privacy Scan Blocks

Symptom: the scanner returns `Blocked: local machine identity was found in public text.`

Action: do not print the offending line. Rewrite the exact public text using repo-relative paths and generic validation notes. Remove local home paths, usernames, hostnames, temp/cache paths, raw terminal output, and attribution trailers. Scan again before publishing.

## Plan Is Too Vague or Has No Root Cause

Symptom: a plan says what to change but not why, does not name affected functions/files, omits edge cases, or proposes broad new infrastructure without proving existing paths are insufficient.

Action: reject or pause the plan. Require a verifiable root cause, line/function targets, minimal code changes, test proof, pitfalls, known edge cases, and a proposal to remove/refactor old code when adding new infrastructure. Do not proceed on assumptions.

## Untracked Files Were Removed or Threatened

Symptom: cleanup commands would delete untracked files or an untracked file disappeared during work.

Action: stop destructive cleanup. Preserve untracked files unless the user explicitly instructed removal. If a removal happened, report it immediately and attempt safe recovery from editor buffers, shell backups, or VCS-independent copies before continuing.

## Unjustified Fallback or Defensive Masking

Symptom: a change catches broad exceptions, hides import failures, adds alternate behavior not requested by users, or uses `type: ignore` casually.

Action: remove the fallback or document why the fallback is required and user-expected. Import failures should normally be visible. Prefer direct tests that prove the real failure mode.

## Checkpoint Resume Topology Assumption

Symptom: a plan assumes checkpoint resume remains valid after changing distributed topology, data settings, batch sizing, accumulation, shuffling, bucket splitting, or dataloader configuration.

Action: do not add compatibility fallbacks unless the user explicitly requires that support and it is verified. Treat topology/data resume changes as risky and document the constraint.

## Selenium E2E Skips Unexpectedly

Symptom: `tests.test_webui_e2e` reports skipped tests.

Action: confirm Selenium was enabled with `SIMPLETUNER_SELENIUM_TESTS=1`, a supported browser/driver is available, and the selected browser list is valid. If the change requires E2E and the local environment cannot run it, report the unresolved verification gap rather than claiming browser coverage.
