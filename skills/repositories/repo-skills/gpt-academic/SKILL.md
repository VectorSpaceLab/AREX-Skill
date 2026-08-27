---
name: gpt-academic
description: "Operate GPT Academic chat, academic document, code analysis, agent
  tooling, and multimodal media workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# GPT Academic

Use this root skill when a user asks an agent to operate, configure, troubleshoot, or choose workflows inside GPT Academic. Keep the root as a router: load the nearest sub-skill for task depth, and use the root references/scripts only for shared setup, provider routing, and environment checks.

## Fast orientation

GPT Academic is a Gradio app with prompt buttons and plugin groups for:

- text chat, model routing, internet search, multi-model query, RAG, Mermaid, and conversation archives;
- academic PDFs, Arxiv papers, LaTeX projects, Word/Markdown files, paper reading, document QA, DOC2X/GROBID/NOUGAT parser choices;
- programming workflows such as source-code project analysis, notebook analysis, Markdown translation, and Python docstring generation;
- agentic tools such as Void Terminal, Code Interpreter, Commandline Assistant, and dynamic plugin dispatch;
- multimodal image, voice, audio, video, TTS, and animation workflows.

## Install and preflight

From a GPT Academic checkout, use a Python 3.9-3.11 environment and install the repository requirements:

```bash
python -m pip install -r requirements.txt
python -m pip install 'setuptools<81'  # only if gradio imports fail on pkg_resources
python -c "import gradio, toolbox, core_functional, crazy_functional, request_llms.bridge_all; print('gpt_academic imports ok')"
```

Start the UI with the bundled wrapper when you want a local service:

```bash
bash scripts/launch_app.sh --repo-root <checkout>
```

Use `config_private.py` or environment variables for secrets and machine-specific settings. Do not place API keys into shared prompts, generated docs, or test fixtures.

## Route by user intent

| If the user asks about... | Read this sub-skill | Why |
| --- | --- | --- |
| chat, provider setup, `LLM_MODEL`, `AVAIL_LLM_MODELS`, proxy, internet search, SearXNG, multi-model query, RAG, saved chats, Mermaid | `sub-skills/conversation/SKILL.md` | owns core conversation and model/provider operation |
| PDFs, Arxiv, DOI, LaTeX, Word, Markdown, paper reading, PDF QA, translation, DOC2X/GROBID/NOUGAT, Google Scholar, batch file query | `sub-skills/academic-docs/SKILL.md` | owns scholarly and office-document processing |
| source-code project analysis, code explanation, Python docstrings, notebook analysis, README/Markdown translation, file-pattern selection | `sub-skills/programming-code/SKILL.md` | owns code and technical documentation workflows |
| Void Terminal, Code Interpreter, Commandline Assistant, natural-language plugin dispatch, dynamic function generation, config mutation | `sub-skills/agent-tooling/SKILL.md` | owns agent-like control surfaces and safety decisions |
| image generation or understanding, voice assistant, audio/video summary, Edge TTS, SoVITS, Bilibili/video resources, Manim animation | `sub-skills/multimodal-media/SKILL.md` | owns media, speech, and visual workflows |

When a request spans several areas, route first to the workflow that owns the input artifact. Example: a PDF with code appendix starts in `academic-docs`; then cross-link to `programming-code` for code analysis and `conversation` for Mermaid output.

## Shared references

- `references/workflow-map.md` — read when a prompt is ambiguous or crosses several GPT Academic workflow families.
- `references/configuration.md` — read before model/provider, proxy, search, document, media, Azure, vLLM, local-model, or TTS setup.
- `references/api-reference.md` — read when debugging plugin registry names, `toolbox` helpers, `core_functional`, `crazy_functional`, or `request_llms.bridge_all`.
- `references/troubleshooting.md` — read for cross-cutting install/import, Gradio, API-key, proxy, model-name, upload-path, and local-model failures.
- `references/repo-provenance.md` — read before deciding whether this skill is stale for a newer checkout.
- `references/repo-routing-metadata.json` — structured router metadata used by the managed repo-skill importer; do not edit it free-form during normal use.

## Shared scripts

Run these bundled helpers from the generated skill directory, passing the GPT Academic checkout through `--repo-root` when needed:

| Helper | Use |
| --- | --- |
| `scripts/inspect_runtime.py --repo-root <checkout>` | print a no-secret summary of imports, config snapshot, core buttons, plugin groups, and model registry size |
| `scripts/check_proxy.py --repo-root <checkout> --no-network` | inspect masked proxy config without a network call; omit `--no-network` for a small public-IP probe |
| `scripts/check_doc_backends.py --repo-root <checkout>` | inspect PDF/Word/LaTeX/NOUGAT/DOC2X-related imports, commands, and credential presence |
| `scripts/check_media_backends.py --repo-root <checkout>` | inspect media, TTS, speech, ffmpeg, Manim, and optional GPU/service readiness |
| `scripts/launch_app.sh --repo-root <checkout>` | run import preflight and then launch `main.py` from a checkout |

## Safety and backend boundaries

- Remote LLMs, search, Arxiv, DOC2X, Edge TTS, image generation, Azure, and vLLM require network, credentials, or external services; diagnose setup before launching long tasks.
- NOUGAT, local models, SoVITS, and vLLM serving are optional heavy backends. GPU may be recommended, but the core GPT Academic skill remains usable without proving those optional paths.
- Destructive operations include clearing caches/history, inserting Python docstrings, Void Terminal config mutation, generated-code execution, and shell commands. Require explicit user confirmation or a backup plan before those operations.
- Do not tell future agents to open original repo docs or tests as runtime documentation. Use this skill's bundled references and scripts; source tests remain verification evidence only.
