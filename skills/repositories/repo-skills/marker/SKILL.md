---
name: marker
description: "Use Marker to convert documents, configure pipelines, run LLM
  extraction, and operate app/server deployment surfaces."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Marker Repo Skill

Use this repo skill when a user asks about Marker, `marker-pdf`, `marker_single`, `marker`, document-to-markdown/JSON/HTML/chunks conversion, OCR/table conversion, structured extraction, Marker LLM services, custom Marker processors/renderers/providers, or Marker app/server deployment.

## Start Here

1. Confirm the user wants the open-source Marker package, distributed as `marker-pdf` and imported as `marker`.
2. For a fresh environment, install the base package first:

   ```bash
   pip install marker-pdf
   ```

3. Install `marker-pdf[full]` only when converting non-PDF document families such as DOCX, PPTX, XLSX, HTML, or EPUB.
4. Run a safe environment probe before heavy conversion, model downloads, or service launch:

   ```bash
   python scripts/marker_environment_check.py --check-cli
   ```

5. Route to the focused sub-skill below, then use its nearest references/scripts for commands, API examples, validation, and troubleshooting.

## Route By Task

| User task | Read |
| --- | --- |
| Convert one PDF/image or a folder, choose output format, use Python API, run table-only/OCR-only conversion, parse outputs, tune workers/device | `sub-skills/conversion-cli-api/SKILL.md` |
| Explain or change `config_json`, `ConfigParser`, `--processors`, `--converter_cls`, providers, builders, processors, renderers, schema/debug output | `sub-skills/configuration-extension/SKILL.md` |
| Enable `--use_llm`, select Gemini/Vertex/Ollama/Claude/OpenAI/Azure services, build structured extraction schemas, troubleshoot LLM JSON/retry/key failures | `sub-skills/llm-extraction-services/SKILL.md` |
| Run `marker_server`, call FastAPI endpoints, use `marker_gui`/`marker_extract`, adapt Modal deployment, build client templates | `sub-skills/server-deployment/SKILL.md` |

## Shared References

- `references/install-and-environment.md`: install variants, optional dependencies, backend/device checks, model/download cautions, and package identity.
- `references/troubleshooting.md`: cross-cutting install/import, optional dependency, device, model/cache, credential, and workflow routing failures.
- `references/benchmark-notes.md`: performance and benchmark context without making benchmark scripts a runtime dependency.
- `references/repo-provenance.md`: source snapshot and evidence paths used to generate this skill.
- `references/repo-routing-metadata.json`: structured routing metadata for DisCo import.

## Safety Defaults

- Do not run document conversion, model downloads, server processes, Streamlit apps, Modal deploys, or external LLM calls unless the user explicitly asks.
- Prefer `--help`, dry-run config probes, schema validation, and small fixture checks before heavy conversion.
- Treat original repo examples/tests as evidence only; this skill bundles its own references and scripts for future use.
- Keep API keys and local environment paths out of generated code, prompts, logs, and shared examples.
