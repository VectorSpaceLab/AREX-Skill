# Conversation Workflows

## Purpose

Read this when a GPT Academic task is text-first and does not primarily involve a paper/document, codebase, generated-code execution, or media input.

## Core chat and prompt buttons

GPT Academic exposes basic prompt buttons from `core_functional.get_core_functions()`. Verified public buttons include academic prose polishing, grammar checking, Chinese/English translation, bidirectional academic translation, code explanation, image lookup, and reference-to-BibTeX conversion.

Typical flow:

1. Put the user's text, URL, or short file-derived excerpt in the main input.
2. Select the default model or a configured model from the toolbar.
3. Click the relevant basic button or submit directly.
4. If the output should be saved, use the conversation save plugin rather than copying raw browser state.

## Internet search

Use `查互联网后回答` when the user needs fresh web evidence. Check:

- `USE_PROXY` and `proxies` for blocked destinations;
- `SEARXNG_URLS` for search backends;
- `JINA_API_KEY` only when the search/extraction path uses Jina;
- model token budget, because search results can be long.

Expected output is a summarized answer with citations or search-result snippets. If SearXNG returns 429 or poor results, switch to a private SearXNG endpoint, simplify the query, or ask the user to provide URLs.

## Multi-model query

Use `询问多个GPT模型` for side-by-side model comparison. For manual model selection, configure `MULTI_QUERY_LLM_MODELS` and ensure every listed model also appears in `AVAIL_LLM_MODELS` with the correct provider key.

Use this when the user wants confidence comparison, provider fallback, or model quality comparison. Do not use it just to make a single answer slower or more expensive.

## RAG and knowledge base

The conversation group includes RAG/knowledge-base plugins such as `构建知识库`, `知识库文件注入`, and `Rag智能召回`.

Before use:

1. Confirm the files are available to the GPT Academic server, not just to the browser.
2. Check embedding model/provider settings and OpenAI/Azure embedding credentials.
3. Keep input files small enough for LlamaIndex readers and vectorization; split or convert large files first.
4. After building/injecting, ask targeted questions that reference the knowledge base.

If the user primarily asks over PDFs or scholarly files, start in `academic-docs`; use RAG only when they want a persistent reusable knowledge base.

## Conversation history and Mermaid

Use `保存当前的对话` to export a conversation and `载入对话历史存档` to restore one. History files are server-side artifacts; if a browser upload path expires, ask the user to re-upload.

Use Mermaid workflows when the user asks for diagrams, flowcharts, sequence charts, mind maps, or visual summaries from the current conversation or a supported file. For paper/document diagrams, route to `academic-docs` first to extract content, then use Mermaid output here.
