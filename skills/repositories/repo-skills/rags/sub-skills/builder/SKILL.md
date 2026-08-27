---
name: builder
description: "Use this RAGs sub-skill to build a Streamlit RAG agent from files,
  directories, URLs, optional web search, model settings, and RAG parameters."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# RAGs Builder

Use this sub-skill when the task is to create a new RAGs bot, diagnose the Home
page builder flow, or use the builder APIs directly. RAGs is a Streamlit app
that asks a builder agent to create a retrieval-augmented chat agent over a
single data source.

## Read This When

- The user wants to build a RAG bot from local files, one directory, or URLs.
- The task mentions the Home page, builder agent, task description, system
  prompt generation, `RAGAgentBuilder`, or `RAGParams`.
- The user needs to choose `top_k`, `chunk_size`, embedding model, LLM provider,
  summarization, or optional `web_search`.
- The user asks why source loading, OpenAI secrets, web search, or multimodal
  setup fails before the agent exists.

If the bot already exists and the user wants to edit or delete it, read
[`../configuration/SKILL.md`](../configuration/SKILL.md). If the user wants to
ask questions to an existing bot, read [`../chat/SKILL.md`](../chat/SKILL.md).

## Core Workflow

1. Confirm dependencies and secrets first. The app expects a Streamlit secret
   named `openai_key`; provider-specific keys are needed only for their routes.
2. Validate the data-source choice with
   [`scripts/validate_source_selection.py`](scripts/validate_source_selection.py)
   before invoking builder logic. RAGs accepts exactly one source kind: local
   files, one directory, or URLs.
3. Use the builder conversation to collect the task description and let the
   builder create the system prompt.
4. Load data, inspect or set RAG parameters, optionally add `web_search` when a
   `metaphor_key` secret is configured, then create the agent.
5. After creation, route to the configuration and chat sub-skills for later
   editing and querying.

For detailed step-by-step routes, model identifiers, data-source rules, and
validation checks, read [`references/workflows.md`](references/workflows.md).
For signatures and defaults verified from the package inspection environment,
read [`references/api-reference.md`](references/api-reference.md).
For failure symptoms and fixes, read
[`references/troubleshooting.md`](references/troubleshooting.md).

## Important Operating Facts

- `RAGParams` defaults are `include_summarization=False`, `top_k=2`,
  `chunk_size=1024`, `embed_model="default"`, and
  `llm="gpt-4-1106-preview"`.
- `load_data` requires exactly one of `file_names`, `directory`, or `urls` and
  raises a `ValueError` when zero or multiple source kinds are supplied.
- Unprefixed LLM names are treated as OpenAI models. Recognized prefixes are
  `openai:`, `anthropic:`, `replicate:`, and `local:`.
- The web-search tool is only exposed when a `metaphor_key` Streamlit secret is
  present, and its tool name is `web_search`.
- The beta multimodal builder path is optional. The minimum verified
  environment imported multimodal classes but did not install the torch,
  torchvision, or CLIP runtime stack and did not run external model calls.

## Boundaries

Do not claim that a full OpenAI, Anthropic, Replicate, Metaphor, URL-loading, or
multimodal chat call was verified unless the user supplies credentials/network
and asks for that execution. For safe checks, use the bundled validator and the
root installation diagnostic instead of launching a long-running Streamlit
server.
