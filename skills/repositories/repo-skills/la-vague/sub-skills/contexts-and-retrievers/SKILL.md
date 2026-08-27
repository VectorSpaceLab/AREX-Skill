---
name: contexts-and-retrievers
description: "Choose and validate LaVague provider contexts, credentials, custom
  model objects, cache contexts, and retriever pipelines without making live
  provider or browser calls by default."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# LaVague Contexts and Retrievers

Use this sub-skill when a LaVague task needs provider/model selection, API-key checks, custom LlamaIndex `llm`/`embedding`/`mm_llm` wiring, cache-backed contexts, WorldModel knowledge examples, task `user_data`, or ActionEngine/NavigationEngine retriever selection.

## Route first

- Provider context, credentials, custom models, cache, Cohere rerank, or `RetrieversPipeline`: stay here.
- Browser construction, Selenium/Playwright profiles, browser binaries, screenshots, tabs, iframes, or CAPTCHA/session handling: route to `../browser-drivers/SKILL.md`.
- Full `WebAgent`, `WorldModel`, `ActionEngine`, logs, token counts, or agent run/debug loops: route to `../core-web-agent/SKILL.md` after choosing the context or retriever here.
- Gradio, Chrome extension server, `AgentServer`, or `lavague-serve`: route to `../server-extension-gradio/SKILL.md`.
- `lavague-qa` and `lavague-test`: route to `../qa-and-test-runner/SKILL.md`.

## Fast workflow

1. Pick the provider context from `references/provider-contexts.md`; install the matching optional package if its import is missing.
2. Check required environment variables without printing secret values. For Anthropic and Fireworks, remember that default components still require `OPENAI_API_KEY` for OpenAI embedding or multimodal pieces.
3. Prefer `WorldModel.from_context(context)` and `ActionEngine.from_context(context, driver=driver)` when all three context models should travel together. Pass individual custom LlamaIndex objects only when mixing providers deliberately.
4. Pick a retriever from `references/retriever-reference.md`. Keep the default retriever unless retrieval logs show missing target nodes or a page has unusual markup.
5. Run the bundled safe probe before live work:

```bash
python sub-skills/contexts-and-retrievers/scripts/lavague_context_retriever_probe.py --context all --retriever all --check-env
```

The probe imports modules, inspects constructor signatures, and reports whether required credential variables are present. It does not instantiate providers, contact model APIs, launch browsers, download data, or start servers.

## Common recipes

- OpenAI default: ensure `OPENAI_API_KEY`, then use `OpenaiContext()` or rely on LaVague's default context.
- Azure OpenAI: pass explicit `llm`, `mm_llm`, `deployment`, `endpoint`, and `embedding_deployment`; do not rely on defaults for deployment names.
- Anthropic planning/action with OpenAI embeddings: set both `ANTHROPIC_API_KEY` and `OPENAI_API_KEY`, then use `AnthropicContext()`.
- Gemini all-in-one: set `GOOGLE_API_KEY`, then use `GeminiContext()`.
- Fireworks action/embedding with OpenAI multimodal world model: set `FIREWORKS_API_KEY` and `OPENAI_API_KEY`, then use `FireworksContext()`.
- Cache-driven dry recovery: use `ContextCache` only when prompt/embedding stores are intentionally local and versioned for the run; understand fallback behavior before assuming it is offline.
- Retriever pipeline: compose `InteractiveXPathRetriever(driver)`, `SyntaxicRetriever()`, and `XPathedChunkRetriever()` when you need deterministic XPath marking plus lightweight syntax filtering; add Cohere only when `COHERE_API_KEY` and network/API use are explicitly permitted.

## References

- `references/provider-contexts.md` — provider packages, signatures, environment variables, default-model caveats, and cache stores.
- `references/retriever-reference.md` — retriever classes, default pipeline, Cohere rerank behavior, and selection rules.
- `references/customization-workflows.md` — mixed-provider contexts, `from_context`, `add_knowledge`, task `user_data`, and template snippets.
- `references/troubleshooting.md` — optional-package, API-key, Azure, embedding, cache, Cohere, and NLTK/import issues.

## Safety defaults

Keep provider calls and browser launches opt-in. The examples distilled into this sub-skill originally run live web objectives, but the bundled helper only performs local import/signature/env checks and prints runnable templates. Never store API keys in generated files, logs, or prompt caches.
