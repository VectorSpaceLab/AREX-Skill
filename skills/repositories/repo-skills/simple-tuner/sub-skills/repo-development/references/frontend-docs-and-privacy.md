# Frontend, Docs, and Privacy

## Frontend Test Boundary

SimpleTuner has two frontend validation layers with different guarantees:

- Jest/JSDOM tests in `tests/js/` cover isolated JavaScript logic. They mock Alpine.js and DOM APIs.
- Selenium E2E tests in `tests/test_webui_e2e.py` run through a real browser and the WebUI test server.

Jest/JSDOM does not prove Alpine event modifiers, DOM event bubbling, real browser rendering/timing, or integration between templates and Alpine stores. Use Jest to cover pure JS logic and local store helpers, then add Selenium E2E whenever the bug depends on the wired browser page.

## When Selenium E2E Is Required

Run or add Selenium E2E tests for changes involving:

- Event propagation or event modifiers such as `.stop`, `.prevent`, or `.self`.
- Form dirty state tracking and save-button enablement.
- Alpine template-to-store integration.
- Direct page load versus tab-switch behavior.
- Browser rendering or timing assumptions.

Command examples:

- `SIMPLETUNER_SELENIUM_TESTS=1 .venv/bin/python -m unittest -v -f tests.test_webui_e2e`
- `SIMPLETUNER_SELENIUM_TESTS=1 .venv/bin/python -m unittest -v -f tests.test_webui_e2e.FormDirtyStateFlowTestCase tests.test_webui_e2e.EasyModeFormDirtyTestCase`

The E2E harness starts a trainer-mode server, uses isolated WebUI state/config directories, defaults to headless Chrome unless browser variables are changed, captures screenshots/HTML/console logs for failing browser runs, and skips unless Selenium is explicitly enabled.

## Dirty-Form Checklist

For the `formDirty` to save-button flow, E2E coverage must verify all of these behaviors:

1. Direct page load, edit an Easy Mode field, save button enables.
2. Direct page load, edit a main form field, save button enables.
3. Switch tabs, edit a field, save button enables.
4. Save clears dirty state, then a new edit re-enables the save button.

A minimal dirty-form bug validation normally includes the relevant JS unit test plus `FormDirtyStateFlowTestCase` and `EasyModeFormDirtyTestCase`. Jest alone is insufficient because it cannot validate real event bubbling, Alpine modifiers, or template/store integration.

## Documentation and Translation Rules

SimpleTuner documentation is built with mkDocs Material and suffix-based i18n. When docs change:

- Update mkDocs navigation and custom index pages when adding, moving, or removing docs. Representative index pages include `documentation/index.md`, section index files, and the `mkdocs.yml` nav entries.
- Update all translations for an existing doc when the English source changes.
- For new docs, create translations for `zh`, `ja`, `pt-BR`, `es`, and `hi`.
- Keep Markdown structure, code blocks, commands, file paths, configuration keys, API endpoints, and model identifiers intact across translations.
- Translate prose, headings, UI labels/descriptions, alt text, and admonition titles.
- If adding a new option, update `documentation/OPTIONS.md` and its translations.
- If adding a dataloader setting, update `documentation/DATALOADER.md` and its translations, plus the corresponding WebUI Dataset template.

`documentation/TRANSLATING.md` documents the suffix-based convention and glossary; project instructions add the required `pt-BR`, `es`, and `hi` coverage for new documentation in this generated skill.

## Public Text Privacy Guard

Never publish local machine identity in public text. This includes commit messages, PR titles, PR bodies, PR comments, issue comments, release notes, model cards, Hub commit messages, generated metadata, validation summaries, and any API-driven comment or publication.

Forbidden public text includes:

- Local absolute home-directory paths.
- Local account names or workstation usernames.
- Hostnames or shell-prompt fragments that reveal a local machine.
- Temp/cache paths tied to local execution.
- Raw terminal output containing local identity.
- Co-author, reviewer, signer, or attribution trailers that expose personal names or emails.
- Pod/workspace paths unless intentionally public infrastructure paths.

Use repo-relative paths and generic commands in public text. Before any public publish action, scan the exact text that will be sent:

- From a file: `python skills/disco/simple-tuner/sub-skills/repo-development/scripts/scan_public_text_privacy.py PR_BODY.md`
- From stdin: `printf '%s' "$PUBLIC_TEXT" | python skills/disco/simple-tuner/sub-skills/repo-development/scripts/scan_public_text_privacy.py -`

If the scanner blocks content, do not print the matched line. Report only: `Blocked: local machine identity was found in public text.` Then rewrite to repo-relative, generic wording and scan again.

## Publishing Workflow

Do not commit or push unless the user explicitly asks. Before any push or public PR/comment/release/Hub publication:

1. Inspect the staged diff.
2. Inspect the exact commit message.
3. Inspect the exact PR title/body/comment/release/model-card text.
4. Run the privacy scanner on every public text payload.
5. Only publish after the scanner passes and the user has authorized the public action.
