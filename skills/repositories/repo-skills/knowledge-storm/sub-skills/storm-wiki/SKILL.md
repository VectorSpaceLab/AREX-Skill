---
name: storm-wiki
description: "Generate STORM Wikipedia-like articles with STORMWikiRunner,
  LiteLLM model configs, internet retrievers, staged execution, output
  inspection, callbacks, and demo-light setup guidance."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# STORM Wiki Article Generation

Use this sub-skill when the task is to generate, resume, inspect, or troubleshoot a STORM Wikipedia-like article with the installed `knowledge-storm` Python package.

## When to use

- Configure `STORMWikiLMConfigs`, `STORMWikiRunnerArguments`, and a search retriever.
- Run `STORMWikiRunner.run(...)` through research, outline, article, and polish stages.
- Inspect STORM output files such as `conversation_log.json`, `storm_gen_outline.txt`, `storm_gen_article.txt`, `storm_gen_article_polished.txt`, `run_config.json`, and `llm_call_history.jsonl`.
- Add `BaseCallbackHandler` callbacks for progress reporting.
- Distill demo-light Streamlit setup patterns without copying the full UI.

## Route elsewhere

- CSV, Qdrant, `VectorRM`, and user-corpus grounding belong to the `vector-corpus` sub-skill.
- Collaborative discourse, `warm_start`, `step`, `generate_report`, mind map behavior, and Co-STORM logging belong to the `co-storm` sub-skill.
- Full Streamlit UI source code and assets are not bundled here; use only the distilled setup notes in this sub-skill.

## Operating map

1. Read [workflows](references/workflows.md) for commands, staged/resume runs, output validation, and callback use.
2. Read [API reference](references/api-reference.md) for runner classes, method signatures, stage flags, callback hooks, and output-file contracts.
3. Read [model and retriever options](references/model-and-retriever-options.md) before choosing LiteLLM models or search providers.
4. Read [demo-light notes](references/demo-light.md) only when asked to build or reason about the local Streamlit demo.
5. Use [troubleshooting](references/troubleshooting.md) for missing credentials, optional packages, rate limits, resume-file errors, topic sanitization, and deprecated wrapper fixes.
6. Use the bundled helper [scripts/run_storm_wiki.py](scripts/run_storm_wiki.py) for a self-contained CLI. Start with `--help` and `--dry-run` before any network or LLM call.

## Minimal safe path

```bash
pip install knowledge-storm
python scripts/run_storm_wiki.py --help
python scripts/run_storm_wiki.py \
  --dry-run \
  --topic "Example topic" \
  --output-dir ./storm-results \
  --retriever bing
```

If the dry-run reports missing model or retriever credentials, set environment variables or pass a `--secrets-file` TOML before running without `--dry-run`.
