# Local Agent workflows

These recipes are self-contained adaptations of the repository's Agent examples. They use placeholders for runtime secrets and never embed a private path or credential.

## 1. Bounded first query

```python
from deepxiv_sdk import Agent, Reader

reader = Reader(token="runtime-deepxiv-token")
agent = Agent(
    api_key="runtime-llm-key",
    reader=reader,
    model="gpt-4",
    max_llm_calls=8,
    max_time_seconds=120,
    max_tokens=2048,
    temperature=0.2,
    print_process=False,
    stream=False,
)
answer = agent.query("Find recent papers on agent memory and compare their main ideas.")
print(answer)
```

Start with metadata and section TLDRs. The Agent prompt tells the model to search first, load metadata before sections, check token counts, prefer previews/targeted sections, and avoid a large full-paper fetch unless justified.

The call budget counts graph-level LLM rounds, not each individual token. The internal completion helper may retry a failed request up to three times. Keep both the call and wall-clock budgets bounded for unattended use.

## 2. Follow-up with persistent paper context

```python
first = agent.query("Summarize the strongest papers about tool-use memory.")
second = agent.query("Compare the memory update mechanisms in the papers you just loaded.")
loaded = agent.get_loaded_papers()
print(len(loaded), second)
```

A new query gets a fresh message list but starts with a copy of the papers persisted by the previous query. The final state merges any papers loaded during the new query back into the persistent dictionary. This is paper-context persistence, not a transcript or response cache.

To start a clean topic:

```python
agent.query("Start a separate topic on diffusion models.", reset_papers=True)
# or, before a later query:
agent.reset_papers()
```

## 3. Manual preload with recoverable absence

```python
for paper_id in ("2409.05591", "2504.21776"):
    if not agent.add_paper(paper_id):
        print(f"Skip {paper_id}: missing or not indexed yet")

answer = agent.query("Compare the papers currently loaded in context.")
```

`add_paper()` is idempotent for an already-loaded ID. A `False` result does not add a partial entry. Catch genuine API exceptions separately; do not silently turn a server outage into a missing-paper result.

## 4. OpenAI-compatible provider and reasoning model

```python
agent = Agent(
    api_key="runtime-provider-key",
    reader=reader,
    base_url="https://provider.example/v1",
    model="provider/reasoning-model",
    max_llm_calls=6,
    max_time_seconds=90,
    max_tokens=2048,
    extra_body={"provider_option": "value"},
    enable_thinking=False,
)
```

`enable_thinking=False` is merged after the caller's `extra_body`, so it wins if the same key was present. Every LLM request, including the circuit-breaker/limit forced-answer request, receives the merged body. Use this for providers that otherwise return reasoning content that cannot legally occur in an intermediate assistant tool-call history.

The local Agent needs an OpenAI-compatible chat-completions endpoint. The `Reader` still talks to the DeepXiv data service independently; `base_url` changes only the LLM client.

## 5. Streaming and verbose process output

```python
agent = Agent(
    api_key="runtime-provider-key",
    reader=reader,
    stream=True,
    print_process=True,
    max_llm_calls=10,
    max_time_seconds=180,
)
print(agent.query("Explain the method and key limitations of the best matching paper."))
```

Streaming expects iterable completion chunks with `choices[0].delta`. The graph accumulates content and tool-call fragments before continuing. Verbose mode prints progress and provider reasoning separately; reasoning text is not placed in message history. Verify that the selected provider supports both streaming and function/tool calls before enabling this combination.

## 6. Hard-case test recipes

### Reasoning model, bounded calls, persistent papers

Use a fake Reader whose `head()` returns one deterministic paper, and a fake OpenAI-compatible client that first requests `load_paper` and then returns a tagged answer. Construct the Agent with `enable_thinking=False`, `max_llm_calls=3`, and a short `max_time_seconds`. Run two queries and assert that the second query's initial system context contains the paper while the request body still contains `extra_body["enable_thinking"] is False`. Do not call a real endpoint.

### Service failures plus a recoverable missing ID

Use a Reader whose search raises `ServerError` repeatedly but whose `head()` raises `NotFoundError` for a recent/missing ID. Assert that the tool result for the missing ID says it could not find the paper and `is_service_failure()` is false; assert that repeated service-failure rounds increment the counter and force a final answer without tools once the threshold is reached. The missing ID must remain a model-recoverable condition rather than causing the breaker to trip.
