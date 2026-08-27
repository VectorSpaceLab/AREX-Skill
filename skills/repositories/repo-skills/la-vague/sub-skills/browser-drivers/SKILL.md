---
name: browser-drivers
description: "Select, configure, and troubleshoot LaVague Selenium and
  Playwright browser drivers safely."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# LaVague browser drivers

Use this sub-skill when the task is to choose or configure a LaVague browser driver, verify browser runtime availability, connect an existing browser/session, or diagnose Selenium/Playwright browser failures.

## Route here for

- Choosing `SeleniumDriver` versus `PlaywrightDriver` for a LaVague `ActionEngine` or `WebAgent`.
- Configuring `headless`, viewport size, `user_data_dir`, custom Selenium options, driver injection, or Playwright page factories.
- Diagnosing missing Chrome/Chromedriver, missing Playwright browser binaries, GUI/headless mismatches, tabs, iframes, scrolling, screenshots, or Browserbase remote Selenium setup.

## Route elsewhere

- `WorldModel`, `ActionEngine`, `WebAgent`, agent logging, token counting, and normal `agent.run()` patterns: route to `../core-web-agent/`.
- Provider contexts, OpenAI/Gemini/Anthropic/Fireworks credentials, embeddings, and retrievers: route to `../contexts-and-retrievers/`.
- Gradio, `agent.demo()`, Chrome extension server, websocket driver server, or `lavague-serve`: route to `../server-extension-gradio/`.
- QA generation or benchmark runner CLI behavior: route to `../qa-and-test-runner/`.

## Start points

1. Read [references/driver-reference.md](references/driver-reference.md) for constructor signatures, driver capabilities, and feature support boundaries.
2. Use [references/browser-workflows.md](references/browser-workflows.md) for copyable Selenium/Playwright setup patterns, existing-session recipes, iframe/tab/scan behavior, and Browserbase notes.
3. Use [references/troubleshooting.md](references/troubleshooting.md) when browser construction fails, Playwright binaries are missing, headless/headed behavior is wrong, or a page with CAPTCHAs/pop-ups/iframes/tabs stalls.
4. Run the safe probe before spending browser/API time:

```bash
python sub-skills/browser-drivers/scripts/lavague_driver_probe.py
```

The probe checks imports and local browser binary hints by default. It does **not** launch a browser unless `--construct` is provided.

## Driver choice in one minute

- Prefer `SeleniumDriver` for the widest LaVague feature coverage: default install path, iframes, multiple tabs, element highlighting, scrolling, dropdowns, custom Selenium options, and Browserbase remote connection.
- Use `PlaywrightDriver` only when the caller specifically wants Playwright or already has a Playwright page/context. Treat it as a smaller feature surface: do not promise Selenium feature parity, remote Browserbase support, or complete tab/headless-agent behavior without a local verification run.
- Both driver constructors create a browser/page immediately. If the task only asks whether the environment is ready, run the bundled probe without `--construct` first.

## Minimal usage patterns

Selenium default:

```python
from lavague.core import ActionEngine, WorldModel
from lavague.core.agents import WebAgent
from lavague.drivers.selenium import SeleniumDriver

driver = SeleniumDriver(headless=True)
action_engine = ActionEngine(driver)
agent = WebAgent(WorldModel(), action_engine)
# agent.get(url); agent.run(objective) belongs to the core-web-agent workflow.
```

Playwright selection:

```python
from lavague.core import ActionEngine
from lavague.drivers.playwright import PlaywrightDriver

driver = PlaywrightDriver(headless=True)
action_engine = ActionEngine(driver)
```

Existing Chrome session for CAPTCHA/login-heavy sites:

```python
from lavague.drivers.selenium import SeleniumDriver

driver = SeleniumDriver(headless=False, user_data_dir="/path/to/chrome-profile")
```

Do not hard-code profile paths or credentials in reusable scripts. Ask the caller for an explicit path at runtime.

## Safety defaults

- Default probes and recipes here avoid model provider calls, downloads, public-site navigation, persistent servers, and browser launch.
- `--construct` in the bundled probe is the explicit opt-in for browser launch. Passing `--url` may navigate to that URL; omit it for a blank-page construction check.
- Browser examples can still require GUI support, browser binaries, matching drivers, provider credentials, and network access when escalated into full agent execution.
