# Troubleshooting LaVague QA and test-runner workflows

## `lavague-qa` reports missing `--url` or `--feature`

- Pass both flags explicitly: `lavague-qa --url <site-url> --feature <file.feature>`.
- Do not depend on demo defaults; they are only available in environments where package example files are discoverable.
- Use `python scripts/lavague_qa_feature_probe.py --url <site-url> --feature <file.feature>` to catch missing paths before a live run.

## Malformed Gherkin or empty scenarios

Symptoms: parser errors, no scenarios, no generated pytest, or action/assertion mismatch.

Checklist:

- The file contains `Feature:` and at least one `Scenario:`.
- Use at least one `Given`, one `When`, and one `Then`.
- Avoid `And` before a preceding `Given`/`When`/`Then`; `And` inherits the previous step type.
- Keep one scenario per feature file. The generator selects the first scenario.
- Keep one `Then` outcome per generated pytest when possible; only the first outcome is used by the generator path.
- Rename nearly identical steps that would normalize to the same Python function name.

## Generated pytest file has the wrong name or cannot find the feature

Expected names:

- Default mode: `generated_tests/<feature-stem>.py`
- Full LLM mode: `generated_tests/<feature-stem>_llm.py`
- Copied feature: `generated_tests/<feature-stem>.feature`

The generated Python file calls `scenarios('<feature-basename>.feature')`. Keep the copied feature beside the generated Python file or edit the scenario path.

## Default generation fails because the agent took extra or fewer steps

Default mode assumes the live agent's logged actions map to the Gherkin action steps. If the agent completes extra navigation, skips a step, or merges actions, pytest building can fail or produce missing step functions.

Options:

1. Rewrite the Gherkin into smaller, one-action steps.
2. Add clearer page landmarks or expected text in the prompt.
3. Regenerate with `--full-llm` only after accepting increased token/cost and variability.
4. Inspect generated pytest before running it against a real site.

## `--full-llm` is expensive or inconsistent

`--full-llm` asks the multimodal LLM to generate the whole pytest file. It can improve alignment when deterministic generation fails, but it uses more tokens and may produce different code on each run.

Controls:

- Use it only after the probe passes and default generation is insufficient.
- Set token/cost expectations with the user before running.
- Prefer a custom low-cost context only if it is compatible with LaVague QA's needs.
- Keep generated output under review before committing or running it.

## Custom context file fails

Both CLIs execute the `--context` Python file and require two variables:

- `context`: a LaVague `Context` with `llm`, `mm_llm`, and `embedding`.
- `token_counter`: a `TokenCounter` instance.

If the file imports a provider package that is not installed, or if credentials are missing, route to the context sub-skill. Never put secret values in the generated skill or in committed context files.

## Browser, LLM, and network requirements

Static probes do not prove live execution. Live `lavague-qa` and `lavague-test` need:

- A usable Selenium/Chrome environment.
- Model-provider credentials and network access for the selected context.
- Access to the target website or local server.
- User permission for public web navigation, potential log files, and token spending.

If Chrome/Chromedriver or browser libraries are missing, route to the browser-driver sub-skill. If provider setup is missing, route to the context sub-skill.

## Headless, display, and local browser behavior

- `lavague-qa --headless` opts into headless mode. Without it, the browser may be visible.
- `lavague-test` is headless by default; `--display` makes the browser visible.
- Some sites behave differently in headless mode or block automation. Retry headed only if an interactive browser is acceptable.
- Login, CAPTCHA, cookie banners, pop-ups, and profile-dependent flows may require browser-driver guidance.

## `--log-to-db` creates persistent logs

`--log-to-db` enables SQLite logging for agent runs. Use it for debugging only when persistent local files are acceptable. Avoid it for clean probes, sensitive sites, or runs where filesystem artifacts are prohibited.

## Site config schema errors

Common issues:

- Missing or empty `tasks` list.
- Missing task `prompt`.
- Missing task `url` for a `web` task.
- Top-level `type` omitted. Although docs describe web defaults, adding `type: web` makes configs more portable across releases.
- `user_data` is not a mapping.
- `max_steps` or `n_attempts` is not an integer.

Run:

```bash
python scripts/lavague_tests_config_probe.py --config sites/example-site/config.yml
```

## Expectation operator/property errors

Valid properties are case-sensitive: `URL`, `Status`, `Output`, `Steps`, `HTML`, `Tabs`.

Valid operators are: `is`, `is not`, `is lower than`, `is greater than`, `contains`, `does not contain`.

Examples of fixes:

- Replace `url is https://...` with `URL is https://...`.
- Replace `Page contains Welcome` with `HTML contains Welcome` or `Output contains Welcome`.
- Probe numeric comparisons before relying on them because installed parser versions may not cast numbers automatically.

## Static local site setup fails

For `type: static`:

- Use an integer `port`, for example `8000`.
- Keep the static directory under the site folder, commonly `www`.
- Ensure the task `url` points to that port, for example `http://localhost:8000`.
- Ensure the port is free before a live run.

The config probe checks the directory reference but does not start the server.

## Dynamic local sites are not automatically managed

The documented dynamic-site initialization flow is not implemented. Start the dynamic app yourself, verify it responds, then run `lavague-test` with `type: web` and an explicit local URL. Stop the server when finished.

## Import-time warnings before CLI help

Some LaVague imports can emit telemetry, package-resource, or NLTK data warnings before CLI help. These warnings do not always block CLI usage, but they can indicate environment setup work:

- Set LaVague telemetry according to the root troubleshooting guidance when silent/non-reporting runs are needed.
- If NLTK data downloads are blocked, pre-seed the required data in a trusted environment rather than allowing unexpected network fetches.
- If `pkg_resources` import errors appear under very new packaging tooling, use the root install troubleshooting guidance for compatible package versions.
