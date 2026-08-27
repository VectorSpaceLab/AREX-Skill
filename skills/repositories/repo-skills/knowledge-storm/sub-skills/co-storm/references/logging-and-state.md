# Logging and state in Co-STORM

Co-STORM exposes enough runtime state for agents to inspect a collaborative session, serialize it, and debug model/search cost. Treat state dumps as operational artifacts, not public data, because conversation turns may contain retrieved snippets and LM configuration kwargs.

## LoggingWrapper

Create `LoggingWrapper(lm_config)` after the LM config is populated and pass the same wrapper to `CoStormRunner`.

```python
from knowledge_storm.logging_wrapper import LoggingWrapper

logging_wrapper = LoggingWrapper(lm_config)
runner = CoStormRunner(..., logging_wrapper=logging_wrapper)
```

Co-STORM methods wrap work in pipeline stages and events:

- `warm_start()` uses a `warm start stage` with events for perspective-guided QA, outline generation, knowledge-base insertion, and report-to-conversation synthesis.
- `step()` uses `conv turn: N stage` with events for turn policy, utterance generation, expert-list update, knowledge-base insertion, and optional reorganization.
- `generate_report()` uses `report generation after conv turn: N` with a report-generation event.

Dump logs:

```python
log_dump = runner.dump_logging_and_reset()
```

Each stage in `log_dump` contains:

| Field | Meaning |
| --- | --- |
| `time_usage` | Per-event timing with start/end timestamps and elapsed seconds. |
| `lm_usage` | Token usage collected from configured LMs that implement `get_usage_and_reset()`. |
| `lm_history` | Aggregated LM call history from configured LMs, after secret-prefixed kwargs are stripped by the LM wrapper. |
| `query_count` | Search-query count added by grounded QA modules. |
| `total_wall_time` | Wall-clock duration for the stage. |

`dump_logging_and_reset()` clears accumulated logs by default. If you need to inspect while keeping logs, call the wrapper directly: `logging_wrapper.dump_logging_and_reset(reset_logging=False)`.

## Avoid logging stage nesting mistakes

`LoggingWrapper` permits one active pipeline stage at a time. A nested `log_pipeline_stage(...)` will end the current stage safely and start the new one, which can split logs unexpectedly. A `log_event(...)` without an active pipeline stage raises `RuntimeError("No pipeline stage is currently active.")`.

Safe custom pattern:

```python
with logging_wrapper.log_pipeline_stage("custom stage"):
    with logging_wrapper.log_event("custom event"):
        ...
```

Unsafe patterns:

```python
# No active stage: raises RuntimeError.
with logging_wrapper.log_event("event without stage"):
    ...

# Nested stages: the current stage is ended before the nested stage starts.
with logging_wrapper.log_pipeline_stage("outer"):
    with logging_wrapper.log_pipeline_stage("inner"):
        ...
```

For normal Co-STORM use, let `warm_start()`, `step()`, and `generate_report()` manage stages.

## LocalConsolePrintCallBackHandler

Use `LocalConsolePrintCallBackHandler` for visible progress in a terminal or job log.

```python
from knowledge_storm.collaborative_storm.modules.callback import LocalConsolePrintCallBackHandler

runner = CoStormRunner(..., callback_handler=LocalConsolePrintCallBackHandler())
```

Callback events include:

- Turn policy planning start.
- Expert action planning start/end.
- Expert information collection start/end with browsed URLs.
- Expert utterance generation end and polishing start.
- Mind-map insertion and reorganization start/end.
- Expert-list update start.
- Warm-start progress updates.

For applications, subclass `BaseCallbackHandler` and override the methods you need.

## ConversationTurn

A `ConversationTurn` records one discourse turn.

Important fields:

| Field | Meaning |
| --- | --- |
| `role` | Speaker role, e.g. `Guest`, `Moderator`, generated expert role, `PureRAG`. If a role string contains `:`, text after the colon becomes `role_description`. |
| `raw_utterance` | Original model/user utterance. |
| `utterance` | Polished utterance when available; defaults to `raw_utterance`. |
| `utterance_type` | Turn type such as `Original Question`, `Information Request`, `Questioning`, `Support`, or `Potential Answer`. |
| `claim_to_make` | Question/claim focus for grounded answer turns. |
| `queries` | Search queries generated for the turn. |
| `raw_retrieved_info` | Retrieved `Information` records before citation selection. |
| `cited_info` | Citation-indexed `Information` used to update the knowledge base. |

Creation examples:

```python
from knowledge_storm.dataclass import ConversationTurn

turn = ConversationTurn(
    role="Guest",
    raw_utterance="Can we focus on deployment risk?",
    utterance_type="Original Question",
)
```

