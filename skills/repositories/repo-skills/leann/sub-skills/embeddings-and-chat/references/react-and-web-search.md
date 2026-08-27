# ReAct And Web Search

## When To Use ReAct

Use `LeannChat.ask` for one retrieval followed by one answer. Use `ReActAgent` when the question needs query refinement, evidence from several local searches, or a deliberate mix of private-index and current public-web information. Each extra iteration adds an LLM call and may add a search or page-fetch request.

## Verified API

```python
ReActAgent(
    searcher,
    llm=None,
    llm_config=None,
    max_iterations=5,
    serper_api_key=None,
    jina_api_key=None,
)
ReActAgent.search(query, top_k=5)
ReActAgent.run(question, top_k=5)

create_react_agent(
    index_path,
    llm_config=None,
    max_iterations=5,
    serper_api_key=None,
    jina_api_key=None,
    **searcher_kwargs,
)
```

Pass either an already constructed `llm` to `ReActAgent` or an `llm_config`, not both as competing configurations. `create_react_agent` constructs `LeannSearcher(index_path, **searcher_kwargs)` and returns the agent.

Local-only example:

```python
from leann import create_react_agent

agent = create_react_agent(
    "indexes/notes",
    llm_config={"type": "ollama", "model": "qwen3:8b"},
    max_iterations=4,
    use_daemon=True,
    daemon_ttl_seconds=600,
)
answer = agent.run("Compare the two indexing strategies and cite local evidence.", top_k=5)
```

Dual-source example using environment variables rather than inline secrets:

```python
import os
from leann import create_react_agent

agent = create_react_agent(
    "indexes/notes",
    llm_config={"type": "openai", "model": "gpt-4o-mini"},
    max_iterations=5,
    serper_api_key=os.environ.get("SERPER_API_KEY"),
    jina_api_key=os.environ.get("JINA_API_KEY"),
)
answer = agent.run("Compare our local design with current public guidance.", top_k=5)
```

## Tool Availability And Network Boundaries

| Tool | Availability rule | Request and credential | Observation |
|---|---|---|---|
| `leann_search("query")` | Always listed. | Calls the supplied local `LeannSearcher`; embedding recomputation may still use a local or hosted embedding provider. | Up to `top_k` results, each with score, a 500-character text prefix, and optional source metadata. |
| `web_search("query")` | Listed only when a Serper key is present. | POST to `https://google.serper.dev/search`; explicit `serper_api_key` or `SERPER_API_KEY`. | Serper organic title, link, and snippet entries. |
| `visit_page("url")` | Listed alongside web tools, which means a Serper key must make web search available. | GET through `https://r.jina.ai/<url>`; `JINA_API_KEY` is optional and sent as a bearer token when present. | Page text truncated to 15,000 characters before being added to the ReAct observation. |

A `JINA_API_KEY` without `SERPER_API_KEY` does not enable the web tools in the generated prompt. Conversely, Serper enables `visit_page` even when Jina has no key because Jina Reader is called without authorization in that case.

All web content is external and untrusted. The agent does not sanitize instructions embedded in a page. Do not let retrieved web text override system constraints, expose private indexed text, or authorize side effects.

## Thought/Action Protocol

On each iteration the LLM receives the original question, prior observations, current iteration count, tool descriptions, and an exact-format instruction. The parser recognizes:

```text
Thought: explain the next evidence need
Action: leann_search("query")
```

It also recognizes `web_search("query")`, `visit_page("url")`, legacy `search("query")`, and:

```text
Thought: enough evidence is available
Action: Final Answer: the answer
```

Operational constraints:

- Put `Action:` on its own new line as requested by the prompt.
- Use one recognized function call with a single quoted argument.
- The parser is regular-expression-based, not a structured tool-calling API. Quoted arguments containing quote characters are fragile.
- Any response containing `Final Answer:` is treated as final.
- If no parseable action is found, `run` treats the response as a final answer rather than retrying automatically.

Use an instruction-following chat model. If it repeatedly emits Markdown fences, JSON, several actions, or unquoted arguments, change the model or tighten its serving template; increasing `max_iterations` alone will not repair parsing.

## Iterations, Fallbacks, And Cost

`max_iterations` bounds tool-selection rounds. If no final answer is produced by then, LEANN makes one additional LLM call containing all collected action/observation context and asks for a final answer. A run can therefore make up to `max_iterations + 1` LLM calls.

Empty local results, a transient web error, an invalid Serper key, or a failed page visit becomes an observation; it does not immediately abort the loop. The LLM can choose a different source or retry on the next iteration. When a model asks for web search without a configured Serper key, the observation tells it to use local search.

Choose the smallest useful bounds:

- `max_iterations=2` or `3` for bounded comparisons.
- `max_iterations=5` for ordinary multi-hop research.
- Larger values only when latency, token use, hosted LLM cost, and repeated web requests are acceptable.
- `top_k` applies independently to each local or web search action; total context can grow quickly.

## Inspecting A Run

`search_history` is reset at the start of every `run`. Each executed tool action records:

```python
{
    "iteration": 1,
    "thought": "...",
    "action": "leann_search:query text",
    "results_count": 5,
    "source": "local",  # or "web"
}
```

Final-answer-only iterations are not appended because no tool ran. Use history to verify source routing and zero-result/tool-error turns; do not treat LLM `thought` text as hidden or authoritative reasoning.

## Failure-Aware Pattern

```python
answer = agent.run(question, top_k=5)

if not answer.strip() or answer.startswith("Error:"):
    raise RuntimeError("ReAct did not produce a usable answer")

if not agent.search_history:
    # The model answered immediately or failed to emit a parseable action.
    # Decide whether direct answering was acceptable for this task.
    pass
```

For provider setup, parser failures, missing web keys, and iteration exhaustion, use [troubleshooting](troubleshooting.md).
