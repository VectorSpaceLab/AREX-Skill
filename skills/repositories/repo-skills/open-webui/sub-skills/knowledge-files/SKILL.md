---
name: knowledge-files
description: "Route file, folder, note, memory, knowledge-base, and retrieval
  workflows in Open WebUI."
metadata:
  disco-role: operating
disable-model-invocation: true
license: NOASSERTION
---

# Knowledge and Files

Use this sub-skill for file uploads, folders, notes, memories, knowledge bases, retrieval, RAG, and document-processing workflows in Open WebUI.

## When to use this sub-skill

Use `knowledge-files` when the user asks about:

- uploading, organizing, or processing files
- building knowledge bases or retrieval collections
- notes, folders, or persistent memories
- document ingestion, extraction, chunking, or local search
- RAG-related storage, loader, or file-size problems

## Read these bundled files first

- `references/workflows.md` for the workflow map and data-layout assumptions.
- `references/troubleshooting.md` for file, loader, and retrieval failures.
- `../../references/configuration.md` for shared storage and retrieval-related environment variables.
- `../deployment/references/deployment.md` if the app itself is not running yet.

## Core capabilities

- File upload and processing flows.
- Folder and note organization.
- Memory persistence and retrieval.
- Knowledge-base creation and search.
- Document loader and extraction behavior.
- RAG and retrieval-backend selection.

## Typical user questions

- "How do I upload a document and ask questions about it?"
- "Why is my knowledge base empty after upload?"
- "How do I organize notes or folders?"
- "How do I change retrieval scope or vector backend settings?"
- "Why did a file fail to process or exceed the allowed size?"

## Important boundaries

- Model-provider routing belongs in `chat-models`.
- Plugins, tools, skills, pipelines, and browser/image/audio helpers belong in `extensions`.
- Auth, storage provisioning, channels, calendar, and telemetry belong in `admin-collaboration`, though storage settings may be referenced here when they block file processing.

## Success shape

A future agent should be able to:

1. Explain the file/knowledge data path.
2. Distinguish upload, processing, retrieval, and storage failures.
3. Give concrete steps for fixing unsupported formats or oversized files.
4. Route true storage or auth problems to the admin sub-skill instead of guessing.
