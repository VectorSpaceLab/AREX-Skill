# PyMuPDF Cross-Cutting Troubleshooting

## Install and import failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'pymupdf'` | PyMuPDF is not installed in the active Python environment | Run `python -m pip install --upgrade pymupdf`; verify with `python -c "import pymupdf; print(pymupdf.__version__)"`. |
| `ModuleNotFoundError: No module named 'frontend'` after `import fitz` | Unrelated PyPI package named `fitz` shadows PyMuPDF's deprecated compatibility import | Change code to `import pymupdf`; if legacy code cannot change, uninstall unrelated `fitz` and reinstall PyMuPDF. |
| Windows DLL import errors | Missing/incompatible Microsoft Visual C++ runtime or unsupported Python distribution | Reinstall the supported Visual C++ Redistributable and use a Python/wheel combination PyMuPDF supports. |
| Pip compiles PyMuPDF unexpectedly | No compatible wheel or old pip | Upgrade pip, confirm wheel support, or intentionally prepare a C/C++ source-build environment. |
| Custom/system MuPDF build behaves differently | MuPDF version/config differs from PyMuPDF's expected build | Prefer the PyMuPDF wheel/default bundled MuPDF build unless the task is explicitly maintainer-level. |

## Runtime capability surprises

- OCR requires Tesseract and language data; base import success does not verify OCR.
- Office documents require PyMuPDF Pro and licensing; core PyMuPDF is not enough.
- `Table.to_pandas()` requires pandas; use `Table.extract()` or `Table.to_markdown()` when pandas is absent.
- `Pixmap.pil_*` helpers require Pillow; use direct Pixmap output where possible.
- Empty text usually means image-only pages, simulated vector text, clipping/flags, or missing OCR. Garbled/out-of-order text usually points to PDF content order, font encodings, columns, or obfuscation.

## Save, redaction, and object-lifetime hazards

- Use full saves to explicit new output paths for cleanup, conversion, encryption changes, and confidential redaction artifacts.
- Never use incremental save for final redaction outputs; previous content can remain in file history.
- After applying redactions, full-save with garbage collection, reopen the output, and verify text/search no longer finds the sensitive content.
- Page-tree edits can orphan existing `Page`, `Annot`, `Widget`, `Link`, `Table`, and `TextPage` objects. Reacquire objects after insert/delete/select/move/reopen/update operations.
- If `doc.needs_pass` is true, authenticate before page work; `doc.authenticate(password) == 0` is failure.

## Self-containment rule

Do not ask a future agent to open the original PyMuPDF checkout's docs, examples, tests, or scripts for ordinary package use. Use this skill's bundled references and scripts. Original tests and examples are verification evidence, not runtime dependencies.
