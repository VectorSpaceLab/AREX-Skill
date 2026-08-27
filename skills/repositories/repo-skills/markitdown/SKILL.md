---
name: markitdown
description: "Use MarkItDown to convert documents to Markdown, configure
  cloud/OCR/plugin workflows, and run the local MCP server safely."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# MarkItDown Repo Skill

Use this skill when a task involves Microsoft MarkItDown: converting files or URIs to Markdown for LLM pipelines, choosing optional format extras, using Azure conversion integrations, enabling OCR or third-party plugins, developing plugins, or exposing conversion through the local MCP server.

## Start With The Route

- For ordinary file, stream, URI, stdin, or CLI conversion, read `sub-skills/core-conversion/SKILL.md`.
- For Azure Document Intelligence or Azure Content Understanding conversion, read `sub-skills/cloud-integrations/SKILL.md`.
- For OCR over images embedded in PDF, DOCX, PPTX, or XLSX via `markitdown-ocr`, read `sub-skills/ocr-plugin/SKILL.md`.
- For authoring or debugging third-party MarkItDown plugins, read `sub-skills/plugin-development/SKILL.md`.
- For running `markitdown-mcp` as a local MCP server, Docker service, Claude Desktop server, or Inspector target, read `sub-skills/mcp-server/SKILL.md`.

## Install And Smoke Check

Install the core package plus the extras needed for the requested workflow:

```bash
pip install 'markitdown[pdf,docx,pptx,xlsx,xls,outlook,audio-transcription,youtube-transcription]'
```

Use `markitdown[all]` only when the task truly needs every optional converter, including Azure cloud integrations. Add these package families when needed:

- `pip install markitdown-mcp` for MCP serving.
- `pip install markitdown-ocr` plus an OpenAI-compatible client package for real LLM Vision OCR.
- A custom plugin package with a `markitdown.plugin` entry point for third-party converters.

Run the bundled shared checker from this skill directory when the user asks for an environment or install diagnosis:

```bash
python scripts/check_markitdown_environment.py --check-cli --list-plugins
```

Minimal Python import check:

```python
from markitdown import MarkItDown, StreamInfo

md = MarkItDown()
result = md.convert_stream(
    open("example.md", "rb"),
    stream_info=StreamInfo(extension=".md"),
)
print(result.markdown)
```

For untrusted inputs, prefer the narrowest API that matches the source (`convert_stream`, `convert_local`, `convert_uri`, or `convert_response`) and remember that MarkItDown performs I/O with the privileges of the current process.

## Shared References

- `references/package-overview.md` summarizes the monorepo packages, public entry points, optional extras, and when each sub-skill owns the workflow.
- `references/troubleshooting.md` covers cross-cutting install/import, optional dependency, plugin discovery, cloud credential, security, and system-tool failures.
- `references/repo-provenance.md` records the source snapshot and evidence paths used to create this skill; read it before deciding whether to refresh the skill.
- `references/repo-routing-metadata.json` is structured metadata used by `repo-skills-router` during managed import.

## Workflow Hints

- Choose local/offline conversion first unless the user explicitly asks for Azure cloud extraction, OCR via an LLM, or remote URI fetching.
- Use stream hints (`StreamInfo` or CLI `--extension`, `--mime-type`, `--charset`) when converting stdin or bytes without a reliable filename.
- Keep plugin usage explicit: install the plugin package, verify `markitdown --list-plugins`, then use `--use-plugins` or `MarkItDown(enable_plugins=True)`.
- Treat MCP and cloud modes as security-sensitive because they can read local files or fetch network resources with the process privileges.
- Do not make cloud, LLM, network, server, or Docker calls unless the user has supplied the necessary endpoints/credentials/files and explicitly wants that side effect.

## Common Task Routing

| User request | Read |
| --- | --- |
| "Convert this PDF/DOCX/XLSX/HTML/ZIP to Markdown" | `sub-skills/core-conversion/SKILL.md` |
| "Why does MarkItDown say missing dependency or unsupported format?" | `sub-skills/core-conversion/references/troubleshooting.md` |
| "Use Azure Document Intelligence or Content Understanding" | `sub-skills/cloud-integrations/SKILL.md` |
| "Extract text from screenshots inside a PDF or Office file" | `sub-skills/ocr-plugin/SKILL.md` |
| "Build a MarkItDown plugin for a new file type" | `sub-skills/plugin-development/SKILL.md` |
| "Expose MarkItDown to Claude Desktop or an MCP client" | `sub-skills/mcp-server/SKILL.md` |
| "Check whether this install has MarkItDown, plugins, and CLIs" | `scripts/check_markitdown_environment.py` |

## Safety Boundaries

- Do not hard-code Azure endpoints, API keys, bearer tokens, OpenAI keys, or private file paths into generated code or examples.
- Do not bind `markitdown-mcp` to non-loopback interfaces unless the user accepts that the server has no authentication and can read files/network resources available to its process.
- Do not preserve data URIs with `--keep-data-uris` unless the downstream consumer explicitly needs embedded data; it can make Markdown very large.
- Do not run long-lived servers, Docker containers, cloud conversions, real OCR calls, or network fetches as a "smoke test" without explicit user intent.
