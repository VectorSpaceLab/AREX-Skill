# Co-STORM API reference

## Core imports

```python
from knowledge_storm.collaborative_storm.engine import (
    CollaborativeStormLMConfigs,
    RunnerArgument,
    CoStormRunner,
)
from knowledge_storm.collaborative_storm.modules.callback import (
    BaseCallbackHandler,
    LocalConsolePrintCallBackHandler,
)
from knowledge_storm.dataclass import ConversationTurn, KnowledgeBase
from knowledge_storm.lm import LitellmModel
from knowledge_storm.logging_wrapper import LoggingWrapper
from knowledge_storm.rm import (
    BingSearch,
    YouRM,
    BraveRM,
    SerperRM,
    DuckDuckGoSearchRM,
    TavilySearchRM,
    SearXNG,
)
```

Use `LitellmModel` for new code. It accepts LiteLLM model strings such as `openai/gpt-4o`, `openai/gpt-4o-mini`, or `azure/<deployment-name>` and tracks usage/history for Co-STORM logs.

## CollaborativeStormLMConfigs

`CollaborativeStormLMConfigs` stores the LM used for each Co-STORM component. Create it and set every component before constructing `LoggingWrapper` and `CoStormRunner`.

| Setter | Typical max tokens | Used by | Notes |
| --- | ---: | --- | --- |
| `set_question_answering_lm(model)` | 1000 | Grounded answer generation and query decomposition. | Quality-sensitive; must support citations and concise grounded answers. |
| `set_discourse_manage_lm(model)` | 500 | Turn policy/expert management and expert generation. | Can be cheaper/faster if it follows structured role outputs. |
| `set_utterance_polishing_lm(model)` | 2000 | Polishing expert utterances. | Reduce max tokens for terse discourse. |
| `set_warmstart_outline_gen_lm(model)` | 500 | Warm-start outline from perspective-guided QA. | Warm start is the most expensive stage. |
| `set_question_asking_lm(model)` | 300 | Moderator/question generation. | Lower max tokens usually works. |
| `set_knowledge_base_lm(model)` | 1000 | Mind-map insertion, node expansion, summaries, report sections. | Also used by `KnowledgeBase.to_report()`. |

Minimal helper:

```python
import os
from knowledge_storm.lm import LitellmModel

def make_lm(model: str, max_tokens: int):
    kwargs = {"temperature": 1.0, "top_p": 0.9}
    if model.startswith("azure/"):
        kwargs.update(
            api_key=os.getenv("AZURE_API_KEY"),
            api_base=os.getenv("AZURE_API_BASE"),
            api_version=os.getenv("AZURE_API_VERSION"),
        )
    elif model.startswith("openai/") or model.startswith("gpt-"):
        kwargs.update(api_key=os.getenv("OPENAI_API_KEY"))
    return LitellmModel(model=model, max_tokens=max_tokens, **kwargs)
```

`CollaborativeStormLMConfigs.to_dict()` returns the `.kwargs` for each configured LM. It does not fully preserve model identity for restoration, and it may contain secret fields if you passed explicit keys; redact before sharing.

## RunnerArgument fields

`RunnerArgument(topic=..., ...)` controls Co-STORM runtime behavior.

| Field | Default | Purpose | Practical guidance |
| --- | ---: | --- | --- |
| `topic` | required | Topic of the collaborative discourse. | Use a specific, researchable topic. |
| `retrieve_top_k` | 10 | Results per search query. | Lower for faster/cheaper runs. |
| `max_search_queries` | 2 | Queries generated for each question. | Major search-cost knob. |
| `total_conv_turn` | 20 | Intended maximum conversation turns. | Co-STORM does not run a full loop by itself; caller controls how many `step()` calls happen. |
| `max_search_thread` | 5 | Parallel retriever threads. | Lower on search rate limits. |
| `max_search_queries_per_turn` | 3 | Query budget per turn-level policy. | Keep aligned with `max_search_queries` for conservative runs. |
| `warmstart_max_num_experts` | 3 | Expert perspectives during warm start. | Set 1-2 for smoke tests. |
| `warmstart_max_turn_per_experts` | 2 | QA turns per warm-start expert. | Set 1 for quick sessions. |
| `warmstart_max_thread` | 3 | Parallel warm-start expert work. | Lower on model/search rate limits. |
| `max_thread_num` | 10 | General thread/rate-limit knob retained in runner args. | Lower together with other thread knobs for strict quotas. |
| `max_num_round_table_experts` | 2 | Active experts in later round-table turns. | Lower for predictable turn routing. |
| `moderator_override_N_consecutive_answering_turn` | 3 | Consecutive non-questioning answer turns before moderator asks a question. | Raise to reduce moderator interruptions; lower to force exploration. |
| `node_expansion_trigger_count` | 10 | Expand mind-map node after it accumulates many snippets. | Lower to create more sections; higher to keep the map coarse. |
| `disable_moderator` | `False` | Disable moderator questions. | Use for answer-focused sessions. |
| `disable_multi_experts` | `False` | Disable generated/rotating experts. | Use for simpler debugging or cost control. |
| `rag_only_baseline_mode` | `False` | Use PureRAG baseline mode. | Requires user questions before PureRAG answers and may generate sparse reports. |

