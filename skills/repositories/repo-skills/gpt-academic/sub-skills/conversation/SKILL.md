---
name: conversation
description: "Operate GPT Academic chat, model routing, search, RAG, Mermaid,
  and conversation history workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# Conversation

Use this sub-skill for GPT Academic's text-first workflows: ordinary chat, built-in prompt buttons, model/provider selection, proxy setup, internet search, multi-model comparison, RAG/knowledge base, Mermaid generation, URL extraction, and saving/loading chat history.

## Trigger phrases

Read this sub-skill when the user mentions any of:

- `LLM_MODEL`, `AVAIL_LLM_MODELS`, API keys, proxy, OpenAI-compatible endpoint, Azure, Ollama, vLLM, local model, DashScope/Qwen, DeepSeek, GLM, Claude, Gemini;
- “chat with GPT Academic”, “ask multiple models”, “web search”, “SearXNG”, “Jina”, “RAG”, “knowledge base”, “conversation archive”, “save chat”, “load chat”, “Mermaid”, “draw a mind map”, or “URL input”;
- core prompt buttons such as academic polish, grammar check, Chinese/English translation, code explanation, reference-to-BibTeX, or image lookup.

## First decisions

1. Confirm whether the task is normal chat, provider setup, search, RAG, conversation persistence, or a visualization/output-format task.
2. Check the shared root `references/configuration.md` for provider and proxy settings before diagnosing live model failures.
3. Use the bundled plugin listing script when the exact plugin/button name matters:

```bash
python sub-skills/conversation/scripts/list_conversation_plugins.py --repo-root <checkout> --group 对话
```

4. If the prompt involves documents, code projects, agentic execution, or media inputs, route to the owning sibling sub-skill rather than stretching conversation guidance.

## Workflow routes

| User goal | Primary GPT Academic surface | Read next |
| --- | --- | --- |
| normal chat or built-in prompt transforms | submit button plus `core_functional` prompt buttons | `references/workflows.md` |
| model/provider setup or model-dropdown issue | `LLM_MODEL`, `AVAIL_LLM_MODELS`, provider key config, `request_llms.bridge_all` | `references/model-routing.md` and root `references/configuration.md` |
| web search answer | `查互联网后回答`, SearXNG/Jina/proxy config | `references/workflows.md` and `references/troubleshooting.md` |
| multi-model comparison | `询问多个GPT模型` or manual model list | `references/model-routing.md` |
| RAG / knowledge base | `构建知识库`, `知识库文件注入`, `Rag智能召回` | `references/workflows.md` |
| save/load/export chat | `保存当前的对话`, `载入对话历史存档` | `references/workflows.md` |
| Mermaid or mind-map output | Mermaid plugin or core summarization/mind-map prompt | `references/workflows.md` |

## Boundaries

- Route PDFs, Arxiv, LaTeX, Word, paper reading, and batch document QA to `../academic-docs/SKILL.md`.
- Route source-code project analysis, notebooks, README/Markdown translation, and docstring insertion to `../programming-code/SKILL.md`.
- Route Void Terminal, Code Interpreter, natural-language plugin dispatch, command execution, and config mutation to `../agent-tooling/SKILL.md`.
- Route image/audio/video/TTS/animation workflows to `../multimodal-media/SKILL.md`.

## Troubleshooting quick checks

- Run `scripts/inspect_runtime.py --repo-root <checkout>` from the root skill for imports, plugin groups, and model registry size.
- Run `scripts/check_proxy.py --repo-root <checkout> --no-network` before remote provider or search debugging.
- Use `references/troubleshooting.md` here for conversation-specific failure modes and root `references/troubleshooting.md` for install/import issues.
