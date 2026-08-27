---
name: deepxiv-sdk
description: "Use the DeepXiv SDK for citation-aware academic and web research
  through its Python Reader, deepxiv CLI, progressive paper APIs, optional local
  LangGraph agent, PMC, bioRxiv/medRxiv, and trending workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# DeepXiv SDK

Use this repo skill when a task needs DeepXiv's hosted literature service or
its optional local research agent. It teaches a later Researcher how to choose
between the Python SDK and CLI, preserve citations and evidence strength, and
avoid credential, quota, truncation, and stale-API mistakes.

## Start here

1. Confirm the installed package and CLI are the expected 1.0.x surface:
   `python -c "import deepxiv_sdk; print(deepxiv_sdk.__version__)"` and
   `deepxiv --help`. If the executable lists an older command set, repair the
   installation before using route-specific flags.
2. Install the base package with `python -m pip install deepxiv-sdk`. For the
   optional local OpenAI-compatible LangGraph agent use
   `python -m pip install "deepxiv-sdk[agent]"` (or `[all]`) and install
   `tiktoken` separately if the optional-import probe reports it missing.
3. Keep DeepXiv and model-provider credentials outside prompts, source files,
   logs, and commits. Ordinary retrieval uses a DeepXiv token; hosted `ask`
   requires a registered account key and has a separate agentic quota.
4. Run the no-network [installation check](scripts/check_install.py) before
   diagnosing package or optional-dependency problems.

## Route by task

- **Python literature research:** Read
  [reader-and-paper-research](sub-skills/reader-and-paper-research/SKILL.md)
  for `Reader`, hosted agentic search, source/citation handling, progressive
  reading, biomedical sources, PMC, and trending signals.
- **Shell commands and operations:** Read
  [cli-and-operations](sub-skills/cli-and-operations/SKILL.md) for command
  selection, flag partitions, JSON/text output, stdout/stderr, token setup,
  health/debug, and CLI recovery.
- **Local model-driven research loop:** Read
  [optional-local-agent](sub-skills/optional-local-agent/SKILL.md) for the
  optional `Agent`, LangGraph tools, provider options, persistent paper context,
  budgets, and circuit-breaker behavior.

## Shared operating rules

- Prefer the narrowest evidence operation: search or `brief` first, then
  `head`, one or two sections, or `preview`; avoid `raw`/`json` for routine
  screening.
- Hosted `agent_search` and `agent_search_stream` distinguish arXiv and web
  flags. Preserve arXiv IDs or URLs, separate retrieved sources from sources
  cited in the answer, and reject `answer_truncated` or streamed `error` output
  as complete evidence.
- The SDK retries ordinary GET timeouts/connections with exponential backoff,
  but hosted agentic calls deliberately do not auto-retry because each call can
  spend quota. Correct the query or wait rather than hammering the endpoint.
- Network, registered credentials, remote LLM keys, and live service results
  are runtime prerequisites; this skill does not claim them from import or
  help checks. Read [cross-cutting troubleshooting](references/troubleshooting.md)
  and the [provenance baseline](references/repo-provenance.md) when a mismatch
  or stale checkout is suspected.
