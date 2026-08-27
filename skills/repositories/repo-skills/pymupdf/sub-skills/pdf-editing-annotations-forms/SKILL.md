---
name: pdf-editing-annotations-forms
description: "Assemble and edit PDFs with PyMuPDF annotations, redactions,
  links, outlines, widgets, embedded files, optional content, and safe save
  semantics."
disable-model-invocation: true
metadata:
  disco-role: operating
license: AGPL 3.0
---

# PDF Editing, Annotations, and Forms

Use this sub-skill for editing PDFs or building new PDFs from pages and PDF-only objects: page assembly, annotations, redactions, links, outlines, widgets/forms, embedded files, optional content layers, and safe save modes.

## Read or run

- [references/pdf-assembly.md](references/pdf-assembly.md) covers merging, inserting, selecting, deleting, moving, rotating, and optimized saves.
- [references/annotations-redaction.md](references/annotations-redaction.md) covers annotation creation/update and permanent redaction.
- [references/forms-links-outlines-embedded.md](references/forms-links-outlines-embedded.md) covers links, TOC, widgets/forms, embedded files, and optional content.
- [references/troubleshooting.md](references/troubleshooting.md) covers object orphaning, redaction safety, save conflicts, and embedded-file pitfalls.
- Run [scripts/annotate_redact_smoke.py](scripts/annotate_redact_smoke.py) and [scripts/embedded_file_smoke.py](scripts/embedded_file_smoke.py) for safe smokes.

## Safety rules

Redaction is permanent only after `Page.apply_redactions()` and a full save. Never use incremental save for final confidential redaction artifacts. Reopen and verify text/search no longer finds the sensitive phrase. Reacquire Page/Annot/Widget/Link objects after page-tree edits or updates.

