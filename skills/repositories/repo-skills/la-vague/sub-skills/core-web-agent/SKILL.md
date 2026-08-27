---
name: core-web-agent
description: "Build, run, debug, and cost-check LaVague WebAgent workflows with
  WorldModel, ActionEngine, PythonEngine, logging, and safe dry-run scaffolds."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# LaVague core WebAgent workflows

Use this sub-skill when the task is to create, adapt, debug, or explain a LaVague `WebAgent` run loop: `WorldModel`, `ActionEngine`, `PythonEngine`, navigation controls, logging, token counting, and returned `ActionResult` handling.

## Route here for

- Building a minimal agent with `WorldModel`, `ActionEngine`, a browser driver, and `WebAgent`.
- Choosing between `agent.run(...)`, `agent.run_step(...)`, `agent.demo(...)`, or a dry-run template.
- Wiring custom LLM/embedding/multimodal objects after a context has been chosen.
- Interpreting `ActionResult.success`, `ActionResult.output`, generated code, logs, token/cost estimates, and debug node displays.
- Troubleshooting core-agent errors after browser and provider dependencies are already selected.

## Route elsewhere

- Selenium/Playwright binary, profile, iframe, tab, scroll, screenshot, and browser construction issues: use `../browser-drivers/SKILL.md`.
- OpenAI/Azure/Anthropic/Gemini/Fireworks contexts, cache contexts, Cohere, or custom retriever pipelines: use `../contexts-and-retrievers/SKILL.md`.
- Gradio demos, Chrome extension server, `AgentServer`, `DriverServer`, or `lavague-serve`: use `../server-extension-gradio/SKILL.md`.
- `lavague-qa` or `lavague-test` CLI workflows: use `../qa-and-test-runner/SKILL.md`.

## Start points

1. Read [references/workflows.md](references/workflows.md) for minimal, context-backed, step-by-step, and dry-run WebAgent recipes.
2. Read [references/api-reference.md](references/api-reference.md) for verified constructor signatures, method names, and return objects.
3. Read [references/logging-and-debugging.md](references/logging-and-debugging.md) when the user asks about token costs, logs, node inspection, SQLite logging, or step-by-step debugging.
4. Read [references/troubleshooting.md](references/troubleshooting.md) for missing API keys, telemetry warnings, NLTK/proxy warnings, `pkg_resources` failures, stale result/debug state, and core API misuse.
5. Run the safe helper from the `la-vague` skill root before spending browser or model-provider time:

```bash
python sub-skills/core-web-agent/scripts/lavague_minimal_agent.py --dry-run
```

The helper validates imports and prints a runnable template by default. It does **not** start a browser, contact a model provider, browse the web, or write logs unless `--run-live` is explicitly supplied.

## Minimal live shape

```python
from lavague.core import WorldModel, ActionEngine
from lavague.core.agents import WebAgent
from lavague.drivers.selenium import SeleniumDriver

# Requires browser support and the default model-provider credentials.
driver = SeleniumDriver(headless=True)
action_engine = ActionEngine(driver)
world_model = WorldModel()
agent = WebAgent(world_model, action_engine, n_steps=5)
agent.get("https://example.com")
result = agent.run("Summarize the visible page")
print(result.success, result.output)
```

Before running a live objective, confirm the matching browser route and provider-context route. The default LaVague stack uses OpenAI-backed models and embeddings, so `OPENAI_API_KEY` is normally required unless you pass a custom context/model stack.

## Core decisions

- Use `WorldModel.from_context(context)` and `ActionEngine.from_context(context, driver)` when a provider context owns the LLM, multimodal LLM, and embedding choices.
- Pass `llm=`, `embedding=`, `mm_llm=`, `retriever=`, or custom engines only when mixing components deliberately.
- Use `agent.run_step(objective)` for manual loops or debugging one instruction at a time.
- Use `agent.run(objective, display=True)` only when notebook/display output is useful and safe.
- Use `agent.run(..., log_to_db=True)` only when a local SQLite log file is acceptable.
- Use `agent.demo(...)` only after routing to the Gradio/server sub-skill because it imports `lavague-gradio` lazily.

## Validation checklist

- Python version is supported by the installed package set.
- `lavague.core`, the selected driver package, and selected context package import.
- Required model-provider environment variables are present but not printed.
- Browser binaries/profile/session requirements are satisfied.
- `LAVAGUE_TELEMETRY=NONE` is set if telemetry must be disabled.
- The objective contains no personal data that should not be sent to model providers or telemetry.
- Live work is explicitly permitted; otherwise stay in dry-run/template/probe mode.
