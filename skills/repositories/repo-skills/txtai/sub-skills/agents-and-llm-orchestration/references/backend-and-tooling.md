# Backend and Tooling Reference

This reference helps choose txtai LLM/Agent backends and configure tools without reopening source docs.

## Installation Extras

| Need | Install focus | Failure signal |
| --- | --- | --- |
| `Agent` with smolagents tools | `txtai[agent]` | `ImportError: smolagents is not available - install "agent" extra to enable` |
| LLM/RAG generation pipelines | `txtai[pipeline-llm]` or an environment with the chosen backend libraries | backend import errors for `litellm`, `llama_cpp`, `litert_lm`, `transformers`, or model loading |
| File extraction for RAG ingestion | `txtai[pipeline-data]` plus selected extraction backend | Textractor/backend import errors |
| API serving | API extras | FastAPI/uvicorn import or startup errors; route to deployment sub-skill |

Use the narrowest extra that matches the workflow. Avoid installing all extras unless the environment is disposable and broad optional dependencies are acceptable.

## Backend Inference Rules

`LLM(path=None, method=None, **kwargs)` delegates to a generation factory:

| Path/method | Backend | Notes |
| --- | --- | --- |
| `method="transformers"` or normal Hugging Face model path | Hugging Face Transformers | Default when no other method is inferred. Default path is `ibm-granite/granite-4.0-350m` when omitted. |
| path ending in `.gguf` or `method="llama.cpp"` | `llama-cpp-python` | Local GGUF file or Hub download. Supports `n_ctx`, `n_gpu_layers`, and llama.cpp kwargs. |
| provider-style API path recognized by LiteLLM or `method="litellm"` | LiteLLM | Requires `litellm` and provider credentials. Model names may be provider-prefixed. |
| path ending in `.litertlm` or `method="litert"` | LiteRT | Tries GPU backend, falls back to CPU. |
| path starting with `opencode` or `method="opencode"` | OpenCode HTTP service | Defaults to `http://localhost:4096`; requires a running OpenCode service. |
| custom `method="package.module.Class"` | Resolved custom generation implementation | Must accept `(path, **kwargs)` and implement generation behavior compatible with txtai. |

Pass `method=` explicitly when inference chooses the wrong backend or when a remote model string conflicts with a Hugging Face Hub path.

## Local Transformers Notes

```python
from txtai import LLM

llm = LLM(
    "Qwen/Qwen3-4B-Instruct-2507",
    gpu=False,
    task="language-generation",
)
```

- `gpu=True` is the default in many generation paths, but CPU-only environments can pass `gpu=False`.
- `quantize=True` may reduce memory for supported models, but can require extra libraries.
- `task` can force `language-generation`, `sequence-sequence`, or `vision` when model task detection is not enough.
- Chat models are formatted as chat messages automatically when `defaultrole="auto"` and the text does not start with a known instruction token.

## llama.cpp Notes

```python
llm = LLM(
    "./models/model.Q4_K_M.gguf",
    method="llama.cpp",
    n_ctx=8192,
    n_gpu_layers=0,
)
```

- Paths ending in `.gguf` infer llama.cpp.
- If `n_ctx` is omitted, txtai first tries `n_ctx=0` to use the model training context and falls back if memory is insufficient.
- `n_gpu_layers=-1` is the default when GPU/Metal is enabled; use `n_gpu_layers=0` for CPU.
- Use local files for deterministic environments; Hub downloads need network and cache space.

## LiteLLM/API Notes

```python
llm = LLM("gpt-4o-mini", method="litellm")
print(llm("Say hello", maxlength=64))
```

- Credentials such as API keys should be provided through environment variables or provider-specific secure configuration, not embedded in skill files or committed config.
- `maxlength` maps to provider `max_tokens`.
- LiteLLM model/provider detection only works when `litellm` is installed; otherwise method inference may fall back to Transformers.
- If a model name is also a valid Hugging Face Hub model, set `method="litellm"` to force hosted API behavior.

