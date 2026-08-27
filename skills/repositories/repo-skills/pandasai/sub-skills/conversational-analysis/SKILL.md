---
name: conversational-analysis
description: "Guides PandasAI natural-language DataFrame chat, Agent workflows,
  LLM configuration, response objects, generated-code repair, and legacy wrapper
  migration."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Conversational Analysis

Use this sub-skill when the user wants to ask natural-language questions of
tabular data through PandasAI, configure the LLM behind `.chat()`, inspect typed
responses, debug generated code, or migrate from legacy `SmartDataframe`/
`SmartDatalake` usage.

## Fast route

1. If the user only has a pandas dataframe or a CSV/Excel file, create a
   PandasAI `DataFrame` or route dataset creation to the semantic-layer sub-skill.
2. Configure a real LLM before `.chat()` unless this is an offline smoke:

   ```python
   import pandasai as pai
   from pandasai_litellm.litellm import LiteLLM

   llm = LiteLLM(model="gpt-4.1-mini", api_key="...")
   pai.config.set({"llm": llm, "save_logs": True, "verbose": False, "max_retries": 3})
   ```

3. Use `df.chat(...)` for a single dataframe, `pai.chat(...)` for multiple
   DataFrames in a fresh global conversation, or `Agent(...).follow_up(...)` for
   explicit multi-turn state.
4. Inspect `response.value`, `response.type`, and `response.last_code_executed`
   before deciding that a PandasAI run succeeded.
5. If code is untrusted or the app is public-facing, route to
   [`../sandbox-and-security/SKILL.md`](../sandbox-and-security/SKILL.md).

## Read next

- [`references/api-reference.md`](references/api-reference.md) for verified
  signatures, config fields, response classes, and legacy wrapper notes.
- [`references/workflows.md`](references/workflows.md) for copyable chat,
  multi-dataframe, follow-up, FakeLLM, and migration recipes.
- [`references/response-formats.md`](references/response-formats.md) for result
  dictionary rules and response object handling.
- [`references/troubleshooting.md`](references/troubleshooting.md) when `.chat()`
  fails, generated code is rejected, or response parsing errors appear.
- [`scripts/offline_chat_smoke.py`](scripts/offline_chat_smoke.py) for a
  deterministic no-credential smoke test.

## Core choices

| Situation | Use |
| --- | --- |
| One dataframe and no need to keep a separate explicit agent | `df.chat("question")` |
| Several dataframes in one question | `pai.chat("question", df1, df2, ...)` |
| Multi-turn conversation with explicit memory and options | `agent = Agent([...], memory_size=10); agent.chat(...); agent.follow_up(...)` |
| Need deterministic local validation | `FakeLLM` plus bundled `offline_chat_smoke.py` |
| User asks about `SmartDataframe` or `SmartDatalake` | Explain deprecation and migrate to `pai.DataFrame`, `pai.chat`, or `Agent` |

## Boundaries

- Route schema creation, `pai.create`, `pai.load`, SQL views, transformations,
  and CSV/Excel dataset modeling to
  [`../semantic-layer/SKILL.md`](../semantic-layer/SKILL.md).
- Route `@pai.skill()` and global custom function registration to
  [`../custom-skills/SKILL.md`](../custom-skills/SKILL.md).
- Route Docker sandbox lifecycle and custom sandbox implementations to
  [`../sandbox-and-security/SKILL.md`](../sandbox-and-security/SKILL.md).
- Route the `pai` command-line interface to
  [`../cli-and-project-ops/SKILL.md`](../cli-and-project-ops/SKILL.md).

## Safe validation

Run this from any environment where PandasAI is installed:

```bash
python sub-skills/conversational-analysis/scripts/offline_chat_smoke.py
```

The script uses `FakeLLM`, a tiny in-memory dataframe, and generated code that
calls `execute_sql_query`. It should not need network, provider credentials, or
large data.

## Common gotchas

- `.chat()` fails without a configured LLM, except when using `FakeLLM` or a
  supplied config object for tests.
- Generated code must call `execute_sql_query` and assign a valid `result`
  dictionary. Free-form pandas code without the query function is rejected by
  the package's validator.
- Table names in generated SQL must match the registered dataframe schema name.
  Hyphenated dataset paths are transformed to underscore table names.
- Printing a chart response can open an image viewer; use `.save(...)` in
  automation.
