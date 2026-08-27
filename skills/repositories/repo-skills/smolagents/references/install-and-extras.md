# Install and Extras

## Base Package

Use the base package for core agent classes, prompts, memory, local execution, serialization, and hosted Hugging Face inference clients:

```bash
pip install smolagents
python - <<'PY'
import smolagents
from smolagents import CodeAgent, ToolCallingAgent, InferenceClientModel, Tool
print(smolagents.__version__)
PY
```

The package requires Python 3.10 or newer. The verified package metadata for this skill identified version `1.27.0.dev0` and console scripts `smolagent` and `webagent`.

## Optional Extras

Install the smallest extra that matches the selected workflow:

| Extra | Use when | Typical surfaces |
| --- | --- | --- |
| `toolkit` | Web search or webpage-reading built-in tools are required. | `DuckDuckGoSearchTool`, `VisitWebpageTool` |
| `openai` | OpenAI-compatible APIs are used through the OpenAI client. | `OpenAIModel`, Azure/OpenAI-compatible endpoints |
| `litellm` | LiteLLM provider routing is needed. | `LiteLLMModel`, `LiteLLMRouterModel` |
| `transformers` | Local Transformers models are loaded. | `TransformersModel`, `torch`, `accelerate` |
| `vllm` | Local or server-backed vLLM workflows are needed. | `VLLMModel`, GPU-backed inference |
| `mlx-lm` | Apple MLX local inference is needed. | `MLXModel` |
| `bedrock` | Amazon Bedrock models are used. | `AmazonBedrockModel` |
| `gradio` | Gradio chat/demo UI is launched. | `GradioUI`, `launch_gradio_demo` |
| `vision` | Browser automation through `webagent` is used. | `vision_web_browser`, `helium`, `selenium` |
| `mcp` | MCP server tools are imported. | `ToolCollection.from_mcp` |
| `docker`, `e2b`, `modal`, `blaxel` | A remote or sandboxed executor is selected. | `executor_type` and remote executor classes |
| `telemetry` | OpenTelemetry/Phoenix instrumentation is enabled. | monitoring/instrumentation integrations |

Avoid `smolagents[all]` unless you intentionally need many integrations in one environment. It brings in provider, UI, executor, and local-model stacks that are unrelated to many tasks.

## Safe Verification

After installation, run the bundled smoke check:

```bash
python scripts/smoke_smolagents_install.py
```

This verifies package import, distribution metadata, public constructors, and `smolagent --help` without calling model providers or network services.

When browser automation is part of the task, verify the optional browser entry point separately:

```bash
python scripts/smoke_smolagents_install.py --check-webagent
```

If `webagent` fails with an import error such as missing `helium`, install `smolagents[vision]` and confirm the browser/WebDriver stack required by your platform.

## CLI Entry Points

- `smolagent` runs a configurable agent from a prompt or launches interactive setup when no prompt is provided.
- `webagent` runs a browser-oriented agent and requires the vision/browser automation dependencies.

Use `sub-skills/cli-and-ui/SKILL.md` for flags and UI workflows.
