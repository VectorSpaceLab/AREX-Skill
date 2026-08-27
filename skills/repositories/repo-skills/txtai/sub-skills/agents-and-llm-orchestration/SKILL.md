---
name: agents-and-llm-orchestration
description: "Build txtai LLM, RAG, and Agent workflows with backend selection,
  tools, templates, teams, and troubleshooting guidance."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Agents and LLM Orchestration

Use this sub-skill when the task is to connect txtai generation, retrieval, and agentic tool use. It covers `LLM`, `RAG`, and `Agent` construction, YAML configuration, tool definitions, prompt templates, agent teams, backend selection, and optional dependency troubleshooting.

For low-level embeddings store creation and query tuning, route to [embeddings-search](../embeddings-search/SKILL.md). For deterministic pipeline/workflow task chains, route to [pipelines-and-workflows](../pipelines-and-workflows/SKILL.md). For serving agents/RAG over API, OpenAI-compatible endpoints, or hosted app deployment, route to [api-and-deployment](../api-and-deployment/SKILL.md).

## Quick Routing

| User goal | Use |
| --- | --- |
| Generate text directly | `LLM(path=None, method=None, **kwargs)` |
| Answer with retrieved context | `RAG(similarity, path, template=..., context=..., output=...)` |
| Let a model choose tools over multiple steps | `Agent(model=..., tools=[...], max_steps=...)` |
| Build multi-agent research/delegation | Agents as tool targets inside another `Agent` |
| Define via YAML/Application | top-level `llm:`, `rag:`, and `agent:` sections |
| Validate RAG config safely | `python scripts/rag_config_template.py --write-template rag_template.py` |

## Minimal Import Check

```python
from txtai import Agent, Embeddings, LLM, RAG

print(LLM)
print(RAG)
print(Agent)
```

If constructing `Agent(...)` raises `ImportError: smolagents is not available - install "agent" extra to enable`, install an agent-capable environment such as `pip install "txtai[agent]"`. If LLM backends fail, see [backend-and-tooling](references/backend-and-tooling.md).

## Direct LLM Pattern

```python
from txtai import LLM

llm = LLM("ibm-granite/granite-4.0-350m")
answer = llm("Summarize retrieval augmented generation", maxlength=256)
```

`LLM` accepts a model `path`, optional `method`, and backend keyword arguments. It supports strings, lists of strings, chat-message dictionaries with `role` and `content`, streaming via `stream=True`, `stop` strings, `defaultrole`, and `stripthink` cleanup. Use `method="transformers"`, `method="llama.cpp"`, `method="litellm"`, or a custom generation class path when inference cannot be inferred from the model path.

## RAG Pattern

```python
from txtai import Embeddings, RAG

embeddings = Embeddings(content=True)
embeddings.index([
    ("install", "txtai supports semantic search, RAG, agents, workflows and APIs"),
    ("agent", "txtai agents use tools such as Python functions, embeddings stores and web search"),
])

template = """
Answer using only the context.
Question: {question}
Context: {context}
"""

rag = RAG(
    embeddings,
    "ibm-granite/granite-4.0-350m",
    template=template,
    system="You answer from retrieved context.",
    context=3,
    output="flatten",
)

result = rag("What can txtai agents use?", maxlength=256)
```

`RAG` joins a similarity source with a generator or question-answering pipeline. The similarity source can be an `Embeddings` instance, a `Similarity` pipeline, a callable batch searcher, or an Application-provided embeddings index. Build and persist retrieval stores with [embeddings-search](../embeddings-search/SKILL.md) before focusing on prompt generation here.

## Agent Pattern

```python
from datetime import datetime
from txtai import Agent

def today() -> str:
    """
    Gets the current date.

    Returns:
        current date in ISO format
    """
    return datetime.today().isoformat()

agent = Agent(
    model="Qwen/Qwen3-4B-Instruct-2507",
    tools=[today, "websearch"],
    max_steps=5,
)

answer = agent("What is today's date and why might it matter for a news search?", maxlength=2048)
```

