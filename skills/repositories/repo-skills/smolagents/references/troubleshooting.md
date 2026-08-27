# Cross-Cutting Troubleshooting

## Import or Install Fails

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: smolagents` | Package is not installed in the active Python. | Install `smolagents` in the environment that runs the agent or CLI. |
| `ModuleNotFoundError` for `openai`, `litellm`, `helium`, `docker`, `mcp`, `gradio`, `torch`, or provider SDKs | The relevant optional extra was not installed. | Install only the needed extra from `references/install-and-extras.md`. |
| `pip check` reports conflicts after adding extras | Broad extras or existing packages conflict. | Recreate a clean environment and install the narrow extra set needed by the selected workflow. |
| Local model loading fails before generation | Missing backend package, unsupported device, low memory, or model requires `trust_remote_code`. | Use `sub-skills/model-providers/references/troubleshooting.md` and validate config before loading. |

## Credentials and Provider Calls Fail

- Keep provider keys in environment variables or a secret store, not in code snippets or serialized artifacts.
- Confirm the selected wrapper matches the endpoint: `InferenceClientModel` for Hugging Face Inference Providers, `OpenAIModel` for OpenAI-compatible APIs, `LiteLLMModel` for LiteLLM routing, and provider-specific wrappers for Azure or Bedrock.
- Check `model_id`, `provider`, `api_base`, `base_url`, `api_key`/`token`, and token limits before debugging agent logic.
- Use `sub-skills/model-providers/scripts/check_model_config.py` for static config validation that does not call external APIs.

## Agent Output or Loop Behavior Is Wrong

- If a `CodeAgent` never returns, inspect whether the generated code called `final_answer(...)`; otherwise the loop continues until `max_steps`.
- If parsing fails, check whether model output contains valid Python code blocks or tool-call JSON for the selected agent type.
- If a managed agent is ignored or unavailable, ensure it has a unique `name` and clear `description`.
- If memory looks missing, distinguish `reset=True` default behavior from `reset=False` resume behavior.
- Use `sub-skills/agent-workflows/references/troubleshooting.md` for detailed run, planning, memory, callback, and serialization failures.

## Tool Validation Fails

- `@tool` functions need complete type hints, a return type, and an `Args:` docstring entry for every argument.
- `Tool` subclasses need `name`, `description`, `inputs`, `output_type`, and `forward`.
- Tool names must be unique within an agent toolbox and valid Python identifiers.
- Use `sub-skills/tools-and-integrations/scripts/validate_tool_schema.py` before wiring custom tools into live agents.

## Execution or Sandbox Fails

- Unauthorized imports are usually intentional safety behavior; add only the minimum module names to `additional_authorized_imports`.
- Docker, E2B, Modal, and Blaxel require their own extras and service/runtime setup.
- Do not switch from local to remote execution only to bypass validation; first decide what side effects, filesystem access, network access, dependencies, and credentials are acceptable.
- Use `sub-skills/execution-and-safety/references/troubleshooting.md` for executor-specific recovery.

## CLI or UI Fails

- Running `smolagent` with no positional prompt launches interactive setup; CI jobs should pass a prompt or invoke `--help`.
- `webagent` requires the `vision` extra and a working browser/WebDriver stack.
- Gradio UI requires the `gradio` extra and a model/tool setup that can run in the serving process.
- Use `sub-skills/cli-and-ui/scripts/print_cli_help.py` to check CLI help without launching live providers.
