---
name: academic-docs
description: "Operate GPT Academic paper, PDF, Arxiv, LaTeX, Word, Markdown, and
  batch document workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# Academic Documents

Use this sub-skill when a GPT Academic task consumes scholarly or office documents: PDF papers, Arxiv IDs, DOI-like paper requests, LaTeX projects, Word files, Markdown files, Google Scholar pages, batch document folders, or paper-reading prompts.

## Trigger phrases

Read this sub-skill for: “PDF论文翻译”, “ChatPDF”, “PDF QA”, “Arxiv论文翻译”, “速读论文”, “论文摘要”, “LaTeX润色/纠错/翻译”, “Word总结”, “DOC2X”, “GROBID”, “NOUGAT”, “Google Scholar”, “批量文件询问”, “paper reading”, “translate this paper”, or “summarize uploaded documents”.

## First decisions

1. Identify the input kind: uploaded file, server-local path, URL, Arxiv ID, DOI, Google Scholar URL, folder, zip archive, or Markdown/Word/LaTeX project.
2. Decide whether the user needs translation, summarization, QA, proofreading, structure extraction, or batch querying.
3. Check parser/tool readiness before expensive runs:

```bash
python scripts/check_doc_backends.py --repo-root <checkout>
python sub-skills/academic-docs/scripts/check_document_input.py <document-or-folder>
```

4. If model/provider setup fails, return to root `references/configuration.md` or `../conversation/SKILL.md`.

## Route map

| User goal | GPT Academic workflow | Read next |
| --- | --- | --- |
| translate a PDF paper | `PDF论文翻译`; parser order DOC2X → GROBID → traditional | `references/workflows.md`, `references/document-backends.md` |
| ask questions about a PDF | `理解PDF文档内容 （模仿ChatPDF）` | `references/workflows.md` |
| translate Arxiv paper | `Arxiv论文翻译` or LaTeX-backed Arxiv plugins | `references/workflows.md` |
| polish/proofread/translate LaTeX | LaTeX project polish/proofread/translate plugins | `references/workflows.md`, `references/document-backends.md` |
| summarize Word/Markdown/folder | Word summary, Markdown translation, batch file query | `references/workflows.md` |
| formula-heavy PDF OCR | `精准翻译PDF文档（NOUGAT）` | `references/document-backends.md` |
| academic search/paper discovery | Google Scholar assistant or academic conversation | `references/workflows.md` and `../conversation/SKILL.md` |

## Boundaries

- Plain chat, web search, RAG setup, model selection, and Mermaid output belong to `../conversation/SKILL.md` unless a document workflow is the primary input.
- Source-code project analysis and README translation for code repos belong to `../programming-code/SKILL.md`.
- Void Terminal or Code Interpreter dispatch belongs to `../agent-tooling/SKILL.md`.
- Audio/video paper summaries or voice/TTS belong to `../multimodal-media/SKILL.md`.

## Verification anchors

Native candidates include DOC2X parsing, LaTeX auto-correct, Markdown conversion, safe pickle for LaTeX state, and plugin harness examples. Many require network, credentials, LaTeX binaries, or LLM APIs; do not treat skipped optional parser tests as passing.
