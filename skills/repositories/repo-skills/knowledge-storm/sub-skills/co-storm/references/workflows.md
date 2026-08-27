# Co-STORM workflows

This reference is self-contained for operating collaborative Co-STORM after installing the public `knowledge-storm` package. It uses current `knowledge_storm.lm.LitellmModel` guidance rather than the older provider-specific OpenAI/Azure wrappers.

## Credential setup

Co-STORM uses both chat-completion LMs and an embedding encoder for the mind map. Set these before constructing `CoStormRunner`.

Minimal OpenAI-style setup:

```bash
export OPENAI_API_KEY="..."
export ENCODER_API_TYPE="openai"
export BING_SEARCH_API_KEY="..."        # if --retriever bing
```

Azure-style setup:

```bash
export ENCODER_API_TYPE="azure"
export AZURE_API_KEY="..."
export AZURE_API_BASE="https://<resource>.openai.azure.com/"
export AZURE_API_VERSION="2024-02-15-preview"
# use Azure deployment names with LiteLLM, for example --model azure/my-gpt-4o-deployment
```

A local `secrets.toml` can also be used by the bundled helper:

```toml
OPENAI_API_KEY = "..."
ENCODER_API_TYPE = "openai"
BING_SEARCH_API_KEY = "..."
```

## Dry-run a planned session

`--dry-run` performs no LLM calls, embedding calls, retriever construction, or network access. It is the safest way to check parser options, output paths, and required environment variables.

```bash
python scripts/run_costorm.py \
  --topic "Graph neural networks for traffic forecasting" \
  --output-dir ./runs/costorm-traffic \
  --retriever bing \
  --observe-turns 2 \
  --user-utterance "Focus on deployment constraints and uncertainty." \
  --dry-run
```

Expected dry-run signal: JSON describing `runner_argument`, model names, retriever, missing/set environment variables, and planned outputs (`report.md`, `report.txt`, `instance_dump.json`, `log.json`).

## Run a compact collaborative session

Use small turn counts first. `warm_start()` is the expensive stage because it spawns perspective-guided background QA, outline synthesis, knowledge-base insertion, and a first report-to-conversation pass.

```bash
python scripts/run_costorm.py \
  --topic "Graph neural networks for traffic forecasting" \
  --output-dir ./runs/costorm-traffic \
  --retriever bing \
  --model openai/gpt-4o \
  --observe-turns 2 \
  --user-utterance "Please compare evaluation protocols for spatial-temporal forecasting." \
  --retrieve-top-k 5 \
  --max-search-queries 2 \
  --warmstart-max-num-experts 2 \
  --warmstart-max-turn-per-experts 1 \
  --warmstart-max-thread 2 \
  --max-search-thread 2 \
  --enable-console-log
```

The helper does this sequence:

1. Load optional `secrets.toml`.
2. Build `CollaborativeStormLMConfigs` with `LitellmModel` instances.
3. Build `RunnerArgument(topic=..., ...)`.
4. Build the selected retriever.
5. Construct `LoggingWrapper` and optional `LocalConsolePrintCallBackHandler`.
6. Construct `CoStormRunner`.
7. Call `warm_start()`.
8. If `--user-utterance` is present, call `step(user_utterance=...)` to inject a human steering turn.
9. Call `step()` `--observe-turns` times to observe Co-STORM system turns.
10. Call `knowledge_base.reorganize()` and `generate_report()`.
11. Write `report.md`, `report.txt`, `instance_dump.json`, and `log.json`.

## Python API workflow