Do not call `runner.step()` on a runner whose `conversation_history` is empty. The method reads `conversation_history[-1]` before it handles user injection. Call `runner.warm_start()` first, or manually seed a valid `ConversationTurn` only when you know the consequences.

## KnowledgeBase mind map

`CoStormRunner` creates `runner.knowledge_base = KnowledgeBase(...)` during initialization. It is the dynamic mind map and source of the final report.

High-level concepts:

- The root is a `KnowledgeNode` named `root`.
- Child nodes form a hierarchical concept tree.
- Each node stores citation UUIDs in `content`.
- `info_uuid_to_info_dict` maps citation UUIDs to retrieved `Information` objects.
- `info_hash_to_uuid_dict` deduplicates inserted information.
- `update_from_conv_turn(...)` inserts cited information from generated turns.
- `reorganize()` trims empty leaves, merges single-child nodes, expands overloaded nodes, and updates information placement metadata.
- `to_report()` generates report sections from node content.

Inspection helpers:

```python
kb = runner.knowledge_base
print(kb.get_node_hierarchy_string(include_node_content_count=True))
print(len(kb.info_uuid_to_info_dict))
runner.knowledge_base.reorganize()
article = runner.generate_report()
```

If the tree has no child nodes or the information dictionary is empty, report generation may return an empty string.

## State serialization

Serialize state:

```python
import json
from pathlib import Path

state = runner.to_dict()
Path("instance_dump.json").write_text(json.dumps(state, indent=2), encoding="utf-8")
```

The serialized object contains:

```text
runner_argument
lm_config
conversation_history
warmstart_conv_archive
experts
knowledge_base
```

`knowledge_base` contains:

```text
topic
tree
info_uuid_to_info_dict
info_hash_to_uuid_dict
```

`ConversationTurn.to_dict()` serializes utterances, roles, queries, raw retrieved information, utterance type, and claim. It stores `cited_info` as `None` after insertion because the knowledge base owns citation records.

## Restoring with from_dict

Basic call:

```python
from knowledge_storm.collaborative_storm.engine import CoStormRunner
from knowledge_storm.collaborative_storm.modules.callback import LocalConsolePrintCallBackHandler

restored = CoStormRunner.from_dict(
    state,
    callback_handler=LocalConsolePrintCallBackHandler(),
)
```

Current caveat: `from_dict` does **not** restore the serialized `lm_config`; it initializes a default `CollaborativeStormLMConfigs` from `OPENAI_API_TYPE` and constructs a new runner. It also does not preserve a custom retriever object. For reliable resume workflows:

1. Load the serialized conversation and knowledge-base state.
2. Rebuild your intended `CollaborativeStormLMConfigs` and retriever explicitly.
3. Construct a new `CoStormRunner`.
4. Copy `conversation_history`, `warmstart_conv_archive`, `discourse_manager.experts`, and `knowledge_base` from the restored object or from the serialized records.
5. Recheck that credentials match the restored model/retriever choices before calling `step()`.

## Redacting state dumps

`CollaborativeStormLMConfigs.to_dict()` can include `.kwargs` from `LitellmModel`; if explicit `api_key` values were passed, they can appear in `instance_dump.json`. Redact before sharing.

Safe redaction pattern:

```python
SECRET_WORDS = ("api_key", "apikey", "token", "password", "secret")

def redact(obj):
    if isinstance(obj, dict):
        out = {}
        for key, value in obj.items():
            if any(word in str(key).lower() for word in SECRET_WORDS):
                out[key] = "<redacted>"
            else:
                out[key] = redact(value)
        return out
    if isinstance(obj, list):
        return [redact(item) for item in obj]
    return obj
```

The bundled `scripts/run_costorm.py` applies this style of redaction before writing `instance_dump.json`.

## Output inspection recipes

Parse and summarize state:

```bash
python - <<'PY'
import json
from pathlib import Path
state = json.loads(Path("instance_dump.json").read_text())
print("topic:", state["runner_argument"]["topic"])
print("turns:", len(state["conversation_history"]))
print("warmstart turns:", len(state.get("warmstart_conv_archive", [])))
print("experts:", [e["role_name"] for e in state.get("experts", [])])
print("kb info count:", len(state["knowledge_base"].get("info_uuid_to_info_dict", {})))
PY
```

Parse log stages:

```bash
python - <<'PY'
import json
from pathlib import Path
log = json.loads(Path("log.json").read_text())
for stage, data in log.items():
    print(stage, "queries=", data.get("query_count"), "wall=", round(data.get("total_wall_time", 0), 2))
PY
```

Check report file:

```bash
test -s report.md && sed -n '1,40p' report.md
```
