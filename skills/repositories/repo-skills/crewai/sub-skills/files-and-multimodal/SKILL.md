---
name: files-and-multimodal
description: "Guides agents handling CrewAI crewai-files, input_files, file
  source resolution, multimodal agents, provider file constraints, upload
  caches, and file or document tool adjacency."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Files and Multimodal

Use this sub-skill when a task involves CrewAI file inputs, `crewai-files`, images, PDFs, audio, video, text files, `input_files`, multimodal agents, provider file formatting, upload behavior, or deciding whether to use native file inputs versus file/document tools.

## Route First

- For `File`, `ImageFile`, `PDFFile`, `AudioFile`, `VideoFile`, `TextFile`, `FilePath`, `FileUrl`, `FileBytes`, `FileResolver`, `input_files`, and prompt key patterns, read [references/file-inputs.md](references/file-inputs.md).
- For provider support, MIME/type limits, OpenAI Responses versus completions behavior, Bedrock/Gemini/Anthropic formatting, and file handling modes, read [references/provider-constraints.md](references/provider-constraints.md).
- For inline versus URL versus upload delivery, `prefer_upload`, `UploadCache`, cleanup helpers, and safe cache expectations, read [references/uploaders-and-cache.md](references/uploaders-and-cache.md).
- For missing optional dependencies, unsupported MIME types, URL/path confusion, base64 misuse, upload cleanup, and multimodal flag migration, read [references/troubleshooting.md](references/troubleshooting.md).
- To inspect local paths, safe URL metadata, data URIs, base64 inputs, and provider constraints without LLM calls, uploads, credentials, or network fetches, run [scripts/check_file_inputs.py](scripts/check_file_inputs.py) with `--help` first.

## Boundaries

- Stay here for native CrewAI file inputs, `crewai-files` classes, file source coercion, provider file constraints, multimodal `Agent`/`Crew`/`Task` input wiring, upload cache behavior, and adjacent file/document tool decisions.
- Use [../tools-and-mcp/SKILL.md](../tools-and-mcp/SKILL.md) for official `crewai_tools` document tools such as `FileReadTool`, `DirectoryReadTool`, `PDFSearchTool`, `CSVSearchTool`, `JSONSearchTool`, OCR, custom tools, and MCP tool routing.
- Use [../memory-knowledge-and-rag/SKILL.md](../memory-knowledge-and-rag/SKILL.md) for knowledge sources, RAG loaders, embeddings, vector stores, and retrieval/search architectures built on documents.
- Use [../llm-and-providers/SKILL.md](../llm-and-providers/SKILL.md) for provider credentials, model selection, base URLs, API variants, streaming, and general LLM compatibility beyond file payload constraints.
- Use [../core-runtime/SKILL.md](../core-runtime/SKILL.md) for ordinary `Agent`, `Task`, `Crew`, process, kickoff, callback, guardrail, and output design when files are not the central issue.
- Return to [../../SKILL.md](../../SKILL.md) when a request spans CrewAI project routing, CLI setup, tools, RAG, providers, and file inputs together.

## Safe Defaults

- Prefer native `input_files` with typed `crewai_files` objects for model-readable file payloads; prefer file/document tools when the agent should browse or search local documents during tool use.
- Validate MIME type, provider support, and size limits before a real kickoff; small local fixtures are safer than large PDFs, videos, or remote URLs during debugging.
- Treat uploads as side-effectful provider operations; do not enable `prefer_upload=True` unless the user has approved credentials, retention assumptions, and cleanup needs.
- For legacy image URL/path tasks that rely on `multimodal=True`, prefer migrating to native `input_files` where possible; keep `multimodal=True` only when the intended behavior is the built-in image tool path.

## Usability Targets

- Validate mixed local path, URL, and data-URI/base64 inputs for OpenAI Responses versus Bedrock constraints without triggering network, upload, or LLM calls.
- Diagnose why MIME detection falls back to `application/octet-stream`, why a provider rejects a PDF/audio/video file, or why a non-native file path is handled by a file tool instead of the LLM payload.
