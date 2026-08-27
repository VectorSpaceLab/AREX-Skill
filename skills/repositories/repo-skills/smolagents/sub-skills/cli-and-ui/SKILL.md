---
name: cli-and-ui
description: "Use smolagents command-line entry points, browser automation CLI,
  Gradio UI helpers, and lightweight web-server patterns. Use when a task
  mentions smolagent, webagent, interactive CLI mode, CLI flags, GradioUI,
  launch_gradio_demo, browser agent demos, or serving a smolagents chat UI."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# CLI And UI

Use this sub-skill when the user wants to run smolagents from a terminal or expose an already-designed agent through a local UI/server.

## Route First

- For agent construction, `CodeAgent` vs `ToolCallingAgent`, model objects, managed agents, and tool definitions, route to the sibling agent/model/tool sub-skills.
- For sandbox executors, remote execution backends, import allow-lists, and security hardening beyond the CLI `--imports` flag, route to `execution-and-safety`.
- For this sub-skill, focus on command syntax, UI wrapping, optional extras, browser/UI dependencies, and troubleshooting terminal or serving failures.

## Core Entry Points

- `smolagent` is the general CLI for running a `CodeAgent` or `ToolCallingAgent` from a prompt or an interactive setup wizard.
- `webagent` is a specialized browser-automation CLI that starts a Selenium/Helium Chrome session and runs a vision-capable `CodeAgent` with screenshot callbacks.
- `GradioUI` wraps a `MultiStepAgent` in a streaming Gradio chat interface with optional multimodal file upload.
- `launch_gradio_demo(tool)` launches a Gradio `Interface` for a single `Tool` whose `inputs` and `output_type` are defined; use `GradioUI` for full agent chat UIs.
- Server examples are adaptation patterns: run the blocking `agent.run(...)` call off the async event loop and disconnect external tool clients during shutdown.

## Safe Discovery

Before running model-backed tasks, use safe help checks:

```bash
python sub-skills/cli-and-ui/scripts/print_cli_help.py --command smolagent
python sub-skills/cli-and-ui/scripts/print_cli_help.py --command webagent
smolagent --help
webagent --help
```

If console scripts are unavailable but the package imports, try module-level help:

```bash
python -m smolagents.cli --help
python -m smolagents.vision_web_browser --help
```

## Common Workflows

- Run a direct CLI prompt with `smolagent "your task" --model-type InferenceClientModel --model-id Qwen/Qwen3-Next-80B-A3B-Thinking --tools web_search`.
- Start the guided wizard with bare `smolagent`; it prompts for action type, tools, model settings, optional API fields, additional imports, and final task.
- Use `--action-type code` for a code-writing `CodeAgent`; use `--action-type tool_calling` for a `ToolCallingAgent`.
- Use `webagent "browser task" --model-type LiteLLMModel --model-id gpt-4o` only when browser, model, and optional vision dependencies are installed and a Chrome/WebDriver stack is usable.
- Wrap a configured agent with `GradioUI(agent, file_upload_folder="uploads", reset_agent_memory=True).launch(share=False)` for a local chat UI.

## References

- See [CLI reference](references/cli-reference.md) for command names, flags, defaults, and behavior.
- See [UI workflows](references/ui-workflows.md) for `GradioUI`, streaming, file upload, server adaptation, and monitoring notes.
- See [troubleshooting](references/troubleshooting.md) for missing scripts, optional extras, invalid model/tool flags, and browser failures.
