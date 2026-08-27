---
name: rags
description: "Use this repo skill for RAGs, a Streamlit app that builds
  configurable LlamaIndex RAG agents from natural-language setup, data sources,
  and model settings."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# RAGs Repo Skill

RAGs is a Streamlit application for building retrieval-augmented chat agents
over user-provided data. Use this skill when the task mentions RAGs, creating a
RAG bot from natural language, configuring generated RAG parameters, querying a
generated agent, or debugging RAGs cache/secrets/model behavior.

## Before Acting

1. Read [`references/repo-provenance.md`](references/repo-provenance.md) when
   checking whether this skill is current for a checkout or when refreshing it.
2. Read [`references/app-architecture.md`](references/app-architecture.md) when
   you need the cross-page architecture, state, cache, model, and tool flow.
3. Run or inspect [`scripts/check_install.py`](scripts/check_install.py) for a
   safe dependency/source-import diagnostic. It does not call external LLMs.
4. Use [`scripts/run_rags_app.py`](scripts/run_rags_app.py) to validate or wrap
   the Streamlit launch command for a user-provided RAGs checkout. It dry-runs
   by default; pass `--execute` only when the user wants a long-running server.

The current source snapshot is an app-style repository, not an installable
Python package named `rags`. Dependency-oriented setup and running from a RAGs
checkout is the supported operating model captured by this skill.

## Route Map

| User intent | Read |
| --- | --- |
| Build a new RAG bot from files, a directory, URLs, task text, RAG parameters, optional web search, or beta multimodal setup. | [`sub-skills/builder/SKILL.md`](sub-skills/builder/SKILL.md) |
| Inspect, edit, update, delete, rename, or repair a generated agent's configuration or cache. | [`sub-skills/configuration/SKILL.md`](sub-skills/configuration/SKILL.md) |
| Ask questions to an existing generated agent, inspect sources, or debug no/irrelevant/broken sources. | [`sub-skills/chat/SKILL.md`](sub-skills/chat/SKILL.md) |
| Diagnose install, secrets, dependency version, root-package install, cache upgrade, or optional dependency problems. | [`references/troubleshooting.md`](references/troubleshooting.md) |

## Install and Launch Checks

Use public project instructions or equivalent dependency installation. The
verified inspection environment used Python 3.10 with `streamlit==1.28.0`,
`llama-index==0.9.7`, `llama-hub==0.0.44`, `langchain==0.0.305`, and
`pypdf==3.17.1`. A dependency-only Poetry setup or requirements-based setup may
be needed because root package installation fails for this snapshot.

Safe checks:

```bash
python scripts/check_install.py
python scripts/check_install.py --repo-root /path/to/rags
python scripts/run_rags_app.py --repo-root /path/to/rags --check-secrets
```

Launch only with user intent:

```bash
python scripts/run_rags_app.py --repo-root /path/to/rags --execute -- --server.headless true
```

RAGs reads a Streamlit secret named `openai_key` while configuring the builder
LLM. Provider-specific routes may also need `anthropic_key`, `replicate_key`, or
`metaphor_key`.

## Verification Scope

The generated skill is based on source inspection plus live dependency/source
module inspection. Safe checks covered imports, signatures, `RAGParams` defaults,
local text `load_data`, Streamlit CLI help, and cache-registry behavior. The
following were intentionally not executed by default: real OpenAI/Anthropic/
Replicate/Metaphor calls, URL downloads, a long-running Streamlit server, and
actual beta multimodal construction with torch/CLIP dependencies.

## Boundaries

Do not use this skill as a generic LlamaIndex manual. It is specifically for the
RAGs app's builder/configuration/chat workflow and its cache/secrets behavior.
For changing the RAGs source code itself, treat this as repository maintenance
and combine with ordinary code inspection rather than relying only on this
operating skill.
