---
name: la-vague
description: "Operate LaVague browser-agent, model-context, driver,
  Gradio/server, and QA automation workflows safely with bundled probes and
  troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# LaVague repo skill

Use this skill when a task involves LaVague / lavague package workflows: AI web agents, Large Action Model browser automation, Selenium/Playwright action generation, provider contexts, retriever pipelines, Gradio demos, Chrome extension server, or LaVague QA/test-runner CLIs.

## Fast route map

| User task | Read next |
| --- | --- |
| Build or debug a `WebAgent`, `WorldModel`, `ActionEngine`, `PythonEngine`, logs, token counting, or `ActionResult` | `sub-skills/core-web-agent/SKILL.md` |
| Configure Selenium/Playwright, browser profiles, headless/headed mode, iframes, tabs, scrolling, screenshots, or browser binary failures | `sub-skills/browser-drivers/SKILL.md` |
| Choose OpenAI/Azure/Anthropic/Gemini/Fireworks/cache contexts, custom LlamaIndex models, Cohere, knowledge, or retriever pipelines | `sub-skills/contexts-and-retrievers/SKILL.md` |
| Launch or debug Gradio demos, Chrome extension server, `lavague-serve`, `AgentServer`, or `DriverServer` | `sub-skills/server-extension-gradio/SKILL.md` |
| Use `lavague-qa` or `lavague-test`, validate Gherkin features, generated pytest, or site config YAML | `sub-skills/qa-and-test-runner/SKILL.md` |
| Install/import/package split, telemetry, NLTK, setuptools, browser/API-key cross-cutting failures | `references/package-overview.md` and `references/troubleshooting.md` |

## Safe first step

From this `la-vague` skill root, run the shared probe before live browsing or provider calls:

```bash
python scripts/check_lavague_environment.py --check all --disable-telemetry
```

Then run the nearest sub-skill probe. These probes are safe by default: they check imports, signatures, CLI availability, env-var presence, or file shape. They do not launch browsers, contact providers, start servers, download data, or execute live websites unless a script option explicitly says it will.

## Install and import baseline

For the default user-facing stack:

```bash
pip install lavague
```

For narrower workflows, install only the packages you need, such as `lavague-core`, `lavague-drivers-selenium`, `lavague-drivers-playwright`, `lavague-contexts-openai`, `lavague-server`, `lavague-gradio`, `lavague-qa`, or `lavague-tests`. See [references/package-overview.md](references/package-overview.md) for the package split and console commands.

Minimal import check:

```python
from lavague.core import WorldModel, ActionEngine
from lavague.core.agents import WebAgent
from lavague.drivers.selenium import SeleniumDriver
```

Import success is not proof that browser binaries, provider credentials, UI dependencies, or target websites are ready.

## Live-run guardrails

Before any live LaVague run, confirm:

- The user authorizes browser automation on the target site.
- Provider credentials and token/cost implications are understood.
- Browser binaries or existing browser sessions are available.
- `LAVAGUE_TELEMETRY=NONE` is set if objectives, page content, generated code, screenshots, URLs, or errors could be sensitive.
- Persistent logging (`log_to_db=True`, `LocalLogger`, SQLite logs) is acceptable.
- Live examples that require public websites, model APIs, Gradio, or a Chrome extension are treated as optional and potentially flaky.

## Common entry snippets

Minimal WebAgent shape:

```python
from lavague.core import WorldModel, ActionEngine
from lavague.core.agents import WebAgent
from lavague.drivers.selenium import SeleniumDriver

driver = SeleniumDriver(headless=True)
agent = WebAgent(WorldModel(), ActionEngine(driver), n_steps=5)
agent.get("https://example.com")
result = agent.run("Summarize the visible page")
print(result.success, result.output)
```

Context-backed shape:

```python
from lavague.contexts.gemini import GeminiContext
from lavague.core import WorldModel, ActionEngine

context = GeminiContext()
world_model = WorldModel.from_context(context)
action_engine = ActionEngine.from_context(context, driver)
```

Chrome extension server help:

```bash
lavague-serve --help
```

QA input probe:

```bash
python sub-skills/qa-and-test-runner/scripts/lavague_qa_feature_probe.py --feature feature.feature --url https://example.test
```

## Provenance and refresh

Read [references/repo-provenance.md](references/repo-provenance.md) when checking whether this skill matches a current LaVague checkout. Refresh this skill if the LaVague commit, package versions, console entry points, or public API signatures changed.

## Non-goals

This skill is for operating the LaVague package. It does not cover front-end Chrome extension development, package publishing/release automation, or generic Selenium/Playwright/provider SDK usage when LaVague APIs are not involved.
