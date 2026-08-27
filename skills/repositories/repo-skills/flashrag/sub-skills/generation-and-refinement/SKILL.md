---
name: generation-and-refinement
description: "Use FlashRAG generators, prompt templates, OpenAI/vLLM/HF/FastChat
  backends, multimodal generation, refiners/compressors, and judgers as reusable
  components."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Generation and Refinement

Use this sub-skill when a task asks you to configure, instantiate, call, or debug FlashRAG generation-side components rather than build indexes, assemble full RAG methods, or report final metrics.

## Route by Task

- **Text generation**: Use `flashrag.utils.get_generator(config)` and `generator.generate(...)`; see [generator-api.md](references/generator-api.md).
- **Prompt construction**: Use `flashrag.prompt.PromptTemplate` to convert questions, retrieval results, messages, and previous generations into backend-ready strings or chat messages; see [generator-api.md](references/generator-api.md).
- **Backend selection**: Choose `framework: hf`, `vllm`, `fschat`, or `openai`, then align model paths, credentials, optional packages, and `generation_params`; see [model-and-backend-options.md](references/model-and-backend-options.md).
- **Multimodal generation**: Use HF-backed multimodal generators with message blocks containing text and image content; see [model-and-backend-options.md](references/model-and-backend-options.md).
- **Refiners and compressors**: Use `flashrag.utils.get_refiner(config)` or a concrete refiner to compress retrieved documents or prompts; see [refiner-and-judger.md](references/refiner-and-judger.md).
- **Judgers**: Use `flashrag.utils.get_judger(config)` when a pipeline needs a component that decides whether or how strongly to retrieve; see [refiner-and-judger.md](references/refiner-and-judger.md).
- **Preflight checks**: Run the bundled safe checker before loading large models or calling APIs: `python skills/flashrag/sub-skills/generation-and-refinement/scripts/inspect_generation_config.py path/to/config.yaml`; see [troubleshooting.md](references/troubleshooting.md).

## Boundaries

This sub-skill owns generator, prompt, refiner, compressor, and judger components. For retrieval model setup, index files, corpus processing, and reranking, use the retrieval/indexing sub-skill. For complete methods such as Self-RAG, FLARE, Adaptive-RAG, Trace, or end-to-end experiment scripts, use the pipelines/methods sub-skill. For evaluation metrics or WebUI behavior, use the evaluation/WebUI sub-skill.

## Safety Notes

- Do not paste real OpenAI or Azure credentials into examples, reports, or generated configs; use placeholders or environment variables.
- Treat `generator_model_path`, `refiner_model_path`, and judger model paths as user-supplied model identifiers or local paths; validate intent before downloading or loading large models.
- The bundled inspector is static and does not import FlashRAG, load models, download tokenizers, or make API calls.
