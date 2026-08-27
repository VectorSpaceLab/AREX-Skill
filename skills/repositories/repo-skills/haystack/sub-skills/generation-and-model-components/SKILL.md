---
name: generation-and-model-components
description: "Choose and configure Haystack prompt builders, generators,
  embedders, classifiers, samplers, validators, and provider/model-backed
  components."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Generation and Model Components

Use this sub-skill when the task is about model-facing Haystack components: prompt construction, text or chat generation, embeddings, local/API provider setup, model-backed classification, answer formatting, sampling, JSON validation, credentials, streaming, or optional model dependencies.

## Route Here

- Build prompts with `PromptBuilder` or `ChatPromptBuilder`, including Jinja variables, chat-message templates, runtime template overrides, and required variables.
- Select generators or chat generators such as `OpenAIChatGenerator`, `AzureOpenAIChatGenerator`, `HuggingFaceAPIChatGenerator`, `HuggingFaceLocalChatGenerator`, `OpenAIGenerator`, `AzureOpenAIGenerator`, and Hugging Face local/API text generators.
- Configure embedders for model-backed query/document embeddings, including OpenAI, Azure OpenAI, Hugging Face API, Sentence Transformers, sparse, dense, local, and async variants.
- Add model-backed classifiers, `TopPSampler`, `AnswerBuilder`, `JsonSchemaValidator`, `Secret`, structured output, and streaming callbacks.
- Debug optional dependency, credential, backend, JSON schema, generation parameter, device, or provider-specific failures.

## Reroute Elsewhere

- For pipeline graph construction, component sockets, custom components, loops, serialization, and breakpoints, use `../pipelines-and-components/SKILL.md`.
- For document stores, retrievers, rankers, RAG retrieval strategy, indexing, and hybrid search, use `../retrieval-and-rag/SKILL.md`.
- For agents, tools, tool invocation, human-in-the-loop, and multi-step orchestration, use `../agents-tools-and-hitl/SKILL.md`.
- For evaluators, tracing, metrics, experiment comparison, and observability, use `../evaluation-and-observability/SKILL.md`.

## Fast Workflow

1. Identify whether the model slot expects `str`, `list[ChatMessage]`, `Document`, or `list[Document]`; choose text generators for `prompt -> replies`, chat generators for `messages -> replies`, embedders for vectors, and classifiers/samplers/validators for post-processing.
2. Use `PromptBuilder` for plain string prompts and `ChatPromptBuilder` for chat models; set `required_variables="*"` or a concrete list when missing variables must fail instead of rendering as empty strings.
3. Use `Secret.from_env_var(...)` for provider credentials and avoid hard-coded tokens; pass model parameters through `generation_kwargs`, `huggingface_pipeline_kwargs`, embedder constructor options, or runtime `run(..., generation_kwargs=...)` overrides.
4. Add `JsonSchemaValidator` or provider structured-output `response_format` when the downstream task needs machine-readable JSON; route `validation_error` back into a correction loop at the pipeline layer.
5. Run `scripts/model_component_smoke_check.py` to verify public imports, prompt rendering, answer extraction, sampling, and JSON validation without network credentials.

## References

- `references/api-reference.md` lists the core component imports, inputs, outputs, and configuration knobs.
- `references/model-and-provider-guide.md` explains provider selection, credentials, optional dependencies, local devices, streaming, and structured outputs.
- `references/troubleshooting.md` maps common install/import, credential/backend, API misuse, data/config, and workflow failures to fixes.
- `scripts/model_component_smoke_check.py` is a deterministic smoke check for importable public APIs and non-network component behavior.
