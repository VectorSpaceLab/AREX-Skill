---
name: qa-and-test-runner
description: "Operate LaVague QA and lavague-test workflows for
  Gherkin-to-pytest generation and benchmark/static-site configs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# qa-and-test-runner

Use this sub-skill when the user wants to turn Gherkin feature files into pytest-bdd files with `lavague-qa`, or wants to validate/run LaVague benchmark-style site configs with `lavague-test`.

## Route first

- For Gherkin-to-pytest generation, read [QA CLI reference](references/qa-cli-reference.md) and validate the feature file with [scripts/lavague_qa_feature_probe.py](scripts/lavague_qa_feature_probe.py) before spending LLM/browser time.
- For benchmark or local-site config work, read [test-runner reference](references/test-runner-reference.md) and validate the YAML with [scripts/lavague_tests_config_probe.py](scripts/lavague_tests_config_probe.py) before launching a browser.
- For exact feature and site YAML shapes, operator/property vocabulary, and generated file naming, read [data formats](references/data-formats.md).
- For failures and cost/risk controls, read [troubleshooting](references/troubleshooting.md).
- For provider contexts, model credentials, custom `context`/`token_counter` files, and optional model packages, route to [contexts-and-retrievers](../contexts-and-retrievers/SKILL.md).
- For Selenium/Playwright browser binaries, headless behavior, driver sessions, iframes, and browser installation issues, route to [browser-drivers](../browser-drivers/SKILL.md).

## Safe default workflow

1. Do a file-only probe first. Do not run `lavague-qa` or `lavague-test` until inputs validate and the user accepts browser, network, and model-provider use.
2. Prefer explicit inputs over package defaults:
   - `lavague-qa --url <site-url> --feature <file.feature>`
   - `lavague-test --directory <sites-dir> --site <site-name>`
3. Use a custom context file only when it defines both `context` and `token_counter`; otherwise route to context guidance.
4. Treat `--full-llm`, live public websites, browser display, and database logging as opt-in because they can add token cost, network dependence, local browser state, or persistent files.
5. After generation, run generated pytest only when a browser, target site, and provider credentials are available and permitted.

## Expected observations

- `lavague-qa` creates `generated_tests/<feature-stem>.feature` and `generated_tests/<feature-stem>.py`; with `--full-llm`, the Python file stem ends in `_llm`.
- `lavague-test` prints per-task success/failure lines and a final success percentage; its process exit is successful only when every expectation passes.
- Both workflows ultimately use Selenium-backed LaVague agents, so live execution requires browser support and model-provider access even when static probes pass.