Example:

```python
runner_argument = RunnerArgument(
    topic="AI agents for scientific discovery",
    retrieve_top_k=5,
    max_search_queries=2,
    total_conv_turn=8,
    max_search_thread=2,
    warmstart_max_num_experts=2,
    warmstart_max_turn_per_experts=1,
    warmstart_max_thread=2,
    max_num_round_table_experts=2,
    node_expansion_trigger_count=6,
)
```

## Retriever choices

Co-STORM expects a retriever compatible with `dspy.Retrieve`; the native internet retriever choices are:

| Choice | Class | Required credentials/options | Construction pattern |
| --- | --- | --- | --- |
| `bing` | `BingSearch` | `BING_SEARCH_API_KEY` | `BingSearch(bing_search_api_key=os.getenv("BING_SEARCH_API_KEY"), k=runner_argument.retrieve_top_k)` |
| `you` | `YouRM` | `YDC_API_KEY` | `YouRM(ydc_api_key=os.getenv("YDC_API_KEY"), k=runner_argument.retrieve_top_k)` |
| `brave` | `BraveRM` | `BRAVE_API_KEY` | `BraveRM(brave_search_api_key=os.getenv("BRAVE_API_KEY"), k=runner_argument.retrieve_top_k)` |
| `serper` | `SerperRM` | `SERPER_API_KEY` | `SerperRM(serper_search_api_key=os.getenv("SERPER_API_KEY"), k=runner_argument.retrieve_top_k, query_params={"autocorrect": True, "num": runner_argument.retrieve_top_k, "page": 1})` |
| `duckduckgo` | `DuckDuckGoSearchRM` | no API key; needs `duckduckgo_search` and public web access | `DuckDuckGoSearchRM(k=runner_argument.retrieve_top_k, safe_search="On", region="us-en")` |
| `tavily` | `TavilySearchRM` | `TAVILY_API_KEY` | `TavilySearchRM(tavily_search_api_key=os.getenv("TAVILY_API_KEY"), k=runner_argument.retrieve_top_k, include_raw_content=True)` |
| `searxng` | `SearXNG` | SearXNG endpoint URL; optional `SEARXNG_API_KEY` | `SearXNG(searxng_api_url=os.getenv("SEARXNG_API_URL"), searxng_api_key=os.getenv("SEARXNG_API_KEY"), k=runner_argument.retrieve_top_k)` |

If the task needs a user-provided vector corpus, build/validate that retriever through `sub-skills/vector-corpus` first, then pass the ready retriever object as `rm=...` to `CoStormRunner`.

## CoStormRunner construction

Signature:

```python
CoStormRunner(
    lm_config: CollaborativeStormLMConfigs,
    runner_argument: RunnerArgument,
    logging_wrapper: LoggingWrapper,
    rm: Optional[dspy.Retrieve] = None,
    callback_handler: BaseCallbackHandler = None,
)
```

Construction effects to account for:

- If `rm` is `None`, the runner defaults to Bing search with `k=runner_argument.retrieve_top_k`.
- The runner constructs an `Encoder()` immediately. `ENCODER_API_TYPE` must be set before `CoStormRunner(...)`.
- It initializes `conversation_history=[]`, `warmstart_conv_archive=[]`, a `KnowledgeBase`, and a `DiscourseManager` with simulated user, PureRAG agent, moderator, general knowledge provider, and expert generation module.

