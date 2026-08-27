#!/usr/bin/env python3
"""Classify a document/folder input before a GPT Academic academic-docs workflow."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

PDF = {".pdf"}
WORD = {".docx", ".doc"}
MARKDOWN = {".md", ".markdown", ".mmd"}
LATEX = {".tex", ".bib", ".sty", ".cls"}
ARCHIVE = {".zip", ".tar", ".gz", ".tgz", ".rar", ".7z"}


def classify(path: Path):
    if not path.exists():
        return {"path": str(path), "exists": False, "error": "path does not exist on the GPT Academic server"}
    if path.is_dir():
        counts = {}
        for child in path.rglob("*"):
            if child.is_file():
                counts[child.suffix.lower() or "<none>"] = counts.get(child.suffix.lower() or "<none>", 0) + 1
        suggestions = ["批量文件询问", "Word/PDF/Markdown workflows by suffix"]
        if any(s in counts for s in LATEX):
            suggestions.append("LaTeX project polish/proofread/translate")
        return {"path": str(path), "exists": True, "kind": "directory", "suffix_counts": counts, "suggested_workflows": suggestions}
    suffix = path.suffix.lower()
    workflows = []
    warnings = []
    if suffix in PDF:
        workflows += ["PDF论文翻译", "批量总结PDF文档", "理解PDF文档内容（ChatPDF）"]
        warnings.append("If scanned or formula-heavy, consider OCR/NOUGAT/DOC2X/GROBID choices.")
    elif suffix in WORD:
        workflows.append("批量总结Word文档")
        if suffix == ".doc":
            warnings.append("Legacy .doc may need conversion to .docx outside Windows.")
    elif suffix in MARKDOWN:
        workflows += ["Markdown翻译", "批量文件询问"]
    elif suffix in LATEX:
        workflows += ["LaTeX proofread/polish/translate"]
        warnings.append("Compiled outputs need pdflatex and sometimes latexdiff.")
    elif suffix in ARCHIVE:
        workflows += ["uploaded archive: batch files, LaTeX project, or code/document workflow after extraction"]
    else:
        workflows.append("批量文件询问 if a reader supports this suffix")
        warnings.append("Unsupported suffix may need conversion first.")
    return {"path": str(path), "exists": True, "kind": "file", "suffix": suffix, "suggested_workflows": workflows, "warnings": warnings}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="+", help="server-local document, folder, or archive paths")
    args = parser.parse_args()
    print(json.dumps([classify(Path(p).expanduser()) for p in args.paths], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
