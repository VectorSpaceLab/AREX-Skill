---
name: docling
description: "Use Docling to convert, parse, configure, extract, chunk, serve,
  and maintain document-processing workflows across Python APIs, CLI commands,
  optional pipelines, and repository edits."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Docling

Use this skill when a task involves Docling, the Python SDK and CLI for converting PDFs, Office documents, HTML, Markdown, images, audio/video, XML, CSV, and other sources into `DoclingDocument` for downstream AI workflows.

## Start Here

1. Read `references/install-and-environment.md` when choosing `docling` vs `docling-slim`, optional extras, Python versions, model artifacts, or safe environment checks.
2. Read `references/repo-provenance.md` before deciding whether this skill matches a current checkout or should be refreshed.
3. Read `references/troubleshooting.md` for cross-cutting install/import, optional dependency, model download, CLI/API, remote-service, and repository-edit failures.
4. Use the sub-skill route map below; each sub-skill owns its nearby references and scripts.

## Route Map

| User task | Use sub-skill | Why |
| --- | --- | --- |
| Convert a local file, URL, binary stream, or in-memory Markdown/HTML/DocLang string with Python | `sub-skills/conversion/SKILL.md` | Owns `DocumentConverter`, `convert`, `convert_all`, `convert_string`, `DocumentStream`, limits, headers, and conversion failures. |
| Build or explain `docling` local CLI commands and supported formats | `sub-skills/cli-and-formats/SKILL.md` | Owns `docling convert`, `--from`, `--to`, output directories, image export/fetch modes, and command construction. |
| Tune the standard PDF pipeline, OCR, table structure, accelerators, artifacts, and option models | `sub-skills/pipeline-configuration/SKILL.md` | Owns `PdfPipelineOptions`, OCR/table options, `artifacts_path`, `AcceleratorOptions`, and option validation. |
| Export, serialize, chunk, or post-process an existing `DoclingDocument` | `sub-skills/document-outputs/SKILL.md` | Owns Markdown/JSON/YAML/HTML/Text/DocTags/WebVTT exports, image modes, table extraction, and RAG chunking. |
| Use VLM, ASR/audio-video, enrichments, advanced model backends, GPU/MLX, or offline model prefetch | `sub-skills/advanced-pipelines/SKILL.md` | Owns `VlmPipeline`, `AsrPipeline`, enrichment flags, model catalog decisions, optional extras, and no-download preflights. |
| Call a running docling-serve endpoint or use `docling convert-remote`/service client SDK | `sub-skills/remote-service-client/SKILL.md` | Owns service URL/API key handling, remote CLI, sync/async client, batches, jobs, chunk endpoints, and network-safe checks. |
| Extract structured fields from documents | `sub-skills/extraction/SKILL.md` | Owns `DocumentExtractor`, extraction templates/options/results, and VLM extraction caveats. |
| Modify the Docling repository itself | `sub-skills/repo-maintenance/SKILL.md` | Owns package layout, extras, CLI/docs generation, tests, validation, and repository-specific agent rules. |

## Public Package Facts

- Install the full user package with `pip install docling` for typical users; install `docling-slim` with extras only when intentionally composing a smaller environment.
- Python support in this snapshot is `>=3.10,<4.0`.
- The `docling` CLI exposes local `convert` behavior and remote `convert-remote` behavior; bare `docling SOURCE` routes to local conversion.
- `docling-tools models download` prefetches model artifacts for offline/local use, but it can download large files; do not run it unless the user wants model downloads.
- Core Python APIs include `DocumentConverter`, `DocumentExtractor`, `InputFormat`, `OutputFormat`, pipeline option classes, `HybridChunker`, and `DoclingServiceClient`.

## Safety Defaults

- Do not run model downloads, VLM/ASR inference, remote service calls, network document fetches, or GPU-heavy examples unless the user asks or the workflow explicitly requires them.
- Prefer no-network helpers first: command builders, config preflights, import checks, `--help`, and tiny local fixtures.
- Treat original repository docs, examples, tests, and scripts as evidence only; this skill's runtime instructions and helpers are bundled under this directory.
- For remote model APIs inside a local pipeline, require `enable_remote_services=True`; for docling-serve conversion, route to `remote-service-client`.
- For repository code changes, obey `AGENTS.md`, run focused tests for touched behavior, and run `make validate` before considering the change complete when feasible.

## Bundled Shared Helpers

- `scripts/check_docling_environment.py` checks package importability, CLI availability, optional modules, and common external binaries without converting documents or downloading models.

## Common First Moves

- Python conversion: route to `conversion`, then use `document-outputs` if the user needs Markdown/JSON/HTML/chunking/table files.
- CLI conversion: route to `cli-and-formats`, then use `pipeline-configuration` for OCR/table/model flags or `advanced-pipelines` for VLM/ASR/enrichment choices.
- Remote service: route directly to `remote-service-client`; do not upload documents during preflight unless the user authorizes a live service call.
- Current-checkout edits: route to `repo-maintenance`; do not use public runtime examples as a substitute for repository tests.
