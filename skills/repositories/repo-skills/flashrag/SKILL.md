---
name: flashrag
description: "Use FlashRAG for retrieval-augmented generation research
  workflows: config/data validation, retrieval and index building,
  generation/refinement components, RAG pipelines/method reproduction,
  evaluation, and WebUI setup."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# FlashRAG

Use this skill when a task asks for help with FlashRAG, the Python toolkit for Retrieval-Augmented Generation research, benchmark reproduction, custom RAG pipelines, retriever/index setup, generator/refiner configuration, evaluation, or the FlashRAG UI.

## Start Here

- **Check staleness first**: Read [repo-provenance.md](references/repo-provenance.md) before using this skill with a local checkout; refresh the skill if the commit, dirty state, package version, or public evidence paths changed.
- **Install minimally**: Public package name is `flashrag-dev`; install with `pip install flashrag-dev --pre` or install a checkout with `pip install -e .` when editing the repo.
- **Verify import**: Run `python -c "import flashrag, importlib.metadata as md; print(md.version('flashrag_dev'))"` after install. If metadata lookup fails, try `flashrag-dev` because Python tools normalize underscores and hyphens differently.
- **Check optional dependencies**: Run [check_flashrag_environment.py](scripts/check_flashrag_environment.py) before loading models, building indexes, or launching services.
- **Read troubleshooting**: Use [troubleshooting.md](references/troubleshooting.md) for cross-cutting install/import, optional dependency, data, hardware, credential, and stale-skill failures.

## Route by Task

- **Config, dataset, corpus schemas, and safe input checks**: Use [data-and-config](sub-skills/data-and-config/SKILL.md) for `Config`, `Dataset`, YAML/dict override behavior, JSONL schemas, and validation helpers.
- **Corpus preparation, retrieval, reranking, and index building**: Use [retrieval-and-indexing](sub-skills/retrieval-and-indexing/SKILL.md) for BM25s/Pyserini, dense Faiss, CLIP/multimodal retrieval, Serper/web retrieval, rerankers, and multi-retriever fusion.
- **Generators, prompt templates, refiners, compressors, and judgers**: Use [generation-and-refinement](sub-skills/generation-and-refinement/SKILL.md) for HF/FastChat/vLLM/OpenAI generation, multimodal generators, `PromptTemplate`, refiners, and judgers.
- **End-to-end pipelines and method reproduction**: Use [pipelines-and-methods](sub-skills/pipelines-and-methods/SKILL.md) for quick-start demos, `SequentialPipeline`, active/branching/adaptive/reasoning RAG, multimodal RAG, and experiment-runner planning.
- **Evaluation metrics and WebUI**: Use [evaluation-and-webui](sub-skills/evaluation-and-webui/SKILL.md) for `Evaluator`, metrics, prediction parsing, WebUI chat/evaluate setup, and service troubleshooting.

## Capability Map

Read [capability-map.md](references/capability-map.md) when a request spans multiple FlashRAG areas or when you need to choose the right sub-skill owner for a source artifact, helper, or failure mode.

## Safe Workflow Defaults

1. Validate config/data with the data/config helper before running retrieval or pipelines.
2. For retrieval, validate corpus JSONL and build command arguments before starting index construction.
3. For generation or methods, inspect config keys and optional dependency requirements before loading models or contacting APIs.
4. Treat benchmark reproduction, model downloads, vLLM serving, WebUI launch, and large index builds as explicit user-approved runtime actions.
5. Keep API keys, model paths, dataset locations, and machine-specific paths out of generated notes unless the user explicitly asks for local operational commands.

## Optional Dependency Surface

FlashRAG core workflows commonly need `torch`, `transformers`, `PyYAML`, `numpy`, `tqdm`, and related runtime packages. Optional workflows add more constraints:

- Dense retrieval: `faiss` plus embedding model packages.
- BM25 retrieval: `bm25s` for lightweight CPU use, or `pyserini` plus Java for Lucene-backed indexes.
- Generator acceleration: `vllm` requires a compatible PyTorch/CUDA stack.
- OpenAI generation or LLMJudge-style evaluation: `openai`, `tiktoken`, and credentials.
- Multimodal RAG: image packages and model-specific utilities such as Qwen-VL helpers.
- WebUI: service/UI dependencies such as Streamlit or Gradio plus valid model/index configs.

## When Editing a FlashRAG Checkout

- Prefer focused changes in the owning module and update nearby docs/examples when public behavior changes.
- Use package source and installed-package inspection to confirm APIs; docs/examples show intended workflows but source resolves defaults and edge behavior.
- If modifying public config keys, retriever/generator factories, pipeline names, or metric names, refresh this skill after the code change so routing and references stay aligned.
