# Package Overview

## Purpose

Read this when deciding which MarkItDown package, extra, command, or sub-skill applies to a task.

## Packages And Entry Points

| Package | Import | Entry points | Use |
| --- | --- | --- | --- |
| `markitdown` | `markitdown` | CLI `markitdown` | Core file/stream/URI/response conversion to Markdown. |
| `markitdown-mcp` | `markitdown_mcp` | CLI `markitdown-mcp` | Local MCP server exposing `convert_to_markdown(uri)`. |
| `markitdown-ocr` | `markitdown_ocr` | plugin entry point `ocr = markitdown_ocr` | LLM Vision OCR for images embedded in PDF/DOCX/PPTX/XLSX conversions. |
| `markitdown-sample-plugin` | `markitdown_sample_plugin` | plugin entry point `sample_plugin = markitdown_sample_plugin` | Reference pattern for authoring MarkItDown plugins. |

## Core Optional Extras

Install only the extras needed for the requested workflow:

| Extra | Use |
| --- | --- |
| `pptx` | PowerPoint conversion via `python-pptx`. |
| `docx` | Word conversion via `mammoth` and `lxml`. |
| `xlsx` | Excel `.xlsx` conversion via `pandas` and `openpyxl`. |
| `xls` | Legacy Excel `.xls` conversion via `pandas` and `xlrd`. |
| `pdf` | PDF conversion via `pdfminer.six` and `pdfplumber`. |
| `outlook` | Outlook `.msg` conversion via `olefile`. |
| `audio-transcription` | Audio transcription helpers via `pydub` and `SpeechRecognition`; system audio tools such as `ffmpeg` may still be needed. |
| `youtube-transcription` | YouTube transcript fetching via `youtube-transcript-api`; network access is required. |
| `az-doc-intel` | Azure Document Intelligence converter dependencies. |
| `az-content-understanding` | Azure Content Understanding converter dependencies. |
| `all` | All optional dependencies; useful for broad inspection but heavier than most user tasks need. |

## Route By Workflow

| Workflow | Primary route | Notes |
| --- | --- | --- |
| Offline conversion with Python or CLI | `sub-skills/core-conversion/SKILL.md` | Includes API signatures, CLI flags, formats, exceptions, and local smoke helper. |
| Azure cloud conversion | `sub-skills/cloud-integrations/SKILL.md` | Requires endpoint, credentials, network, and optional cloud extras. |
| LLM Vision OCR plugin | `sub-skills/ocr-plugin/SKILL.md` | Requires plugin installation and `llm_client`/`llm_model` for real OCR. |
| Custom plugin authoring | `sub-skills/plugin-development/SKILL.md` | Covers `DocumentConverter`, entry points, priority, and discovery. |
| MCP serving | `sub-skills/mcp-server/SKILL.md` | Keep local/loopback by default; route conversion details back to core conversion. |

## Verified Public API Facts

- `MarkItDown.__init__(*, enable_builtins=None, enable_plugins=None, **kwargs)` enables built-in converters by default and plugins only when requested.
- `MarkItDown.convert(source, *, stream_info=None, **kwargs)` dispatches local paths, URI-like strings, `Path`, `requests.Response`, and binary streams to narrower conversion methods.
- `MarkItDown.convert_local`, `convert_stream`, `convert_uri`, and `convert_response` return `DocumentConverterResult`.
- `StreamInfo` carries optional `mimetype`, `extension`, `charset`, `filename`, `local_path`, and `url` hints.
- `DocumentConverterResult(markdown, *, title=None)` exposes `markdown`, optional `title`, and compatibility `text_content`.
- `markitdown` CLI supports output files, stream hints, cloud flags, plugin flags, plugin listing, and data URI preservation.
- `markitdown-mcp` exposes one MCP tool, `convert_to_markdown(uri)`, for `http:`, `https:`, `file:`, and `data:` URIs.

## Dependency Selection Guidance

- For a single known input type, install that format extra instead of `all`.
- For conversion agents that must handle many user uploads, install the common local extras plus cloud/OCR packages only when needed.
- For plugin debugging, install the plugin in the same Python environment that runs MarkItDown; `--list-plugins` only sees installed entry points in that environment.
- For real OCR or cloud conversion, verify credentials and network intent separately from package import success.
