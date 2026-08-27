---
name: webagent-family
description: "Route DeepResearch/WebAgent family tasks to the right variant,
  prerequisites, blockers, and sibling sub-skills."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# WebAgent Family Router

Use this sub-skill when a user asks for help choosing, comparing, adapting, or troubleshooting one of the DeepResearch, WebAgent, or Agent family variants and does **not** already name the exact workflow. This is a router and operating-memory skill: it preserves the high-value family map, prerequisites, and workflow-selection knowledge in the bundled references so future agents do not need the original repository documentation.

## Immediate routing rules

1. If the request is about **Tongyi DeepResearch ReAct inference**, `.env` setup, local vLLM serving, OpenRouter/OpenAI-compatible inference, ReAct input data, tools, or rollout files, route to sibling [`../react-inference/SKILL.md`](../react-inference/SKILL.md).
2. If the request is about **official judging, benchmark metric mechanics, prediction-rollout validation, Pass@k summaries, HLE/deep-search evaluation scripts, or LLM-as-judge costs**, route to sibling [`../benchmark-evaluation/SKILL.md`](../benchmark-evaluation/SKILL.md).
3. Otherwise choose family variants from the task signals below, then read the bundled references in this sub-skill before proposing a run plan.

## Fast task-signal chooser

| User task signal | Prefer these family routes | Why | Common blockers |
|---|---|---|---|
| ReAct inference, search/visit agent demo, long-horizon QA with tools | `DeepResearch` via `react-inference`; `WebDancer`; `WebSailor` | Root DeepResearch and early WebAgent projects expose ReAct-style Search/Visit inference patterns. | Model weights, GPUs or hosted API, search/visit credentials, output/data schema. |
| Post-training, agentic data construction, SFT/RL, synthetic QA | `WebDancer`; `WebSailor`; `WebSailor-V2`; `WebShaper`; `WebLeaper`; `AgentFounder`; `AgentScaler` | These projects are primarily training/data/scaling methods rather than simple inference wrappers. | Some assets are paper-only or unreleased; training requires large data, model weights, and RL infrastructure. |
| Multimodal visual web search or VQA | `WebWatcher` | WebWatcher adds image search, visual reasoning, OCR/image benchmarks, and code interpreter tooling. | Trained model, summary model, large image archives, image/text search credentials, optional OSS credentials. |
| Open-ended deep report writing, citations, dynamic outline | `WebWeaver`; conceptual `WebResearcher` | WebWeaver has planner/writer code with dynamic outline and memory-grounded report synthesis; WebResearcher describes iterative report-memory rounds. | 4x80G summary-model serving for WebWeaver, planner/writer APIs, scraper/search credentials. |
| Context summarization, restartable long-horizon search, proactive compression | `WebResummer`/`ReSum`; `AgentFold`; conceptual `WebResearcher` | ReSum periodically compresses trajectories; AgentFold proactively compresses previous steps; WebResearcher uses a running report as central memory. | Summary models/tool checkpoints, vLLM services, search/visit credentials, code placeholders. |
| Efficient/entity-intensive information seeking | `WebLeaper`; `WebShaper`; sometimes `WebSailor-V2` | WebLeaper targets high-density entity retrieval and efficiency rewards; WebShaper formalizes IS task synthesis. | Mostly data/training guidance; runnable inference code may be absent in this checkout. |
| Web traversal, RAG baselines, WebWalkerQA | `WebWalker`; sibling `benchmark-evaluation` for official metric mechanics | WebWalker contributes the WebWalkerQA benchmark, Streamlit demo, RAG baseline, and crawl4ai/Qwen-Agent stack. | crawl4ai setup, provider API keys, dataset acquisition, judge API. |
| Test-time scaling, rollout convergence, answer fusion | `ParallelMuse`; conceptual `WebResearcher`; `AgentFold` | ParallelMuse aggregates multiple rollout reports; WebResearcher documents last-k-fusion; AgentFold can produce long rollouts with compressed context. | Multiple rollouts, local OpenAI-compatible model endpoint, high context length, placeholders/source rough edges. |
| Nested browser-use with click/fill | `NestBrowse` | NestBrowse adds MCP/browser actions beyond Search/Visit: visit, click, fill, and nested page state. | Browser MCP server, local model endpoint, tokenizer path, data/results setup. |
| Continual pretraining or environment scaling | `AgentFounder`; `AgentScaler` | AgentFounder is Agentic CPT; AgentScaler is simulated environment/function-calling scaling. | Public docs mostly describe methodology; no full runnable training code in the inspected tree. |

## Required operating procedure

1. Capture the user’s intent in one sentence and identify the strongest task signals.
2. Run the safe local chooser when useful:

   ```bash
   python scripts/choose_webagent_variant.py "deep report with citations and dynamic outline"
   ```

3. Read [`references/family-map.md`](references/family-map.md) for variant capabilities and evidence status.
4. Read [`references/family-workflows.md`](references/family-workflows.md) before recommending commands, models, dependencies, GPUs, or API services.
5. Read [`references/troubleshooting.md`](references/troubleshooting.md) when a requested family workflow is blocked by missing checkpoints/data, credentials, large archives, generated/vendored code, or path confusion.
6. Reroute back to `react-inference` or `benchmark-evaluation` whenever the user’s request is really root DeepResearch inference or official metric/evaluation mechanics.

## Non-goals and safety boundaries

- Do not reproduce detailed root ReAct configuration here; use `react-inference`.
- Do not reproduce official benchmark metric mechanics here; use `benchmark-evaluation`.
- Do not tell future agents to open the original README tree. Distilled facts are in this sub-skill’s references.
- Do not claim paper-only or placeholder code is immediately runnable. The references distinguish runnable code, data/model notes, and blockers.
- Do not include local checkout paths, private environment prefixes, or secret values in user-facing plans.
