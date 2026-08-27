# GPT Academic Workflow Map

Use this map after the root `SKILL.md` has identified that a request is about GPT Academic. It maps natural user wording to the nearest sub-skill, important evidence, and common output artifacts.

| User intent | Route | Main repo surfaces | Common outputs |
| --- | --- | --- | --- |
| Configure GPT Academic, choose a model, ask questions, compare models, search the web, build a knowledge base, draw Mermaid, save/load chat | `sub-skills/conversation/` | `main.py`, `config.py`, `core_functional.py`, `crazy_functional.py`, `request_llms/`, `shared_utils/`, `docs/features/conversation/`, `docs/models/` | Chat replies, search summaries, rendered Mermaid, conversation archives, knowledge-base answers |
| Translate or read papers, process PDFs/Word/Markdown/LaTeX, query documents, use Arxiv/DOI/Google Scholar/DOC2X/GROBID/NOUGAT | `sub-skills/academic-docs/` | `crazy_functions/PDF_*`, `Latex_*`, `Word_Summary.py`, `Document_Conversation.py`, `Paper_Reading.py`, `Arxiv_Downloader.py`, `docs/features/academic/` | Translated PDF/Markdown/TeX, summaries, QA context, paper-reading report, LaTeX diff PDFs |
| Analyze codebases, generate project summaries, add Python docstrings, analyze notebooks, translate README/Markdown | `sub-skills/programming-code/` | `crazy_functions/SourceCode_*`, `Program_Comment_Gen.py`, `Markdown_Translate.py`, `docs/features/programming/` | Project architecture summaries, function tables, docstring-patched code, notebook reports, translated Markdown |
| Use natural-language plugin dispatch, Void Terminal, Code Interpreter, Commandline Assistant, generated code execution | `sub-skills/agent-tooling/` | `crazy_functions/Void_Terminal.py`, `Commandline_Assistant.py`, `Dynamic_Function_Generate.py`, `docs/features/agents/`, `crazy_functions/vt_fns/` | Routed plugin runs, config edits, generated-and-executed Python, command suggestions or execution logs |
| Generate or understand images, run voice assistant, summarize audio/video, TTS, video resource search, Manim animation | `sub-skills/multimodal-media/` | `crazy_functions/Image_Generate*`, `Audio_*`, `VideoResource_GPT.py`, `Math_Animation_Gen.py`, `docs/use_audio.md`, `docs/use_tts.md`, `docs/features/conversation/image_generation.md` | Images, media summaries, speech input text, TTS audio, media recommendations, animation files |

## Cross-cutting setup sequence

1. Install runtime dependencies in an isolated Python 3.9-3.11 environment. The current repo pins Gradio behavior around `gradio==3.32.15`; if `pkg_resources` is missing, install `setuptools<81`.
2. Put personal settings in `config_private.py` or environment variables. Do not modify `config.py` for secrets unless no better option exists.
3. Validate provider-specific settings before long tasks: model name in `AVAIL_LLM_MODELS`, matching API key, proxy settings, and external services such as SearXNG, DOC2X, Aliyun speech, or TTS.
4. Use `scripts/inspect_runtime.py --repo-root <checkout>` to list available core buttons, plugin groups, configured model names, and important import checks from the current checkout.
5. Use `scripts/check_proxy.py --repo-root <checkout>`, `scripts/check_doc_backends.py --repo-root <checkout>`, or `scripts/check_media_backends.py --repo-root <checkout>` before workflows that depend on network, LaTeX/PDF tools, or media tooling.

## Route escalation rules

- If a task only asks what plugin to click, route to the sub-skill for the domain and use its plugin table.
- If a task asks GPT Academic to choose a plugin from natural language, route to `agent-tooling` and then cross-link to the domain sub-skill that owns the target plugin.
- If a workflow consumes files, first confirm whether the input is an uploaded temporary path, a local server path, a URL, or an identifier such as Arxiv ID/DOI.
- If a workflow requires credentials, remote API quota, downloads, LaTeX, ffmpeg, browser microphone permission, GPU, or external services, treat that as a setup check before launching expensive work.
- For destructive code/document transformations such as Python docstring insertion or config mutation through Void Terminal, require a backup or explicit confirmation from the user before proceeding.