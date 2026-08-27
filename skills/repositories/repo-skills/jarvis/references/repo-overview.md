# JARVIS repo overview

## Purpose

Read this first when you want a quick map of the JARVIS repository family. It tells you which subproject owns each workflow, what kind of inputs it expects, and where to go next without reopening the source checkout.

## The three subprojects

### HuggingGPT / JARVIS chat orchestration

Owns the multimodal agent loop:

- task planning
- model selection
- task execution against expert models
- response generation

It exposes CLI, server, `/hugginggpt`, `/tasks`, `/results`, Gradio-style, and web-client workflows. Most user requests about chat orchestration, config files, endpoint routing, credentials, or local-vs-remote inference belong here.

### EasyTool

Owns concise tool-instruction generation and evaluation for:

- FuncQA
- ToolBench
- ToolBench retrieval
- RestBench

It is script-heavy and benchmark-oriented. Most requests involve `main.py`, progress files, external tool code, API keys, or data preparation.

### TaskBench

Owns task-automation benchmark data, inference, evaluation, graph construction/sampling, formatting, and Back-Instruct generation.

It is the right route for metric computation, dataset/domain layout, prediction JSONL, and graph-tool utilities.

## Shared patterns across the repository

- **External credentials matter**. HuggingGPT needs OpenAI/Hugging Face/Azure values; EasyTool needs OpenAI and sometimes RapidAPI; TaskBench inference and data generation need an OpenAI-compatible endpoint and API key.
- **No single package install exists** for the whole repository. Each subproject has its own runtime requirements and side-effect profile.
- **Remote vs local is a real boundary**. HuggingGPT remote/lite mode is very different from the local model-server stack.
- **Benchmark data is not runtime content**. The dataset and fixture files are evidence for the generated skill, not files future agents should expect to mutate in place.

## Where to go next

- For a quick, safe repository sanity check, run the bundled root helper described in `SKILL.md`.
- For workflow-specific commands, data layouts, and troubleshooting, follow the owning sub-skill and its bundled references/scripts.
