---
name: smolagents
description: "Build, debug, and operate Hugging Face smolagents agents, tools,
  model providers, secure executors, CLIs, and UI workflows with self-contained
  references and helpers."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# smolagents

Use this skill when working with Hugging Face `smolagents`: code-writing agents, tool-calling agents, custom tools, model provider wrappers, secure Python execution, command-line entry points, or Gradio/browser UI workflows.

## Quick Start

Install only the extras needed for the route you are using:

```bash
pip install smolagents
pip install "smolagents[toolkit]"   # web search and webpage tools
pip install "smolagents[openai]"    # OpenAI-compatible client support
pip install "smolagents[litellm]"   # LiteLLM provider routing
pip install "smolagents[gradio]"    # Gradio UI helpers
pip install "smolagents[vision]"    # webagent browser automation stack
```

Minimal import and agent shape:

```python
from smolagents import CodeAgent, InferenceClientModel

model = InferenceClientModel()
agent = CodeAgent(tools=[], model=model)
result = agent.run("Summarize the task and return final_answer.")
```

## Route by Task

- Use `sub-skills/agent-workflows/SKILL.md` for `CodeAgent`, `ToolCallingAgent`, `MultiStepAgent`, planning, memory, callbacks, managed agents, serialization, streaming, final-answer checks, and run debugging.
- Use `sub-skills/tools-and-integrations/SKILL.md` for `Tool` subclasses, `@tool`, schemas, validation, built-in tools, Hub/Space/LangChain/MCP integrations, and tool troubleshooting.
- Use `sub-skills/model-providers/SKILL.md` for `InferenceClientModel`, `LiteLLMModel`, `OpenAIModel`, Azure, Bedrock, Transformers, MLX, vLLM, custom `Model` subclasses, credentials, and provider-specific errors.
- Use `sub-skills/execution-and-safety/SKILL.md` for `executor_type`, `LocalPythonExecutor`, authorized imports, `PythonInterpreterTool`, Docker/E2B/Modal/Blaxel execution, sandboxing, and secure-code troubleshooting.
- Use `sub-skills/cli-and-ui/SKILL.md` for `smolagent`, `webagent`, interactive mode, CLI model/tool flags, `GradioUI`, `launch_gradio_demo`, server patterns, and browser UI failures.

## Common Decisions

- Prefer `CodeAgent` when the model should write Python actions and maintain state through a Python executor.
- Prefer `ToolCallingAgent` when the model natively emits tool calls and you need structured tool invocation or parallel tool calls.
- Start with hosted `InferenceClientModel` for the smallest setup; switch to `OpenAIModel`, `LiteLLMModel`, or local wrappers only when the deployment requires it.
- Keep `additional_authorized_imports` narrow; route broad filesystem, network, browser, or service tasks through the execution-and-safety guidance before enabling imports or remote executors.
- Validate tools and model configuration locally before running live providers, browsers, Hub operations, or remote executors.

## Shared References

- Read `references/install-and-extras.md` for package extras, optional dependencies, CLI availability, and verification commands.
- Read `references/troubleshooting.md` for cross-cutting install/import, credential, optional dependency, CLI/API misuse, and workflow-routing failures.
- Read `references/repo-provenance.md` when deciding whether this skill is stale relative to a newer smolagents checkout.

## Shared Scripts

- Run `python scripts/smoke_smolagents_install.py --help` to see the safe checks.
- Run `python scripts/smoke_smolagents_install.py` after installation to verify import metadata, core constructors, and `smolagent --help` without calling external providers.
- Add `--check-webagent` only when the `vision` extra is expected; failure usually means `helium`/browser dependencies are missing.

## Guardrails

- Do not hardcode API keys in examples, serialized tools, CLI invocations, or config files; read them from environment variables or secret managers.
- Do not install `smolagents[all]` by default; choose the narrow extra for the selected provider, tool, UI, or executor.
- Do not instruct users to run original repository examples or tests from this skill. Use the bundled references and scripts here as the reusable runtime source.
- Treat network, browser automation, remote sandboxes, Hub pushes, and model calls as opt-in operations requiring credentials, services, or optional packages.
