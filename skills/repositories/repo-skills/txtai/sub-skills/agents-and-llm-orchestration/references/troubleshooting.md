# Agents, LLM, and RAG Troubleshooting

Use this guide to diagnose txtai orchestration failures without reopening the source repository.

## Agent Placeholder or Missing `smolagents`

Signal:

```text
ImportError: smolagents is not available - install "agent" extra to enable
```

Why it happens:

- `txtai.agent.__init__` falls back to a placeholder `Agent` when agent dependencies are missing.
- Importing `Agent` can succeed, but constructing `Agent(...)` raises.

Checks:

```python
from txtai import Agent
try:
    Agent(model="hf-internal-testing/tiny-random-LlamaForCausalLM", tools=[], max_steps=1)
except ImportError as exc:
    print(exc)
```

Fix:

- Install the focused extra: `pip install "txtai[agent]"`.
- Confirm `import smolagents` works in the same Python environment.
- If the project uses lockfiles or containers, add the agent extra there rather than installing ad hoc in production.

## Missing LLM Backend Extras

Signals:

- `ImportError: LiteLLM is not available - install "pipeline" extra to enable`.
- `ImportError: llama.cpp is not available - install "pipeline" extra to enable`.
- Import errors for `litellm`, `llama_cpp`, `litert_lm`, `transformers`, `torch`, or tokenizer/model libraries.

Fix:

- Install `txtai[pipeline-llm]` or the exact backend dependency set required by the selected method.
- Pass `method=` explicitly if auto-detection chooses the wrong backend.
- For API models, verify provider credentials and use a one-prompt `LLM(...)("ping")` smoke test before adding tools.
- For local models, pass `gpu=False` in CPU-only environments.

## Hosted API Credentials

Signals:

- 401/403 responses from provider APIs.
- Provider-specific "missing API key" errors.
- LiteLLM cannot infer provider from the model string.

Fix:

- Set credentials through environment variables or the provider's secure config mechanism.
- Do not put API keys in YAML committed to a repository or in generated skill content.
- Use provider-prefixed model names when needed, or force `method="litellm"`.
- Check quota/rate-limit errors separately from authentication errors.

## Local Model Downloads and Cache Problems

Signals:

- Long first run, download timeout, offline failure, disk quota errors, or Hugging Face authorization failures.
- GGUF path downloads unexpectedly instead of reading a local file.

Fix:

- Prefer local model paths for deterministic deployments.
- Pre-download required models in build steps when network access is restricted.
- Use smaller models for smoke tests.
- Verify private model access with the correct token outside source files.
- For `.gguf`, confirm the path exists before constructing `LLM`; otherwise txtai may try to download from a model hub.

## Context Length or Truncation

Signals:

- Agent loses tool outputs or previous steps.
- RAG ignores late context or returns incomplete answers.
- Backend complains about token/context limits.

Fix:

- Increase call-time `maxlength` for generated output when safe.
- Reduce `RAG(context=...)`, chunk sizes, or retrieved row verbosity.
- For llama.cpp, set `n_ctx` deliberately.
- For agents, lower `max_steps`, narrow tools, or summarize tool outputs.
- Use `memory=` only when conversation history is needed; reset sessions with `reset=True` to avoid stale context.

## RAG Template Ignores Context

Signals:

- Retrieval returns relevant rows, but generated answer acts as if no context exists.
- The prompt template contains `{question}` but not `{context}`.
- `output="default"` returns tuples/dicts and downstream code reads the wrong field.

Checks:

```python
template = "Answer: {question}"
assert "{context}" in template and "{question}" in template
```

Fix:

- Include both `{question}` and `{context}` in `template`.
- If using `system=`, include `{context}` there only when the system message should carry retrieved evidence; otherwise keep context in the user prompt.
- Use `output="flatten"` when downstream code expects answer strings only.
- Use `output="reference"` when source ids are needed.

## RAG Retrieval Quality

Signals:

- Context is empty or irrelevant.
- RAG produces generic answers despite a template that includes `{context}`.
- Required terms are missing or filtered rows are too short.

Fix:

