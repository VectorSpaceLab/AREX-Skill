---
name: co-storm
description: "Operate collaborative Co-STORM workflows in knowledge_storm:
  configure models and retrievers, warm start a shared mind map, step through
  user/system turns, generate reports, and persist state/logs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Co-STORM operating sub-skill

Use this sub-skill when the task is about **collaborative Co-STORM**: human-in-the-loop knowledge curation with a warm-started discourse, moderator/multi-expert turn policy, dynamic mind map, final report generation, and state/log export.

Do **not** use this sub-skill for the non-collaborative STORM article pipeline; route that to `sub-skills/storm-wiki`. Do **not** use it for building a VectorRM/Qdrant corpus; route that to `sub-skills/vector-corpus` unless the caller has already supplied a ready retriever object for `CoStormRunner`.

## Operating map

1. Install the public package in the active Python environment: `pip install knowledge-storm`.
2. Configure model and embedding credentials. Co-STORM creates an `Encoder` during `CoStormRunner.__init__`, so `ENCODER_API_TYPE` and the matching embedding credentials must be set before runner construction.
3. Select an internet retriever: `bing`, `you`, `brave`, `serper`, `duckduckgo`, `tavily`, or `searxng`.
4. Create `CollaborativeStormLMConfigs`, `RunnerArgument`, `LoggingWrapper`, retriever, optional callback handler, then `CoStormRunner`.
5. Call `warm_start()` before `step()`. `step()` assumes `conversation_history` is non-empty.
6. Alternate user injection (`step(user_utterance="...")`) and system observation (`step()`), then reorganize the knowledge base and call `generate_report()`.
7. Persist `report.md` or `report.txt`, `instance_dump.json`, and `log.json`.

## Bundled references

- [Workflows](references/workflows.md): concrete CLI and Python workflows for dry-run, warm start, user injection, observation, report generation, and output validation.
- [API reference](references/api-reference.md): tables for `CollaborativeStormLMConfigs`, `RunnerArgument`, `CoStormRunner`, callbacks, retrievers, turn policy fields, and output contracts.
- [Logging and state](references/logging-and-state.md): `LoggingWrapper`, `ConversationTurn`, `KnowledgeBase`, `to_dict`, `from_dict`, redaction, and log/state inspection.
- [Troubleshooting](references/troubleshooting.md): missing model/search/encoder keys, rate limits, warm-start cost, empty history, logging stage nesting, `from_dict` caveat, and empty report failures.

## Bundled helper

- [scripts/run_costorm.py](scripts/run_costorm.py) runs a self-contained Co-STORM session using `LitellmModel`, supports `--topic`, `--output-dir`, `--retriever`, Co-STORM hyperparameters, `--observe-turns`, `--user-utterance`, and `--dry-run`, and writes report/state/log files. `--dry-run` performs no LLM or network calls.
