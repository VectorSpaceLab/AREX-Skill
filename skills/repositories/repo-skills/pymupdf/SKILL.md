---
name: pymupdf
description: "Use PyMuPDF for document opening, text/table/RAG extraction,
  rendering, image and graphics work, PDF editing, annotations, forms, CLI
  checks, and maintenance triage."
disable-model-invocation: true
metadata:
  disco-role: operating
license: AGPL 3.0
---

# PyMuPDF Repo Skill

Use this skill when a task involves the **PyMuPDF** package (`import pymupdf`) for PDF and document processing: opening or converting documents, extracting text/tables/images, rendering pages, editing PDFs, adding annotations/forms/redactions, using the `pymupdf` CLI, or diagnosing PyMuPDF install/build/runtime issues.

Prefer `import pymupdf` in all new code. Treat `import fitz` as deprecated compatibility only; an unrelated package named `fitz` can break legacy imports.

## Install and minimal check

```bash
python -m pip install --upgrade pymupdf
python - <<'PY'
import pymupdf
print(pymupdf.__version__)
doc = pymupdf.open()
page = doc.new_page(width=200, height=100)
page.insert_text((36, 60), "PyMuPDF ok")
assert pymupdf.open(stream=doc.tobytes(), filetype="pdf")[0].get_text().strip() == "PyMuPDF ok"
PY
```

PyMuPDF has no mandatory runtime Python dependencies when a wheel is available. Source builds need C/C++ tooling and build MuPDF; read [references/troubleshooting.md](references/troubleshooting.md) and [references/optional-dependencies.md](references/optional-dependencies.md) before choosing that path.

## Route by task

| Task intent | Read first |
| --- | --- |
| Open files or bytes, create PDFs, authenticate, inspect metadata/TOC, convert supported inputs to PDF, choose safe save modes, reason about `Rect`/`Point`/`Matrix`/`Quad` | [sub-skills/document-core/SKILL.md](sub-skills/document-core/SKILL.md) |
| Extract text, words, blocks, dict/rawdict layout, search text, detect/extract tables, prepare Markdown/JSON/plain text for RAG, understand OCR/PyMuPDF4LLM boundaries | [sub-skills/text-tables-and-rag/SKILL.md](sub-skills/text-tables-and-rag/SKILL.md) |
| Render pages, thumbnails, clips, alpha/color spaces, Pixmaps, embedded image extraction/insertion, image masks, drawing/vector graphics, Story/TextWriter visual layout | [sub-skills/rendering-images-and-graphics/SKILL.md](sub-skills/rendering-images-and-graphics/SKILL.md) |
| Merge/reorder PDFs, annotations, permanent redaction, links, outlines, widgets/forms, embedded files, optional content groups, save semantics for edits | [sub-skills/pdf-editing-annotations-forms/SKILL.md](sub-skills/pdf-editing-annotations-forms/SKILL.md) |
| Use `pymupdf` / `python -m pymupdf`, CLI subcommands, safe CLI smoke checks, wheel/source-build triage, optional component checks, focused maintainer tests | [sub-skills/cli-and-maintenance/SKILL.md](sub-skills/cli-and-maintenance/SKILL.md) |

## Root references and scripts

- Read [references/optional-dependencies.md](references/optional-dependencies.md) before relying on OCR, PyMuPDF4LLM, PyMuPDF Pro, Pillow, fontTools, pandas/tabulate, source builds, or maintainer-only tooling.
- Read [references/troubleshooting.md](references/troubleshooting.md) for cross-cutting install/import, wheel/source-build, legacy `fitz`, optional dependency, save/authentication, and self-containment failures.
- Read [references/repo-provenance.md](references/repo-provenance.md) before deciding whether this skill is current for a PyMuPDF checkout or before running a refresh.
- `references/repo-routing-metadata.json` contains structured metadata for managed repo-skill routing.
- Run [scripts/check_pymupdf_env.py](scripts/check_pymupdf_env.py) for a safe installed-package import/version/CLI/API/optional-component check.
- Run [scripts/create_sample_pdf.py](scripts/create_sample_pdf.py) when another recipe needs a deterministic tiny PDF fixture without using external files.

## Default decisions

1. For ordinary user code, start with a wheel install (`python -m pip install --upgrade pymupdf`) and `import pymupdf`.
2. Use the smallest owning sub-skill: text/table/RAG work should not be solved by rendering unless pixels are truly needed; image extraction should not rasterize full pages unless the visual page appearance is the desired output.
3. Use full saves to explicit new paths for transformations, cleanup, encryption changes, and all confidential redaction outputs. Use incremental saves only when intentionally appending to the same PDF and after the editing sub-skill's checks.
4. Treat Tesseract OCR, PyMuPDF4LLM, PyMuPDF Pro, Pillow, fontTools, `pymupdf-fonts`, pandas, and tabulate as optional until verified in the active runtime.
5. Never make a future workflow depend on the PyMuPDF repository checkout's docs, examples, tests, or scripts. Use the bundled references and scripts in this skill tree instead.

## Version baseline

This skill was generated for PyMuPDF package version `1.28.2` from a source snapshot recorded in [references/repo-provenance.md](references/repo-provenance.md). If the installed package or checkout differs substantially, run `refresh-repo-skill` before trusting API details that changed across versions.