- Ensure the embeddings index is built with `content=True` so retrieved rows contain text.
- Inspect raw retrieval before generation: `embeddings.search(query, 5)` or `rag.query([query], texts=None)`.
- Increase `context` to include more retrieved matches.
- Lower `minscore` if relevant rows are filtered out.
- Lower `mintokens` if useful short facts are filtered out.
- Improve chunking and metadata filters in the retrieval store; use `../embeddings-search/SKILL.md` for index/query work.
- Separate retrieval `query` from final `question` with dict/tuple RAG inputs when the user wording is verbose.

## RAG Output Shape Confusion

Signals:

- Code expects a string but receives `("name", "answer")`.
- Code expects references but only receives answers.
- Single input returns one item while list input returns a list.

Fix:

- Set `output="flatten"` for answer strings.
- Set `output="reference"` for source references.
- Normalize caller handling for single input vs list input.
- For dict inputs, read the `answer` field; for `reference` mode also read `reference`.

## Web Tool and Network Failures

Signals:

- `websearch` returns no results, times out, or raises provider/network errors.
- `webview`/`read` cannot access a URL or extracted page text is empty.
- MCP HTTP tool collection cannot connect.

Fix:

- Verify network access, proxy settings, DNS, and firewall rules.
- Add non-web fallback tools for critical workflows.
- Narrow the prompt so the agent knows when web access is optional.
- For MCP, confirm the server URL is reachable and returns the expected tool collection.
- Avoid exposing web/file tools to untrusted users without sandboxing.

## Agent Tool Schema Problems

Signals:

- The model calls a tool with wrong arguments.
- Tool is present but never selected.
- Tool creation fails around type hints or docstring parsing.

Fix:

- Add explicit `inputs` with clear types and descriptions.
- Use Google-style docstrings with `Args:` and `Returns:` for direct callables.
- Keep tool names short and unique.
- Make descriptions outcome-oriented: domain, when to call, input, and return shape.
- Patch ambiguous tools into explicit dictionaries instead of relying on inference.

## Agent Loops or Wrong Tool Choice

Signals:

- Agent repeats the same tool call.
- Agent reaches `max_steps` before a final answer.
- Agent chooses broad tools such as web search instead of a local knowledge base.

Fix:

- Reduce tool count and split large toolkits into agent teams.
- Make local knowledge base descriptions more specific than generic web tools.
- Raise `max_steps` only after tool descriptions are clear.
- Add an instruction or template telling the agent which source has priority.
- Use RAG instead of Agent when exactly one retrieval-and-answer pass is desired.

## `agents.md` and Skill Markdown Issues

Signals:

- `instructions="agents.md"` appears ignored.
- `.md` tool fails to load metadata.
- Skill tool has no useful name/description.

Fix:

- Confirm the instructions path exists relative to the running process; otherwise pass the instructions string directly.
- Ensure skill Markdown starts with YAML frontmatter containing `name` and `description`.
- Do not confuse txtai's `agents.md` support with repository-level agent instructions for this generated skill.

## GPU vs CPU

Signals:

- CUDA/Metal allocation errors, out-of-memory errors, or backend-specific GPU failures.
- CPU-only host tries to load GPU layers.

Fix:

- Pass `gpu=False` for Transformers/RAG model loading in CPU-only environments.
- For llama.cpp, set `n_gpu_layers=0`.
- Use smaller models or quantized models where supported.
- Keep GPU-specific paths documented but verify them only on hardware that actually has the backend available.

## Observability for RAG and Agents

When debugging complex chains, txtai can be traced through the `mlflow-txtai` integration.

Typical setup:

```bash
pip install mlflow-txtai
mlflow server --host 127.0.0.1 --port 8000
```

```python
import mlflow

mlflow.set_tracking_uri("http://localhost:8000")
mlflow.set_experiment("txtai")
mlflow.txtai.autolog()
```

Run the RAG or Agent call inside `mlflow.start_run()` to inspect retrieval, prompts, model calls, and agent tool steps. This is optional and requires MLflow services; do not make normal runtime flows depend on it.