## Custom Generation Implementation

Use a custom generation class when inference must call a private runtime.

```python
llm = LLM("custom-model-name", method="mypackage.generation.CustomGeneration")
```

The custom class is resolved by txtai's resolver and receives `path` plus keyword arguments. It should behave like a generation backend and return text chunks/content compatible with `LLM`.

## Agent Model Configuration

Agent accepts `model=` or legacy `llm=`:

```python
from txtai import Agent, LLM

agent1 = Agent(model="Qwen/Qwen3-4B-Instruct-2507", tools=[], max_steps=1)
agent2 = Agent(llm="Qwen/Qwen3-4B-Instruct-2507", tools=[], max_iterations=1)
agent3 = Agent(model=LLM("Qwen/Qwen3-4B-Instruct-2507"), tools=[], max_steps=1)
agent4 = Agent(model={"path": "./model.gguf", "method": "llama.cpp", "n_ctx": 4096}, tools=[])
```

`max_iterations` is accepted for backward compatibility and is converted to `max_steps`.

## Tool Creation Matrix

| Tool config | Creates | Required fields |
| --- | --- | --- |
| callable function or callable instance | smolagents tool inferred from annotations/docstring | useful docstring and type hints |
| dict with `target` callable | function tool | `name`, `description`, `target`; add `inputs` when inference is weak |
| dict with `target` as `Embeddings` | embeddings search tool | `name`, `description`, `target` |
| dict with `path` or `container` | loaded embeddings search tool | `name`, `description`, plus `Embeddings.load` kwargs |
| string in built-in aliases | built-in tool | shortcut name |
| `defaults` | all default local/web tools | trusted execution environment |
| `http...` | MCP tools | reachable MCP server |
| `*.md` | skill Markdown tool | frontmatter `name` and `description` |

## Function Tool Schema Tips

Good direct callable:

```python
def search_ticket(query: str) -> list[dict]:
    """
    Searches support tickets.

    Args:
        query: support issue or ticket identifier

    Returns:
        matching support ticket dictionaries
    """
    return []
```

Explicit schema for unannotated callables:

```python
tool = {
    "name": "search_ticket",
    "description": "Searches support tickets by issue text or ticket id",
    "inputs": {
        "query": {"type": "string", "description": "issue text or ticket id"},
    },
    "output": "any",
    "target": search_ticket,
}
```

Avoid vague descriptions like "does lookup". Agents choose tools from descriptions, so include domain, input expectation, and return shape.

## Embeddings Tool Requirements

The built-in embeddings tool calls `search(query, 5)` and expects useful text in results. Prepare the index with content enabled:

```python
from txtai import Embeddings

embeddings = Embeddings(content=True)
embeddings.index([("id1", "tool-readable text")])
embeddings.save("./knowledge-index")
```

Then configure:

```python
{"name": "kb", "description": "Searches local knowledge base", "path": "./knowledge-index"}
```

For advanced SQL, hybrid scoring, graph, object fields, and save/load lifecycle, use `../embeddings-search/SKILL.md`.

## Built-In Tool Safety

- `bash`, `python`, `edit`, and `write` can mutate the environment; expose them only in trusted sandboxes.
- `websearch`, `webview`, and HTTP/MCP tools require network access and may fail under firewall/proxy restrictions.
- `read` can read files and URLs and uses text extraction; enforce path allowlists in sensitive applications.
- `defaults` is convenient for local coding agents but too broad for untrusted users.

## Application/YAML Tool Resolution

```yaml
llm:
  path: Qwen/Qwen3-4B-Instruct-2507

agent:
  researcher:
    method: tool
    max_steps: 5
    tools:
      - websearch
      - name: summarize_ticket
        description: Summarizes a support ticket
        target: mypackage.tools.summarize_ticket
```

`Application` resolves `target` by first checking configured pipelines, then configured workflows, then importing a callable path. This makes it possible to expose configured txtai components as agent tools.
