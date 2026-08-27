# Core WebAgent workflows

## Purpose

Use these recipes to build safe LaVague `WebAgent` workflows without reopening source examples. Every live workflow requires an installed driver package, a compatible browser runtime, and model-provider credentials unless you use a custom local/mock model stack.

## Safe dry-run first

From the `la-vague` skill root:

```bash
python sub-skills/core-web-agent/scripts/lavague_minimal_agent.py --dry-run
```

This prints import status and a runnable template. It does not start a browser or contact providers.

## Minimal Selenium agent

```python
from lavague.core import WorldModel, ActionEngine
from lavague.core.agents import WebAgent
from lavague.drivers.selenium import SeleniumDriver

driver = SeleniumDriver(headless=True)
action_engine = ActionEngine(driver)
world_model = WorldModel()
agent = WebAgent(world_model, action_engine, n_steps=5)
agent.get("https://example.com")
result = agent.run("Summarize the visible page")
print(result.success)
print(result.output)
```

Use this only after the browser driver route confirms that Selenium can construct a browser. The default model stack requires OpenAI-compatible credentials.

## Context-backed agent

Use a context when a task asks for a non-default provider or model set:

```python
from lavague.core import WorldModel, ActionEngine
from lavague.core.agents import WebAgent
from lavague.contexts.gemini import GeminiContext
from lavague.drivers.selenium import SeleniumDriver

context = GeminiContext()
driver = SeleniumDriver(headless=True)
world_model = WorldModel.from_context(context)
action_engine = ActionEngine.from_context(context, driver)
agent = WebAgent(world_model, action_engine)
```

Route provider-specific package and credential choices to `../contexts-and-retrievers/SKILL.md` before running.

## Custom models without a context

When the user already has LlamaIndex-compatible objects:

```python
world_model = WorldModel(mm_llm=my_multimodal_llm)
action_engine = ActionEngine(driver, llm=my_llm, embedding=my_embedding)
agent = WebAgent(world_model, action_engine)
```

Keep all three model roles straight:

- `mm_llm` plans with screenshots/current state in `WorldModel`.
- `llm` generates navigation/Python instructions and action code.
- `embedding` powers retrieval over page HTML when using semantic retrieval.

## Add user data and knowledge

Use `user_data` for per-run instructions or known facts:

```python
agent.run(
    "Fill the registration form",
    user_data={"email": "user@example.test", "plan": "trial"},
)
```

Use `WorldModel.add_knowledge(...)` for reusable background text that should influence planning across steps. Keep personal or secret data out of objectives, user data, logs, and telemetry unless the user explicitly permits it.

## Manual step loop

Use `run_step` when a task asks for step-by-step debugging:

```python
agent.prepare_run(display=False)
for _ in range(3):
    result = agent.run_step("Find the page title")
    if result is not None and result.success:
        break
```

If `run_step` returns `None`, it executed an action but has not completed the objective yet. Inspect logs/nodes before taking another step.

## Python Engine extraction pattern

The world model can route to the Python Engine when a page contains enough data and the task requires extraction/computation rather than another click. If the user asks for a direct Python-engine path, construct `PythonEngine(driver, ...)` only for lower-level debugging. Normal users should let `ActionEngine` own it.

## Gradio handoff

`agent.demo(...)` is a core `WebAgent` method, but it lazily imports `lavague-gradio` and launches an interactive UI. Use the server/Gradio route before running it:

```python
agent.demo("Go on the quicktour of PEFT")
```

Do not launch a Gradio UI in unattended verification.

## Live-run checklist

Before executing `agent.run(...)` on a real website:

1. Confirm the driver can construct or attach to a browser.
2. Confirm the page target is permitted and stable enough for automation.
3. Confirm model-provider credentials and expected cost.
4. Disable telemetry if required: `LAVAGUE_TELEMETRY=NONE`.
5. Use `headless=False` or an existing browser profile when manual login/CAPTCHA handling is needed.
6. Set a low `n_steps` during debugging to bound cost and browser actions.
7. Avoid placing personal data in objectives, user data, logs, or screenshots unless explicitly authorized.