```python
logging_wrapper = LoggingWrapper(lm_config)
callback_handler = LocalConsolePrintCallBackHandler()
runner = CoStormRunner(
    lm_config=lm_config,
    runner_argument=runner_argument,
    logging_wrapper=logging_wrapper,
    rm=rm,
    callback_handler=callback_handler,
)
```

## Warm start

Signature:

```python
runner.warm_start()
```

Normal mode behavior:

1. Runs perspective-guided background QA with generated experts.
2. Generates a warm-start outline.
3. Inserts collected cited information into the `KnowledgeBase` mind map.
4. Generates a preliminary report and transforms it into an engaging opening conversation.
5. Sets `conversation_history` to the revised warm-start conversation when available; preserves the original QA in `warmstart_conv_archive`.
6. Sets a moderator override for the next system turn.

RAG-only behavior (`runner_argument.rag_only_baseline_mode=True`):

- Skips the multi-expert warm-start protocol.
- Uses `PureRAGAgent.generate_topic_background()` and inserts retrieved information under the root.
- A following system `step()` expects the latest turn to be a `Guest` turn; inject a user question before observing.

## Step through turns

Signature:

```python
runner.step(
    user_utterance: str = "",
    simulate_user: bool = False,
    simulate_user_intent: str = "",
) -> ConversationTurn
```

Call patterns:

```python
# Observe the next Co-STORM system utterance.
turn = runner.step()

# Inject a human utterance; returns the Guest ConversationTurn without producing a system answer.
guest_turn = runner.step(user_utterance="Focus on practical limitations.")

# Let the system answer after the injected Guest turn.
answer_turn = runner.step()

# Automatic experiment mode; requires a non-empty simulated intent.
sim_turn = runner.step(simulate_user=True, simulate_user_intent="ask for evidence quality")
```

`step()` updates `conversation_history`. For generated system turns, it also updates the knowledge base using cited information and may reorganize the map depending on turn policy. For user injection, it only appends the `Guest` turn; the next generated turn performs retrieval and knowledge-base insertion.

## Report generation

Signature:

```python
runner.generate_report() -> str
```

Recommended sequence:

```python
runner.knowledge_base.reorganize()
article = runner.generate_report()
```

The report is a Markdown-like string with headings and inline citation markers such as `[1][2]`. Save it as `report.md` or `report.txt`. If the knowledge base has no section nodes or cited information, the report may be empty or degenerate.

## Serialization and logging

```python
state = runner.to_dict()
restored = CoStormRunner.from_dict(state, callback_handler=LocalConsolePrintCallBackHandler())
log_dump = runner.dump_logging_and_reset()
```

`to_dict()` includes:

- `runner_argument`
- `lm_config` kwargs
- `conversation_history`
- `warmstart_conv_archive`
- serialized `experts`
- serialized `knowledge_base`

`from_dict(data, callback_handler=None)` caveat: the current implementation does not restore the serialized LM configuration. It initializes default LM settings from `OPENAI_API_TYPE` and constructs a new runner. Reattach custom LMs/retrievers manually for robust resume workflows.

`dump_logging_and_reset()` returns pipeline-stage logs containing time usage, LM usage, LM history, query count, and total wall time, then clears accumulated logs by default.

## Callback handler

`LocalConsolePrintCallBackHandler` prints progress messages for turn policy planning, expert action planning, information collection, utterance polishing, mind-map insertion/reorganization, expert-list updates, and warm-start updates.

Use it for local debugging:

```python
runner = CoStormRunner(..., callback_handler=LocalConsolePrintCallBackHandler())
```

Subclass `BaseCallbackHandler` if you need to route these events to a UI, job monitor, or structured logging sink.

## Output file contract

A complete run should leave these files in the selected output directory:

| File | Contents | Validation |
| --- | --- | --- |
| `report.md` | Markdown-style final report with headings and citations. | Non-empty for successful knowledge-base runs. |
| `report.txt` | Plain-text/Markdown-compatible copy for systems expecting `.txt`. | Usually same content as `report.md`. |
| `instance_dump.json` | Serialized runner state from `to_dict()`; redact secrets before sharing. | JSON parses; includes `conversation_history` and `knowledge_base`. |
| `log.json` | Logging dump from `dump_logging_and_reset()`. | JSON parses; has warm-start/turn/report stages after a full run. |
