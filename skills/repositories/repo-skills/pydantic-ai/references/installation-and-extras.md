# Installation and Extras

Use this reference when deciding which Pydantic AI package, optional extra, or import check belongs to a task.

## Package Map

| Distribution | Import root | Purpose |
| --- | --- | --- |
| `pydantic-ai` | `pydantic_ai` | Umbrella package that depends on `pydantic-ai-slim` with many common provider/integration extras. Good for full application installs. |
| `pydantic-ai-slim` | `pydantic_ai` | Core agent framework with optional extras for providers, tools, CLI, MCP, evals, UI, durable execution, and integrations. Good for minimal installs. |
| `pydantic-graph` | `pydantic_graph` | Type-hint based graph/state-machine library used by agents and available standalone. |
| `pydantic-evals` | `pydantic_evals` | Code-first evaluation framework for stochastic functions, LLMs, and agents. |
| `clai` | `clai` | Command-line chat and web UI package for Pydantic AI agents. |
| `pydantic-ai-examples` | `pydantic_ai_examples` | Installable examples package; many examples require provider credentials or extra services. |

All workspace packages declare Python `>=3.10`.

## Minimal Installs

For broad application use:

```bash
pip install pydantic-ai
```

For a small dependency footprint, start with the slim package and add extras only when needed:

```bash
pip install pydantic-ai-slim
pip install pydantic-graph pydantic-evals clai
```

For development inside a checkout, use the repository's documented `uv`/`make` workflow rather than copying editable-install commands from this skill. Route repository setup and validation to `../sub-skills/repo-development/SKILL.md`.

## Extra Selection

| Need | Typical extra or package | Route |
| --- | --- | --- |
| OpenAI-compatible or vendor model SDKs | Provider extras such as `openai`, `anthropic`, `google`, `groq`, `mistral`, `cohere`, `bedrock`, `huggingface`, `xai`, `openrouter`, `vertexai` | `../sub-skills/models-and-providers/SKILL.md` |
| CLI entry point | `pydantic-ai-slim[cli]` or `clai` | `../sub-skills/cli-and-apps/SKILL.md` |
| MCP client/toolsets | `pydantic-ai-slim[mcp]` or `pydantic-ai-slim[fastmcp]` | `../sub-skills/mcp-and-integrations/SKILL.md` |
| Evals integration from Pydantic AI | `pydantic-ai-slim[evals]` plus `pydantic-evals` | `../sub-skills/evals-and-graph/SKILL.md` |
| AG-UI or Starlette UI adapters | `pydantic-ai-slim[ag-ui]`, `pydantic-ai-slim[ui]`, or `pydantic-ai-slim[web]` | `../sub-skills/mcp-and-integrations/SKILL.md` and `../sub-skills/cli-and-apps/SKILL.md` |
| Durable execution | `pydantic-ai-slim[temporal]`, `[dbos]`, or `[prefect]` | `../sub-skills/mcp-and-integrations/SKILL.md` |
| Retry helpers | `pydantic-ai-slim[retries]` | `../sub-skills/agent-core/SKILL.md` |
| YAML/JSON agent specs | `pydantic-ai-slim[spec]` | `../sub-skills/agent-core/SKILL.md` |
| Embeddings or search/common tools | Provider/tool-specific extras such as `sentence-transformers`, `voyageai`, `duckduckgo`, `tavily`, `exa`, `web-fetch` | `../sub-skills/models-and-providers/SKILL.md` |

Avoid installing every provider/backend extra unless the task explicitly needs broad provider coverage. Some extras imply cloud SDKs, large model packages, GPU runtimes, or credentials.

## Safe Import Check

```python
import pydantic_ai
import pydantic_graph
import pydantic_evals
import clai
from pydantic_ai import Agent
from pydantic_ai.models.test import TestModel

agent = Agent(TestModel(), instructions='Reply with success.')
result = agent.run_sync('hello')
print(result.output)
```

For a command-line diagnostic that does not call providers, run `python scripts/check_environment.py` from the root of this skill.

## Optional Dependency Rule

When a model/provider/tool import fails, do not guess the broad install command. Route to `../sub-skills/models-and-providers/SKILL.md`, identify the model string or feature, choose the smallest matching extra, and list required environment variables or service credentials separately from package installation.
