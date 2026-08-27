# Model and Repository Overview

Use this reference when a task asks what DeepResearch contains, which family member to use, or whether a workflow is actually runnable from the public checkout.

## Root DeepResearch

Tongyi DeepResearch is an agentic large-language-model release centered on **Tongyi-DeepResearch-30B-A3B**. The public description emphasizes:

- 30.5B total parameters with 3.3B activated per token.
- 128K context length.
- Long-horizon, deep information-seeking tasks.
- Strong benchmark results across HLE, BrowseComp, BrowseComp-ZH, WebWalkerQA, xbench-DeepSearch, FRAMES, and SimpleQA.
- Two inference paradigms in the project narrative:
  - **ReAct**: the open root code path with search/visit/scholar/python/file tools.
  - **Heavy / IterResearch-style mode**: described as a test-time scaling direction but not fully open-sourced in the inspected checkout.

The root checkout exposes practical operating code for ReAct inference and official-style evaluation, but full local execution still needs model weights, GPUs or a hosted model endpoint, and external tool credentials.

## Root Code Surfaces

| Surface | Purpose | Runtime status |
|---|---|---|
| ReAct inference | Multi-turn tool-using agent with web search, page visit/summarization, Google Scholar, Python sandbox, and file parsing tools | Runnable only after configuration, model serving or API adaptation, and credentials |
| Data fixtures | Small JSONL examples and an uploaded-file marker example | Safe for validators and schema checks |
| Official-style evaluation | LLM-as-judge routes for DeepSearch-style datasets and HLE | Credentialed and API-costing; validate shapes first |
| Environment example | `.env` variable catalog for model paths, output/data, tool credentials, NCCL/Torch, SandboxFusion, and IDP/file parsing | Use as a template; never commit real secrets |

## WebAgent / Agent Family Relationship

The repository embeds a broad family of related research projects. Treat them as capability routes, not as one homogeneous package:

- **WebDancer**: ReAct-style autonomous information seeking and a four-stage agentic training paradigm.
- **WebSailor / WebSailor-V2**: high-uncertainty browsing and post-training/RL methods around SailorFog-QA-style tasks.
- **WebShaper**: formalization-driven information-seeking data synthesis with a local 500-example dataset.
- **WebWatcher**: multimodal visual-language web research and visual search/evaluation assets.
- **WebResearcher**: iterative deep-research paradigm with report memory and test-time fusion; primarily conceptual in the inspected tree.
- **WebResummer / ReSum**: restartable long-horizon ReAct via periodic summarization.
- **WebWeaver**: planner/writer deep report generation with dynamic outlines and memory-grounded synthesis.
- **WebWalker**: web traversal benchmark/RAG demo around WebWalkerQA.
- **WebLeaper**: efficient entity-intensive information seeking and ISR/ISE training signals.
- **AgentFold**: proactive context management for long-horizon web agents.
- **ParallelMuse**: multiple rollout report convergence and answer integration.
- **NestBrowse**: nested browser-use with visit/click/fill style actions.
- **AgentFounder / AgentScaler**: related training/scaling methodology docs for Agentic CPT and simulated environment scaling.

Use the `webagent-family` sub-skill when the user asks which variant fits a task.

## Runnable vs. Method-Only

Before promising a command or result, classify the target route:

| Route type | Examples | What to verify first |
|---|---|---|
| Safe local validation | Dataset schema checks, rollout-shape checks, family chooser, checkout inspection | Python 3, file paths, expected JSON/JSONL shape |
| Credentialed API work | Search, Visit summarization, Google Scholar, file parsing, LLM-as-judge scoring, hosted OpenAI-compatible inference | User approval, API variables, cost and rate limits |
| Local model serving | Root DeepResearch vLLM, WebDancer/WebSailor SGLang, WebWeaver summary model, WebWatcher VLM | GPU count/VRAM, model weights, ports, dependency stack, long-running permission |
| Large data or images | WebWatcher image archives, benchmark datasets not present to avoid leakage | Dataset source, size, path layout, download permission |
| Method-only or partial code | WebResearcher, WebSailor-V2, WebLeaper, AgentFounder, AgentScaler | Whether the user wants conceptual guidance rather than execution |

## Default Task Handling

- If the user says “run DeepResearch on my questions,” route to `react-inference`.
- If the user says “score/evaluate my outputs,” route to `benchmark-evaluation`.
- If the user says “which Alibaba web agent should I use,” route to `webagent-family`.
- If the user asks for “Heavy Mode,” state that the inspected public checkout does not fully expose it; suggest ReAct or a relevant WebAgent family route depending on the task.
- If the user asks to reproduce paper benchmark numbers, make missing model weights, exact prompts/tools, benchmark data, and judge APIs explicit before execution.
