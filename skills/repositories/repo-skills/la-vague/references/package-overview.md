# LaVague package overview

## Purpose

Read this when you need the package split, install choices, public entry points, and safe validation sequence for LaVague. Use sub-skills for workflow depth.

## What LaVague is

LaVague is a Large Action Model / AI web-agent framework. Its core loop combines:

- A `WorldModel` that turns an objective plus current web state into the next instruction.
- An `ActionEngine` that translates navigation instructions into browser actions or Python extraction steps.
- A browser `BaseDriver` implementation such as Selenium or Playwright.
- Optional provider contexts, retrievers, logging/token counting, Gradio UI, Chrome extension server, and QA tooling.

## Distribution split

| Distribution | Import surface | Main use |
| --- | --- | --- |
| `lavague` | `lavague` namespace bundle | Meta-package that installs the default core/Selenium/OpenAI/Gradio stack. |
| `lavague-core` | `lavague.core` | `WorldModel`, `ActionEngine`, `WebAgent`, engines, retrievers, logging, token counting, utilities. |
| `lavague-drivers-selenium` | `lavague.drivers.selenium` | Selenium browser driver. |
| `lavague-drivers-playwright` | `lavague.drivers.playwright` | Playwright browser driver. |
| `lavague-contexts-openai` | `lavague.contexts.openai` | OpenAI and Azure OpenAI contexts. |
| `lavague-contexts-anthropic` | `lavague.contexts.anthropic` | Anthropic context, with OpenAI embedding/default fallback requirements. |
| `lavague-contexts-gemini` | `lavague.contexts.gemini` | Gemini context. |
| `lavague-contexts-fireworks` | `lavague.contexts.fireworks` | Fireworks context, with OpenAI multimodal/default fallback requirements. |
| `lavague-contexts-cache` | `lavague.contexts.cache` | Cache/mock context and prompt stores for repeatable testing/probes. |
| `lavague-retriever-cohere` | `lavague.retrievers.cohere` | Cohere reranking retriever. |
| `lavague-gradio` | `lavague.gradio` | `WebAgent.demo()` UI backend. |
| `lavague-server` | `lavague.server` | Chrome extension backend, `AgentServer`, `DriverServer`, `lavague-serve`. |
| `lavague-qa` | `lavague.qa` | `lavague-qa` Gherkin-to-pytest generation. |
| `lavague-tests` | `lavague.tests` | `lavague-test` benchmark/static-site runner. |

## Install patterns

For a normal default user workflow:

```bash
pip install lavague
```

For narrower or advanced workflows:

```bash
pip install lavague-core lavague-drivers-selenium lavague-contexts-openai
pip install lavague-drivers-playwright
pip install lavague-contexts-gemini lavague-contexts-anthropic lavague-contexts-fireworks
pip install lavague-server lavague-gradio lavague-qa lavague-tests
```

Use Python 3.10+; some provider integrations in this snapshot constrain Python below 3.12, so Python 3.10 is the safest cross-package target.

## Minimal import check

```bash
python scripts/check_lavague_environment.py --check all
```

Or directly:

```python
from lavague.core import WorldModel, ActionEngine
from lavague.core.agents import WebAgent
from lavague.drivers.selenium import SeleniumDriver
```

Import success does not prove browser binaries, provider credentials, or live website automation are ready. Run the appropriate sub-skill probe before live work.

## Console entry points

| Command | Owning sub-skill | Purpose |
| --- | --- | --- |
| `lavague-serve` | `server-extension-gradio` | Start the Chrome extension/WebSocket agent server; safe check is `lavague-serve --help`. |
| `lavague-qa` | `qa-and-test-runner` | Generate pytest-bdd tests from a Gherkin feature and URL. |
| `lavague-test` | `qa-and-test-runner` | Run LaVague benchmark-style site configs. |

## Optional live requirements

- Default provider: normally `OPENAI_API_KEY`.
- Other contexts: relevant provider keys such as Azure/OpenAI deployment settings, Anthropic, Gemini/Google, Fireworks, or Cohere.
- Browser automation: Chrome/Chromedriver for Selenium or Playwright browser binaries for Playwright.
- Network: target websites and provider APIs.
- UI/server: local ports, browser extension or Gradio browser session.
- Privacy: page text, screenshots, objectives, generated action code, errors, and logs may contain sensitive data.

## Safe order for future agents

1. Identify the workflow and route to the sub-skill.
2. Run the nearest bundled probe in dry-run/default mode.
3. Confirm browser/provider/network/credential/telemetry requirements.
4. Only then execute live browser or model-provider work.
5. Keep generated code/templates and logs local unless the user permits sharing.
