# Software Company Troubleshooting

## Placeholder or Missing API Key

Symptoms:

- Importing config-backed APIs fails before any useful output.
- CLI starts but provider calls fail authentication.
- Config validation or provider logs mention missing `api_key`, `YOUR_API_KEY`, quota, or unauthorized access.

Diagnosis:

```bash
metagpt --init-config
metagpt --help
```

Fix:

- Edit `~/.metagpt/config2.yaml` and replace `llm.api_key: "YOUR_API_KEY"` with a real secret.
- Do not paste the secret into prompts, generated docs, or source files.
- Remember precedence: `~/.metagpt/config2.yaml` overrides `config/config2.yaml`. A stale user config can hide a fixed checkout config.
- Confirm `llm.api_type`, `llm.model`, and `llm.base_url` match the provider. OpenAI-compatible base URLs commonly end with `/v1`.

## Python Version Unsupported

Symptoms:

- Install resolution fails on Python 3.12+.
- Runtime dependency conflicts appear immediately after install.

Fix:

- Use Python `>=3.9,<3.12`; Python 3.9 or 3.10 is the safest target.
- Recreate the environment instead of forcing incompatible dependencies.

## Slow or Partial Dependency Install

Symptoms:

- `pip install metagpt` or editable install is slow.
- Optional imports fail for search, RAG, browser, Android, or test extras.
- Install fails with permission errors in system site-packages.

Fix:

- Install into an isolated environment, then install the base package first.
- Use `pip install -e . --user` only when the user intentionally installs into user site-packages.
- Install optional extras only for the requested capability; full test/RAG/browser extras are heavy.
- For actual runtime, ensure core requirements are installed before running project generation.

## Mermaid, Node, and Browser Rendering

Symptoms:

- Diagram export fails even though code generation proceeds.
- Errors mention `mmdc`, Puppeteer, Chromium, Playwright, pyppeteer, browser executable, or `getElementsByTagName SyntaxError`.

Fix:

- Treat diagram rendering as optional unless the user specifically needs rendered charts.
- Install Node.js and Mermaid CLI if using `mmdc`; Node 14+ is required for older Mermaid errors, and current stable Node is preferable.
- If Chromium download is undesirable and a browser is already installed, set `PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true` before installing browser tooling.
- Alternative engines can be configured under `mermaid.engine`: `playwright`, `pyppeteer`, or `ink`.
- For Playwright, install browsers explicitly with `playwright install --with-deps chromium` when PDF rendering is needed.
- `mermaid.ink` avoids local browser setup but does not support PDF export.

## Typer or Click Help Compatibility

Symptoms:

- `metagpt --help` fails with Typer/click formatting errors.
- Boolean options are rejected.

Fix:

- First run the safe inspection script: `python sub-skills/software-company/scripts/inspect_role_action.py --check-cli-help --json`.
- Use exact boolean pairs from the installed help, such as `--code-review/--no-code-review`, `--run-tests/--no-run-tests`, `--implement/--no-implement`, `--inc/--no-inc`, and `--init-config/--no-init-config`.
- If help itself crashes, inspect installed Typer/click versions and align them with the package requirements rather than editing CLI code.

## Incremental Mode Misuse

Symptoms:

- `--inc` creates or targets the wrong project.
- MetaGPT cannot find the existing project.
- Generated changes do not apply to the intended repository.

Fix:

- Pair `--inc` with either `--project-name <existing_workspace_name>` or `--project-path <existing_project_root>`.
- Use the project root, not an individual source file, for `--project-path`.
- Use `--reqa-file` only when rewriting QA code for a specific source file.
- Avoid reusing `--project-name` for unrelated new projects.

## Recovery Path Invalid

Symptoms:

- `FileNotFoundError` says the path does not exist or does not end with `team`.
- Recovery says `team.json` is missing.

Fix:

- Pass a directory whose path string ends in `team`.
- Ensure that directory exists and contains `team.json` from a prior serialized team archive.
- Do not pass the parent storage directory or the `team.json` file itself.
- Remember recovery uses the serialized `company.idea`; the CLI idea text is ignored after successful deserialization.

## LLM or Provider Failures

Symptoms:

- Provider replies with quota, rate-limit, model-not-found, proxy, timeout, or connection errors.
- Output says something generic like "Absolutely! How can I assist you today?" instead of following the SOP.
- PRD or code generation stalls.

Fix:

- Check billing/quota and rate limits; reduce RPM or budget when hitting rate limits.
- Verify model access. Some providers require billing before higher-tier models are available.
- Confirm network access to the configured `base_url`; use a correct proxy only when required by the user environment.
- Prefer long-context, higher-quality models for larger projects; short-context models are more likely to truncate or hallucinate APIs.
- For Claude, use a provider or compatibility proxy supported by the installed MetaGPT config; the older codebase does not include every native Claude path.
- For Ollama/local models, expect context-window limitations and lower success on complete software-company workflows unless the model is large enough.

## Custom Role or Action Construction Fails Early

Symptoms:

- Importing a custom `Action` or constructing a custom `Role` fails before `Action._aask(...)`, `Team.run(...)`, or project generation is called.
- Errors mention config validation, placeholder API keys, unsupported provider fields, `ModelsConfig`, or `create_llm_instance`.
- A dry script that only calls `Role.set_actions(...)` fails in an environment with a stale or placeholder `config2.yaml`.

Diagnosis:

```bash
python sub-skills/software-company/scripts/inspect_role_action.py --json
```

Fix:

- Treat `Role` and `Action` construction as config-touching, but not network-spending: `ContextMixin`, `Role._process_role_extra(...)`, `Role.set_actions(...)`, and `Action.llm_name_or_type` can initialize LLM objects from `config2.yaml` before the first LLM request.
- Replace placeholder config values before constructing real custom roles, even if the custom action has not called `_aask(...)` yet.
- For no-LLM inspection, use the bundled `inspect_role_action.py` script; if imports fail, it falls back to source-signature inspection and reports the import/config error instead of calling `_aask(...)`, `Team.run(...)`, or `generate_repo(...)`.
- For local unit tests of custom role wiring, prefer a minimal explicit config/context or an action that overrides `run(...)` without calling `_aask(...)`; reserve `Team.run(...)` for provider-backed integration checks.
- If `llm_name_or_type` is set on an `Action`, verify that the matching entry exists under `models` in `config2.yaml`; otherwise MetaGPT falls back to the default `llm` configuration.

## Long or Truncated Outputs

Symptoms:

- Code files contain incomplete functions.
- Parsing of code blocks or markdown fails.
- Larger projects contain non-existent APIs or partial database setup.

Fix:

- Reduce scope in the one-line idea or ask for a smaller milestone.
- Increase model context/output limits through provider config when available.
- Use `--n-round` and `--investment` deliberately; more rounds can improve coverage but spend more.
- For generated projects over a few hundred lines, plan manual review and test execution.
- Use incremental mode for follow-up fixes instead of asking for a very large project in one prompt.