Use agents for multi-step questions where tool choice matters. Prefer plain `RAG` or deterministic workflows for simple, repeatable flows.

## Tool Shapes

- Direct Python callable: add the function or callable instance to `tools`; type hints and Google-style docstrings improve generated tool schemas.
- Explicit function dictionary: `{"name": "lookup", "description": "...", "inputs": {...}, "target": callable}`.
- Embeddings dictionary: `{"name": "kb", "description": "Searches the knowledge base", "path": "index-path"}` or `{"target": embeddings}`; results are lists of dicts with `id`, `text`, and `score` when content is available.
- Built-in shortcuts: `bash`, `defaults`, `edit`, `glob`, `grep`, `python`, `read`, `todowrite`, `websearch`, `webview`, and `write`.
- MCP tools: HTTP strings such as `http://localhost:8000/mcp` load a Model Context Protocol tool collection.
- Skill files: strings ending in `.md` load a `skill.md`-style tool with frontmatter `name` and `description`.

## Agent Teams

Agents can be tool targets for a supervisor agent.

```python
from txtai import Agent, LLM

llm = LLM("Qwen/Qwen3-4B-Instruct-2507")
websearcher = Agent(model=llm, tools=["websearch"], max_steps=3)

supervisor = Agent(
    model=llm,
    tools=[{
        "name": "websearcher",
        "description": "Searches the web and returns concise findings",
        "target": websearcher,
    }],
    max_steps=6,
)
```

Share a single `LLM` instance when team members should use the same backend configuration. Keep each agent tool description narrow so the supervisor can choose correctly.

## YAML/Application Pattern

```yaml
llm:
  path: Qwen/Qwen3-4B-Instruct-2507

agent:
  researcher:
    max_steps: 5
    tools:
      - websearch
      - name: today
        description: Gets the current date
        target: package.module.today

rag:
  path: ibm-granite/granite-4.0-350m
  template: |
    Answer using only the context.
    Question: {question}
    Context: {context}
  output: flatten
  context: 3
```

`Application(config)` resolves configured pipelines first, then agents, then embeddings. A configured `rag:` pipeline can receive the Application embeddings index when its `similarity` is omitted. In `agent:` sections, `target` values are resolved as configured pipelines, workflows, or importable callables.

## RAG Output Modes

| `output` | Shape |
| --- | --- |
| `default` | `(name, answer)` tuples, or dicts with `answer` for dict/string inputs |
| `flatten` | answer strings only |
| `reference` | `(name, answer, reference)` tuples or dicts with references |

RAG input can be a string, a list of strings, tuples shaped like `(name, query, question, snippet)`, or dict rows with `name`, `query`, `question`, and `snippet`. Use `output="flatten"` for simple chat answers and `output="reference"` when the caller needs source ids from retrieved context.

## References

- [LLM, RAG, and Agent recipes](references/llm-rag-agent-recipes.md) for concrete Python and YAML patterns.
- [Backend and tooling](references/backend-and-tooling.md) for extras, credentials, backends, and tool schemas.
- [Troubleshooting](references/troubleshooting.md) for placeholder agents, template bugs, retrieval quality, output shapes, web/network failures, and CPU/GPU issues.

## Validation Checklist

- Confirm imports and constructor signatures for `LLM`, `RAG`, and `Agent` in the target environment.
- For RAG, ensure the retrieval store is content-enabled and the prompt template includes both `{question}` and `{context}`.
- For agents, verify optional extras by instantiating a tiny `Agent(model=..., tools=[], max_steps=1)` or by importing `smolagents` directly.
- For hosted LLMs, verify credentials outside source files and run a one-prompt smoke test before wiring tools.
- Keep source repository docs, examples, and absolute checkout paths out of generated runtime content.
