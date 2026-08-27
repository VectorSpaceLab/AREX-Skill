---
name: document-processing
description: "Guides OWL DocumentProcessingToolkit workflows for local files,
  web pages, structured data, images, spreadsheets, archives, and optional
  extraction services."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# OWL Document Processing

Use this route when OWL must extract content from a local path or URL before a
worker reasons over it. The route distinguishes deterministic local handling
from model-backed, browser-backed, credentialed, or networked extraction.

## Workflow

1. Run [probe_document_input.py](scripts/probe_document_input.py) against the
   path or URL. It never opens a URL and reports likely prerequisites.
2. For local JSON, JSONL, JSON-LD, XML, or Python files, validate encoding and
   size first. Preserve structured output when the caller needs machine-readable
   values; do not assume every parser returns Markdown.
3. Construct `DocumentProcessingToolkit` with a cache directory and an
   explicit model when the caller has a suitable model backend. See
   [api-reference.md](references/api-reference.md) for signatures and
   [data-and-remote-inputs.md](references/data-and-remote-inputs.md) for
   local/remote routing. In the current CAMEL
   runtime, omitting the model can cause the image sub-tool to construct a
   default provider backend and demand `OPENAI_API_KEY`, even for a later local
   non-image path.
4. Call `extract_document_content(document_path)` and inspect the boolean
   success value before using the content. Route Excel to CAMEL's Excel toolkit
   and images to the image-analysis toolkit rather than treating their output
   as plain text.
5. For webpages, expect the Firecrawl path when `FIRECRAWL_API_KEY` is set;
   otherwise the implementation falls back to Crawl4AI. Treat both as
   network/browser operations and check the returned text for an empty-content
   or error message.
6. For ZIP input, use an isolated cache directory and inspect the returned file
   list. Do not extract untrusted archives into a project or system directory.

## Boundaries

This sub-skill documents the document surface, not model/provider assembly.
Read [workforce-workflows](../workforce-workflows/SKILL.md) for provider
credentials and worker tool assignment. Read
[gaia-evaluation](../gaia-evaluation/SKILL.md) for benchmark attachment
semantics. Read [troubleshooting.md](references/troubleshooting.md) before
retrying a parser, network, or credential failure.

## Output contract

The public method returns a two-item tuple `(success, content)`. A false result
is an operational failure, not an empty successful document. Local JSON/Python
handling is deterministic; other formats may depend on parser packages,
external binaries, model capabilities, network services, or content type
probes. Do not promise lossless extraction from arbitrary PDFs, office files,
or JavaScript-rendered pages.