```python
import json
import os
from pathlib import Path

from knowledge_storm.collaborative_storm.engine import (
    CollaborativeStormLMConfigs,
    RunnerArgument,
    CoStormRunner,
)
from knowledge_storm.collaborative_storm.modules.callback import LocalConsolePrintCallBackHandler
from knowledge_storm.lm import LitellmModel
from knowledge_storm.logging_wrapper import LoggingWrapper
from knowledge_storm.rm import BingSearch


def lm(model: str, max_tokens: int):
    return LitellmModel(
        model=model,
        max_tokens=max_tokens,
        api_key=os.getenv("OPENAI_API_KEY"),
        temperature=1.0,
        top_p=0.9,
    )

lm_config = CollaborativeStormLMConfigs()
lm_config.set_question_answering_lm(lm("openai/gpt-4o", 1000))
lm_config.set_discourse_manage_lm(lm("openai/gpt-4o", 500))
lm_config.set_utterance_polishing_lm(lm("openai/gpt-4o", 2000))
lm_config.set_warmstart_outline_gen_lm(lm("openai/gpt-4o", 500))
lm_config.set_question_asking_lm(lm("openai/gpt-4o", 300))
lm_config.set_knowledge_base_lm(lm("openai/gpt-4o", 1000))

runner_argument = RunnerArgument(
    topic="Graph neural networks for traffic forecasting",
    retrieve_top_k=5,
    max_search_queries=2,
    total_conv_turn=8,
    warmstart_max_num_experts=2,
    warmstart_max_turn_per_experts=1,
    warmstart_max_thread=2,
    max_search_thread=2,
)

logging_wrapper = LoggingWrapper(lm_config)
rm = BingSearch(
    bing_search_api_key=os.getenv("BING_SEARCH_API_KEY"),
    k=runner_argument.retrieve_top_k,
)
runner = CoStormRunner(
    lm_config=lm_config,
    runner_argument=runner_argument,
    logging_wrapper=logging_wrapper,
    rm=rm,
    callback_handler=LocalConsolePrintCallBackHandler(),
)

runner.warm_start()
runner.step(user_utterance="Compare benchmark splits and metrics.")
turn = runner.step()  # observe a system-generated turn
print(f"{turn.role}: {turn.utterance}")

runner.knowledge_base.reorganize()
article = runner.generate_report()

out = Path("runs/costorm-traffic")
out.mkdir(parents=True, exist_ok=True)
(out / "report.md").write_text(article, encoding="utf-8")
(out / "report.txt").write_text(article, encoding="utf-8")
(out / "instance_dump.json").write_text(json.dumps(runner.to_dict(), indent=2), encoding="utf-8")
(out / "log.json").write_text(json.dumps(runner.dump_logging_and_reset(), indent=2), encoding="utf-8")
```

If you plan to share `instance_dump.json`, redact secret-looking fields from `lm_config` first. The bundled helper redacts `api_key`, token, password, and secret fields automatically.

## Turn policy patterns

### Observe a system turn

Call `step()` with no `user_utterance`. Co-STORM chooses the next agent through `DiscourseManager.get_next_turn_policy(...)`:

- Moderator if the system should ask a thought-provoking question or if warm start requested a moderator override.
- General knowledge provider or a rotating expert if the previous turn is not a question and multi-experts are enabled.
- Pure RAG agent if `rag_only_baseline_mode=True` and the last turn is a `Guest` turn.

### Inject a human/user turn

Call `step(user_utterance="...")`. This appends a `ConversationTurn(role="Guest", utterance_type="Original Question")` and returns without producing a system answer. Call `step()` again to let Co-STORM respond.

Important: `step()` reads `conversation_history[-1]` before branching. Always run `warm_start()` or seed `conversation_history` with a valid `ConversationTurn` before the first `step()` call.

### Simulated user turns

For automatic experiments, call `step(simulate_user=True, simulate_user_intent="...")`. A non-empty simulated intent is required. Treat this as an experiment mode, not a normal human-in-the-loop session.

## Moderator, expert, RAG-only, and thread knobs

Use these knobs to control cost, latency, and turn behavior:

| Knob | Effect | Cost/rate-limit guidance |
| --- | --- | --- |
| `disable_moderator` | Prevents moderator-generated questions after consecutive answering turns. | Reduces question-generation calls and avoids unexpected topic shifts. |
| `disable_multi_experts` | Uses the general knowledge provider instead of rotating generated experts. | Reduces expert-list maintenance and perspective diversity. |
| `rag_only_baseline_mode` | Uses PureRAG behavior for a baseline rather than collaborative multi-agent policy. | Requires user question turns before PureRAG answers; final reports may be sparse if the mind map never develops section nodes. |
| `max_search_thread` | Parallelism for retriever calls inside grounded QA. | Lower first when search APIs rate-limit. |
| `warmstart_max_thread` | Parallelism for warm-start expert conversations. | Lower first when warm start is expensive or fails under provider limits. |
| `max_thread_num` | RunnerArgument thread/rate-limit knob retained by the Co-STORM CLI shape. | Lower together with other thread knobs for conservative runs. |
| `max_search_queries` | Search queries generated per question. | Lower to reduce search calls and context volume. |
| `warmstart_max_num_experts` | Number of warm-start perspectives. | Lower for quick validation runs. |
| `warmstart_max_turn_per_experts` | Turns per warm-start expert. | Lower to reduce warm-start runtime. |
| `total_conv_turn` | Intended conversation budget. | Keep small for smoke sessions; enforce in calling application if running interactive loops. |

## Output validation checklist

After a run, check:

```bash
python -m json.tool ./runs/costorm-traffic/instance_dump.json >/dev/null
python -m json.tool ./runs/costorm-traffic/log.json >/dev/null
test -s ./runs/costorm-traffic/report.md
```

Inspect `instance_dump.json` for:

- `runner_argument.topic`
- non-empty `conversation_history`
- `warmstart_conv_archive` if warm start ran in normal mode
- `experts`
- `knowledge_base.tree`
- `knowledge_base.info_uuid_to_info_dict`

Inspect `log.json` for stages such as `warm start stage`, `conv turn: N stage`, and `report generation after conv turn: N`.
